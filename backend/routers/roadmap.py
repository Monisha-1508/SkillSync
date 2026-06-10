from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from backend.agents import coach, reflow as reflow_agent, roadmap_architect, weekly_test
from backend.models.database import ProgressEvent, WeeklyTestAttempt
from backend.models.schemas import ProgressEventIn, ReflowOut, ReplanDecision, ReplanProposeIn, RoadmapVariantSelect
from backend.routers import deps
from backend.routers.deps import SessionDep
from backend.utils import tracing

router = APIRouter(tags=["roadmap"])


@router.post("/api/roadmap/{profile_id}/select")
async def select_roadmap_variant(profile_id: str, payload: RoadmapVariantSelect, session: SessionDep) -> dict[str, Any]:
    await deps.get_profile_or_404(session, profile_id)
    roadmap = await deps.get_latest_roadmap_or_404(session, profile_id)
    if payload.variant not in roadmap.variants:
        raise HTTPException(status_code=409, detail=f"This learner's roadmap has no '{payload.variant}' variant to switch to.")

    projection = roadmap_architect.select_variant(roadmap.variants, payload.variant)
    roadmap.selected_variant = projection["selected_variant"]
    roadmap.active_milestones = projection["active_milestones"]
    roadmap.feasibility_score = projection["feasibility_score"]
    roadmap.feasibility_explanation = projection["feasibility_explanation"]
    await session.commit()
    return {
        "selected_variant": roadmap.selected_variant,
        "active_milestones": roadmap.active_milestones,
        "feasibility_score": roadmap.feasibility_score,
        "feasibility_explanation": roadmap.feasibility_explanation,
    }


@router.post("/api/roadmap/{profile_id}/progress", status_code=201)
async def log_progress(profile_id: str, payload: ProgressEventIn, session: SessionDep) -> dict[str, Any]:
    await deps.get_profile_or_404(session, profile_id)
    if payload.event_type in ("completed", "partial"):
        cleared = (await session.execute(
            select(WeeklyTestAttempt.id).where(
                WeeklyTestAttempt.profile_id == profile_id,
                WeeklyTestAttempt.week == payload.week,
                WeeklyTestAttempt.status == "submitted",
                WeeklyTestAttempt.score >= weekly_test.LOG_FLOOR,
            ).limit(1)
        )).scalar_one_or_none()
        if cleared is None:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Logging week {payload.week} as done needs a checkpoint sitting that scored "
                    f"{round(weekly_test.LOG_FLOOR * 100)} percent or higher first - take it from the "
                    "weekly checkpoint tab, then come back to log the week."
                ),
            )
    event = ProgressEvent(profile_id=profile_id, **payload.model_dump())
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return {
        "id": event.id,
        "week": event.week,
        "skill_id": event.skill_id,
        "event_type": event.event_type,
        "quiz_score": event.quiz_score,
        "logged_at": event.created_at.isoformat(),
    }


@router.post("/api/roadmap/{profile_id}/replan/propose")
async def propose_roadmap_replan(profile_id: str, payload: ReplanProposeIn, session: SessionDep) -> dict[str, Any]:
    profile = await deps.get_profile_or_404(session, profile_id)
    roadmap = await deps.get_latest_roadmap_or_404(session, profile_id)
    learner_profile = deps.profile_to_dict(profile)

    result = coach.propose_replan(learner_profile, {"active_milestones": roadmap.active_milestones}, payload.missed_week)
    proposal = result["pending_replan"]

    session.add(deps.audit_row_from_trace(profile_id, result["trace"]))
    if proposal["status"] == "pending":
        roadmap.pending_replan = proposal
    await session.commit()
    return proposal


@router.post("/api/roadmap/{profile_id}/replan/decide")
async def decide_roadmap_replan(profile_id: str, payload: ReplanDecision, session: SessionDep) -> dict[str, Any]:
    profile = await deps.get_profile_or_404(session, profile_id)
    roadmap = await deps.get_latest_roadmap_or_404(session, profile_id)
    pending = roadmap.pending_replan
    if pending is None:
        raise HTTPException(status_code=409, detail="There is no replan proposal waiting on a decision for this learner.")

    decided_at = tracing.iso_now()
    if payload.decision == "accept":
        learner_profile = deps.profile_to_dict(profile)
        applied = coach.apply_replan(learner_profile, {"active_milestones": roadmap.active_milestones}, pending)
        roadmap.active_milestones = applied["active_milestones"]
        roadmap.feasibility_score = applied["feasibility_score"]
        roadmap.feasibility_explanation = applied["feasibility_explanation"]
        roadmap.version += 1
        resolved = {**applied["pending_replan"], "decided_at": decided_at}
    else:
        resolved = {**pending, "status": "rejected", "decided_at": decided_at}

    roadmap.replan_log = [*roadmap.replan_log, resolved]
    roadmap.pending_replan = None
    await session.commit()
    return {
        "decision": payload.decision,
        "active_milestones": roadmap.active_milestones,
        "feasibility_score": roadmap.feasibility_score,
        "feasibility_explanation": roadmap.feasibility_explanation,
        "version": roadmap.version,
        "replan_log": roadmap.replan_log,
    }


@router.post("/api/roadmap/{profile_id}/reflow/{week}", response_model=ReflowOut)
async def reflow_missed_week(profile_id: str, week: int, session: SessionDep) -> dict[str, Any]:
    profile = await deps.get_profile_or_404(session, profile_id)
    roadmap_row = await deps.get_latest_roadmap_or_404(session, profile_id)

    completed_check = (await session.execute(
        select(ProgressEvent).where(
            ProgressEvent.profile_id == profile_id,
            ProgressEvent.week == week,
            ProgressEvent.event_type == "completed",
        ).limit(1)
    )).scalar_one_or_none()
    if completed_check is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Week {week} has already been logged as completed and cannot be reflowed.",
        )

    try:
        result = reflow_agent.apply_reflow(
            active_milestones=roadmap_row.active_milestones,
            missed_week_number=week,
            deadline_weeks=profile.deadline_weeks,
            weekly_hours=profile.weekly_hours,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    log_entry = reflow_agent.reflow_log_entry(week, result)
    roadmap_row.active_milestones = result["active_milestones"]
    roadmap_row.version += 1
    roadmap_row.replan_log = [*roadmap_row.replan_log, log_entry]
    await session.commit()

    return {
        **result,
        "version": roadmap_row.version,
    }
