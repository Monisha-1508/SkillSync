from __future__ import annotations

from backend.agents import roadmap_architect
from backend.utils import fsrs_engine, llm, skill_graph, tracing

_ENGAGED_TYPES = ("completed", "quiz")


def build_deck(skill_ids: list[str], *, limit: int = 24) -> dict:
    with tracing.traced_step(
        "coach_adapter", "build_revision_deck",
        input_summary=f"{len(skill_ids)} candidate skills, limit {limit}",
    ) as record:
        cards = fsrs_engine.build_deck(skill_ids, limit=limit)
        record["output_summary"] = f"{len(cards)} cards drawn from {len(skill_ids)} skills, all FSRS-fresh"
        record["confidence"] = 0.97 if cards else 0.4

    return {"fsrs_deck": cards, "trace": dict(record)}


def _mood(completion_rate: float, missed: int, recent_quiz: float | None) -> str:
    if missed == 0 and completion_rate >= 0.85 and (recent_quiz is None or recent_quiz >= 0.7):
        return "crushing_it"
    if missed > 0 or completion_rate < 0.5:
        return "slipping"
    return "on_track"


def assess_engagement(name: str, events: list[dict], week_rows: list[dict] | None = None) -> dict:
    with tracing.traced_step(
        "coach_adapter", "assess_engagement", input_summary=f"{len(events)} logged events",
    ) as record:
        if not events:
            payload = {
                "mood": "on_track", "completion_rate": 0.0, "streak_weeks": 0,
                "streak_days": 0, "recent_quiz_score": None, "missed_weeks": 0,
            }
            nudge = llm.get_llm_provider().narrate("nudge", {**payload, "name": name, "recent_quiz_score": 0.0})
            record["output_summary"] = "no progress logged yet - opening nudge only"
            record["confidence"] = 0.5
            return {"engagement_signals": payload, "nudge": nudge.text, "trace": dict(record)}

        completed = sum(1 for e in events if e["event_type"] in _ENGAGED_TYPES)
        partial = sum(1 for e in events if e["event_type"] == "partial")
        missed = sum(1 for e in events if e["event_type"] == "missed")
        completion_rate = round((completed + 0.5 * partial) / len(events), 3)

        quiz_scores = [e["quiz_score"] for e in events if e.get("quiz_score") is not None]
        recent_quiz = quiz_scores[-1] if quiz_scores else None

        touched_weeks = [w for w in (week_rows or []) if w.get("status") in ("completed", "missed")]
        streak_weeks = 0
        for week in reversed(touched_weeks):
            if week.get("status") != "completed":
                break
            streak_weeks += 1

        mood = _mood(completion_rate, missed, recent_quiz)
        nudge_ctx = {
            "name": name, "mood": mood, "streak_days": streak_weeks * 7,
            "completion_rate": completion_rate, "recent_quiz_score": recent_quiz or 0.0,
        }
        nudge = llm.get_llm_provider().narrate("nudge", nudge_ctx)

        payload = {
            "mood": mood,
            "completion_rate": completion_rate,
            "streak_weeks": streak_weeks,
            "streak_days": streak_weeks * 7,
            "recent_quiz_score": recent_quiz,
            "missed_weeks": missed,
        }
        record["output_summary"] = (
            f"mood={mood}, completion={completion_rate:.0%}, streak={streak_weeks}w, missed={missed}"
        )
        record["confidence"] = 0.9 if len(events) >= 3 else 0.6

    return {"engagement_signals": payload, "nudge": nudge.text, "trace": dict(record)}


def _pending_skill_ids(active_milestones: list[dict], from_week: int) -> list[str]:
    pending: list[str] = []
    for milestone in active_milestones:
        if milestone["week"] >= from_week and not milestone.get("is_blackout"):
            pending.extend(milestone["skill_ids"])
    return pending


def propose_replan(learner_profile: dict, roadmap: dict, missed_week: int) -> dict:
    role = learner_profile["target_role"]
    weekly_hours = learner_profile["weekly_hours"]
    deadline_weeks = learner_profile["deadline_weeks"]
    exam_blackouts = learner_profile.get("exam_blackouts", [])
    active_milestones = roadmap["active_milestones"]

    with tracing.traced_step(
        "coach_adapter", "propose_replan", input_summary=f"week {missed_week} logged as missed",
    ) as record:
        pending = _pending_skill_ids(active_milestones, missed_week)

        if not pending:
            record["output_summary"] = f"week {missed_week} has nothing left to reorder - no proposal raised"
            record["confidence"] = 0.4
            return {
                "pending_replan": {
                    "status": "not_applicable",
                    "missed_week": missed_week,
                    "rationale": (
                        "There is nothing scheduled from that week onward to rearrange - "
                        "the plan is either already finished there or that week was already a rest week."
                    ),
                },
                "trace": dict(record),
            }

        critical = set(skill_graph.critical_path(role))
        protected = [s for s in pending if s in critical]
        deferred = [s for s in pending if s not in critical]
        reordered = skill_graph.priority_topo_rank(pending, critical)

        preview_milestones, overflow = roadmap_architect.replan_schedule(
            active_milestones, reordered, weekly_hours, deadline_weeks, exam_blackouts, from_week=missed_week,
        )
        hours_recovered = round(sum(skill_graph.node(s)["estimated_hours"] for s in deferred), 1)
        weeks_remaining = max(0, deadline_weeks - missed_week + 1)

        narrated = llm.get_llm_provider().narrate("replan_rationale", {
            "trigger_reason": f"week {missed_week} was logged as missed",
            "protected_skills": [skill_graph.node(s)["name"] for s in protected],
            "deferred_skills": [skill_graph.node(s)["name"] for s in deferred],
            "hours_recovered": hours_recovered,
            "weeks_remaining": weeks_remaining,
        })

        record["output_summary"] = (
            f"{len(protected)} protected on critical path, {len(deferred)} deferred "
            f"({hours_recovered:.0f}h eased), {len(overflow)} pushed past the deadline"
        )
        record["confidence"] = round(len(protected) / max(1, len(pending)), 3)

    return {
        "pending_replan": {
            "status": "pending",
            "missed_week": missed_week,
            "trigger_reason": f"Week {missed_week} was logged as missed",
            "protected_skill_ids": protected,
            "deferred_skill_ids": deferred,
            "hours_recovered": hours_recovered,
            "weeks_remaining": weeks_remaining,
            "overflow_skill_ids": overflow,
            "preview_milestones": preview_milestones,
            "rationale": narrated.text,
        },
        "trace": dict(record),
    }


def apply_replan(learner_profile: dict, roadmap: dict, pending_replan: dict) -> dict:
    from backend.utils import feasibility

    weekly_hours = learner_profile["weekly_hours"]
    missed_week = pending_replan["missed_week"]
    weeks_remaining = pending_replan["weeks_remaining"]
    new_milestones = pending_replan["preview_milestones"]

    remaining_hours = round(
        sum(
            skill_graph.node(skill_id)["estimated_hours"]
            for milestone in new_milestones
            for skill_id in milestone["skill_ids"]
        ),
        1,
    )
    remaining_blackouts = [
        window for window in learner_profile.get("exam_blackouts", [])
        if window.get("end_week", 0) >= missed_week
    ]
    feas = feasibility.compute(remaining_hours, weekly_hours, weeks_remaining, remaining_blackouts)

    return {
        "active_milestones": new_milestones,
        "feasibility_score": feas["score"],
        "feasibility_explanation": feas["explanation"],
        "pending_replan": {**pending_replan, "status": "accepted"},
    }
