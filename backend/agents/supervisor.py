from __future__ import annotations

from typing import Any, AsyncIterator

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import coach, profiling, resource_curator, roadmap_architect, validator
from backend.models.state import SkillSyncState


def _logged(state: SkillSyncState, trace: dict[str, Any]) -> dict[str, Any]:
    return {
        "trace_events": [trace],
        "audit_log": [{
            "profile_id": state["profile_id"],
            "agent_name": trace["agent"],
            "action": trace["action"],
            "input_summary": trace["input_summary"],
            "output_summary": trace["output_summary"],
            "confidence_score": trace["confidence"],
            "duration_ms": trace["duration_ms"],
            "trace_id": trace["trace_id"],
            "timestamp": trace["timestamp"],
        }],
    }


def _scheduled_skill_ids(state: SkillSyncState) -> list[str]:
    return [
        skill_id
        for milestone in state["active_milestones"]
        if not milestone["is_blackout"]
        for skill_id in milestone["skill_ids"]
    ]


async def _profile_gaps(state: SkillSyncState) -> dict[str, Any]:
    result = await profiling.run(state["learner_profile"])
    return {
        **_logged(state, result["trace"]),
        "gap_map": result["gap_map"],
        "gap_summary": result["summary"],
        "gap_confidence": result["confidence"],
        "radar_axes": result["radar_axes"],
    }


async def _build_roadmap(state: SkillSyncState) -> dict[str, Any]:
    result = await roadmap_architect.run(state["learner_profile"], state["gap_map"])
    return {
        **_logged(state, result["trace"]),
        "roadmap_variants": result["roadmap_variants"],
        "selected_variant": result["selected_variant"],
        "active_milestones": result["active_milestones"],
        "feasibility_score": result["feasibility_score"],
        "feasibility_explanation": result["feasibility_explanation"],
    }


async def _curate_resources(state: SkillSyncState, config: dict[str, Any]) -> dict[str, Any]:
    session: AsyncSession = config["configurable"]["session"]
    budget_mode = (state.get("learner_profile") or {}).get("budget_mode") or "free"
    result = await resource_curator.run(
        session, _scheduled_skill_ids(state),
        budget_mode=budget_mode,
    )
    return {**_logged(state, result["trace"]), "resource_picks": result["resource_picks"]}


async def _draft_revision_deck(state: SkillSyncState) -> dict[str, Any]:
    result = coach.build_deck(_scheduled_skill_ids(state))
    return {**_logged(state, result["trace"]), "fsrs_deck": result["fsrs_deck"]}


async def _validate_plan(state: SkillSyncState) -> dict[str, Any]:
    result = await validator.run(
        learner_profile=state["learner_profile"],
        gap_map=state["gap_map"],
        gap_summary=state["gap_summary"],
        roadmap_variants=state["roadmap_variants"],
        active_milestones=state["active_milestones"],
        resource_picks=state["resource_picks"],
    )
    return {**_logged(state, result["trace"]), "validation_report": result["validation_report"]}


def _build_graph():
    graph = StateGraph(SkillSyncState)
    graph.add_node("profile_gaps", _profile_gaps)
    graph.add_node("build_roadmap", _build_roadmap)
    graph.add_node("curate_resources", _curate_resources)
    graph.add_node("draft_revision_deck", _draft_revision_deck)
    graph.add_node("validate_plan", _validate_plan)

    graph.set_entry_point("profile_gaps")
    graph.add_edge("profile_gaps", "build_roadmap")
    graph.add_edge("build_roadmap", "curate_resources")
    graph.add_edge("curate_resources", "draft_revision_deck")
    graph.add_edge("draft_revision_deck", "validate_plan")
    graph.add_edge("validate_plan", END)
    return graph.compile()


_COMPILED = _build_graph()


def _initial_state(profile_id: str, learner_profile: dict[str, Any], trigger: dict[str, Any]) -> SkillSyncState:
    return {
        "profile_id": profile_id,
        "learner_profile": learner_profile,
        "trigger": trigger,
        "audit_log": [],
        "trace_events": [],
    }


async def run_pipeline(
    session: AsyncSession,
    *,
    profile_id: str,
    learner_profile: dict[str, Any],
    trigger: dict[str, Any],
) -> SkillSyncState:
    initial = _initial_state(profile_id, learner_profile, trigger)
    return await _COMPILED.ainvoke(initial, config={"configurable": {"session": session}})


async def stream_pipeline(
    session: AsyncSession,
    *,
    profile_id: str,
    learner_profile: dict[str, Any],
    trigger: dict[str, Any],
) -> AsyncIterator[dict[str, Any]]:
    initial = _initial_state(profile_id, learner_profile, trigger)
    seen = 0
    final_state = initial
    async for snapshot in _COMPILED.astream(initial, config={"configurable": {"session": session}}, stream_mode="values"):
        final_state = snapshot
        events = snapshot.get("trace_events", [])
        for event in events[seen:]:
            yield {"type": "step", "event": event}
        seen = len(events)
    yield {"type": "done", "state": final_state}
