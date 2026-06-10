from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from backend.agents import coach, project_advisor, resource_curator, validator, weekly_test
from backend.models.database import (
    AuditLog, FsrsCard, InterviewSession, LearnerProfile, ProgressEvent, Roadmap, WeeklyTestAttempt,
)
from backend.models.schemas import ProfileOut
from backend.routers import deps
from backend.routers.deps import SessionDep
from backend.utils import gamification, responsible_ai, skill_graph

router = APIRouter(tags=["dashboard"])

_RECENT_ACTIVITY_LIMIT = 12
_NEXT_DUE_PREVIEW = 3


def _scheduled_skill_ids(active_milestones: list[dict[str, Any]], unlocked_weeks: set[int]) -> list[str]:
    return [
        skill_id
        for milestone in active_milestones
        if not milestone["is_blackout"] and milestone["week"] in unlocked_weeks
        for skill_id in milestone["skill_ids"]
    ]


def _resource_lock_view(active_milestones: list[dict[str, Any]], unlocked_weeks: set[int]) -> dict[str, Any]:
    locked = [
        {"week": m["week"], "skill_ids": list(m.get("skill_ids", [])), "hours": m.get("hours", 0)}
        for m in active_milestones
        if not m.get("is_blackout") and m["week"] not in unlocked_weeks
    ]
    return {"unlocked_weeks": sorted(unlocked_weeks), "locked_weeks": locked}


def _card_brief(card: FsrsCard) -> dict[str, Any]:
    return {
        "id": card.id,
        "skill_id": card.skill_id,
        "skill_name": skill_graph.node(card.skill_id)["name"],
        "front": card.front,
        "due_date": card.due_date.isoformat(),
    }


def _activity_brief(entry: AuditLog) -> dict[str, Any]:
    return {
        "agent_name": entry.agent_name,
        "action": entry.action,
        "output_summary": entry.output_summary,
        "confidence_score": entry.confidence_score,
        "timestamp": entry.timestamp.isoformat(),
    }


@router.get("/api/dashboard/{profile_id}")
async def get_dashboard(profile_id: str, session: SessionDep) -> dict[str, Any]:
    profile = await deps.get_profile_or_404(session, profile_id)
    gap_map_row = await deps.get_latest_gap_map(session, profile_id)
    roadmap_row = await deps.get_latest_roadmap(session, profile_id)
    if gap_map_row is None or roadmap_row is None:
        raise HTTPException(
            status_code=409,
            detail="This learner's plan has not finished building yet - open the onboarding stream first.",
        )

    learner_profile = deps.profile_to_dict(profile)

    progress_rows = (await session.execute(
        select(ProgressEvent).where(ProgressEvent.profile_id == profile_id).order_by(ProgressEvent.created_at)
    )).scalars().all()
    progress = deps.progress_tracker(roadmap_row, progress_rows)
    unlocked_weeks = deps.unlocked_week_numbers(progress)

    scheduled_ids = _scheduled_skill_ids(roadmap_row.active_milestones, unlocked_weeks)
    resource_lock = _resource_lock_view(roadmap_row.active_milestones, unlocked_weeks)

    curated = await resource_curator.run(
        session, scheduled_ids,
        budget_mode=profile.budget_mode or "free",
    )
    resource_picks = curated["resource_picks"]

    validated = await validator.run(
        learner_profile=learner_profile,
        gap_map=gap_map_row.skill_gaps,
        gap_summary=gap_map_row.summary,
        roadmap_variants=roadmap_row.variants,
        active_milestones=roadmap_row.active_milestones,
        resource_picks=resource_picks,
    )
    report = validated["validation_report"]
    overrides = report["narration_overrides"]

    cards = (await session.execute(
        select(FsrsCard).where(FsrsCard.profile_id == profile_id)
    )).scalars().all()
    now = datetime.utcnow()
    due_cards = sorted((c for c in cards if c.due_date <= now), key=lambda c: c.due_date)

    engagement = coach.assess_engagement(
        profile.name,
        [{"event_type": e.event_type, "quiz_score": e.quiz_score} for e in progress_rows],
        week_rows=progress["weeks"],
    )

    recent_activity = (await session.execute(
        select(AuditLog).where(AuditLog.profile_id == profile_id)
        .order_by(AuditLog.timestamp.desc()).limit(_RECENT_ACTIVITY_LIMIT)
    )).scalars().all()

    gap_summary_text = overrides.get("gap_summary", gap_map_row.summary)
    variants_out = {
        key: {**variant, "rationale": overrides.get(f"{key}_plan_rationale", variant["rationale"])}
        for key, variant in roadmap_row.variants.items()
    }
    resource_picks_out = {
        skill_id: [
            {**entry, "why": overrides.get(f"resource_why[{skill_id}#{index}]", entry["why"])}
            for index, entry in enumerate(entries)
        ]
        for skill_id, entries in resource_picks.items()
    }

    test_attempts = (await session.execute(
        select(WeeklyTestAttempt).where(
            WeeklyTestAttempt.profile_id == profile_id, WeeklyTestAttempt.status == "submitted",
        )
    )).scalars().all()
    interview_sessions = (await session.execute(
        select(InterviewSession).where(InterviewSession.profile_id == profile_id)
    )).scalars().all()
    points_summary = _gamification_summary(progress, test_attempts, interview_sessions)

    log_unlocked_weeks = {
        attempt.week for attempt in test_attempts
        if attempt.score is not None and attempt.score >= weekly_test.LOG_FLOOR
    }
    progress = {
        **progress,
        "weeks": [
            {**week_row, "log_unlocked": week_row["week"] in log_unlocked_weeks}
            for week_row in progress["weeks"]
        ],
    }

    project_suggestions = None
    if progress["total_weeks"] > 0 and progress["completed_weeks"] >= progress["total_weeks"]:
        advised = project_advisor.run(target_role=profile.target_role)
        session.add(deps.audit_row_from_trace(profile_id, advised["trace"]))
        await session.commit()
        project_suggestions = {
            "projects": advised["project_picks"],
            "matched_tracks": advised["matched_tracks"],
        }

    return {
        "profile": ProfileOut.model_validate(profile).model_dump(),
        "gap_map": {
            **gap_map_row.skill_gaps,
            "id": gap_map_row.id,
            "summary": gap_summary_text,
            "radar_axes": gap_map_row.radar_axes,
            "disclosure": responsible_ai.disclosure_for(gap_map_row.confidence),
            "generated_at": gap_map_row.generated_at.isoformat(),
        },
        "roadmap": {
            "id": roadmap_row.id,
            "selected_variant": roadmap_row.selected_variant,
            "variants": variants_out,
            "active_milestones": roadmap_row.active_milestones,
            "feasibility_score": roadmap_row.feasibility_score,
            "feasibility_explanation": roadmap_row.feasibility_explanation,
            "version": roadmap_row.version,
            "pending_replan": roadmap_row.pending_replan,
            "replan_log": roadmap_row.replan_log,
        },
        "resource_picks": resource_picks_out,
        "resource_lock": resource_lock,
        "resource_curation": {
            "average_trust": curated["average_trust"],
            "trust_floor": curated["trust_floor"],
            "below_floor_excluded": curated["below_floor_excluded"],
            "budget_mode": curated["budget_mode"],
        },
        "revision": {
            "total_cards": len(cards),
            "due_now": len(due_cards),
            "next_due": [_card_brief(card) for card in due_cards[:_NEXT_DUE_PREVIEW]],
        },
        "validation_report": {
            "overall_status": report["overall_status"],
            "checks": report["checks"],
            "checked_at": report["checked_at"],
        },
        "engagement": {
            "signals": engagement["engagement_signals"],
            "nudge": engagement["nudge"],
        },
        "recent_activity": [_activity_brief(entry) for entry in recent_activity],
        "progress": progress,
        "alerts": _deadline_alerts(profile, progress),
        "gamification": points_summary,
        "project_suggestions": project_suggestions,
    }


def _gamification_summary(
    progress: dict[str, Any], test_attempts: list[WeeklyTestAttempt], interview_sessions: list[InterviewSession],
) -> dict[str, Any]:
    checkpoint_facts = [
        gamification.CheckpointFact(week=row.week, band=row.band or "failed", attempt_number=row.attempt_number)
        for row in test_attempts
    ]
    perfect_checkpoints = sum(
        1 for row in test_attempts
        if row.score is not None and row.questions and row.score >= 0.999
    )
    interview_rounds = sum(1 for row in interview_sessions if row.feedback)
    strong_interview_answers = sum(
        1 for row in interview_sessions for entry in row.answers
        if (entry.get("overall_score") or 0) >= 0.8
    )
    return gamification.summarize(
        completed_weeks=progress["completed_weeks"],
        total_weeks=progress["total_weeks"],
        checkpoint_facts=checkpoint_facts,
        perfect_checkpoints=perfect_checkpoints,
        interview_rounds=interview_rounds,
        strong_interview_answers=strong_interview_answers,
    )


def _deadline_alerts(profile: LearnerProfile, progress: dict[str, Any]) -> list[dict[str, Any]]:
    total_days = max(profile.deadline_weeks, 1) * 7
    elapsed_days = (datetime.utcnow() - profile.created_at).days
    days_remaining = total_days - elapsed_days
    weeks_remaining = days_remaining / 7

    alerts: list[dict[str, Any]] = []

    if days_remaining < 0:
        alerts.append({
            "level": "critical",
            "kind": "deadline",
            "title": "Your target date has passed",
            "message": (
                f"The {profile.deadline_weeks}-week runway you set at intake ended "
                f"{abs(days_remaining)} day(s) ago. Worth deciding deliberately whether "
                "to set a fresh target date or keep working the plan as is - either is "
                "a fine choice, but one made on purpose beats one made by drifting."
            ),
        })
    elif weeks_remaining <= 1:
        alerts.append({
            "level": "critical",
            "kind": "deadline",
            "title": "About a week left on your runway",
            "message": (
                f"Roughly {days_remaining} day(s) remain before the target date you set "
                f"({profile.deadline_weeks} weeks from when this plan was built). If the "
                "remaining milestones feel out of reach, a re-plan from the roadmap tab "
                "is the honest next step - not pushing through and logging it as done anyway."
            ),
        })
    elif weeks_remaining <= 2:
        alerts.append({
            "level": "warn",
            "kind": "deadline",
            "title": "Two weeks left until your target date",
            "message": (
                f"About {days_remaining} days remain on the {profile.deadline_weeks}-week "
                "runway you set. A good moment to check the upcoming milestones against "
                "the hours you actually have left in the week."
            ),
        })

    if total_days > 0 and progress["total_weeks"] > 0:
        expected_percent = min(100, round((max(elapsed_days, 0) / total_days) * progress["total_weeks"]) / progress["total_weeks"] * 100)
        actual_percent = progress["percent_complete"]
        gap = expected_percent - actual_percent
        if gap >= 25:
            alerts.append({
                "level": "warn",
                "kind": "pace",
                "title": "Logged progress is trailing the runway",
                "message": (
                    f"By this point in the {profile.deadline_weeks}-week plan, roughly "
                    f"{round(expected_percent)}% of the scheduled weeks would typically be "
                    f"logged as done - this account shows {actual_percent}%. That gap is "
                    "exactly what the Coach reads to propose a re-plan, on the roadmap tab, "
                    "whenever it would help."
                ),
            })

    return alerts
