from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, TypeVar

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from backend.models.database import AuditLog, GapMap, LearnerProfile, ProgressEvent, Roadmap, get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

_Row = TypeVar("_Row", bound=DeclarativeBase)


async def get_or_404(session: AsyncSession, model: type[_Row], row_id: str, *, label: str) -> _Row:
    row = await session.get(model, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No {label} found for id '{row_id}'.")
    return row


async def get_profile_or_404(session: AsyncSession, profile_id: str) -> LearnerProfile:
    return await get_or_404(session, LearnerProfile, profile_id, label="learner profile")


async def _latest_for_profile(session: AsyncSession, model: type[_Row], profile_id: str, order_column) -> _Row | None:
    result = await session.execute(
        select(model).where(model.profile_id == profile_id).order_by(order_column.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def get_latest_gap_map(session: AsyncSession, profile_id: str) -> GapMap | None:
    return await _latest_for_profile(session, GapMap, profile_id, GapMap.generated_at)


async def get_latest_roadmap(session: AsyncSession, profile_id: str) -> Roadmap | None:
    return await _latest_for_profile(session, Roadmap, profile_id, Roadmap.created_at)


async def get_latest_roadmap_or_404(session: AsyncSession, profile_id: str) -> Roadmap:
    roadmap = await get_latest_roadmap(session, profile_id)
    if roadmap is None:
        raise HTTPException(
            status_code=404,
            detail="This learner does not have a roadmap yet - onboarding has not finished building one.",
        )
    return roadmap


def profile_to_dict(profile: LearnerProfile) -> dict[str, Any]:
    return {
        "name": profile.name,
        "target_role": profile.target_role,
        "target_companies": profile.target_companies,
        "current_skills": profile.current_skills,
        "weekly_hours": profile.weekly_hours,
        "deadline_weeks": profile.deadline_weeks,
        "budget_mode": profile.budget_mode,
        "placement_mode": profile.placement_mode,
        "background": profile.background,
        "exam_blackouts": profile.exam_blackouts,
    }


def audit_row_from_trace(profile_id: str, trace: dict[str, Any]) -> AuditLog:
    return AuditLog(
        profile_id=profile_id,
        agent_name=trace["agent"],
        action=trace["action"],
        input_summary=trace["input_summary"],
        output_summary=trace["output_summary"],
        confidence_score=trace["confidence"],
        duration_ms=trace["duration_ms"],
        trace_id=trace["trace_id"],
        timestamp=datetime.fromisoformat(trace["timestamp"]),
    )


def skill_brief(skill_id: str) -> dict[str, Any]:
    from backend.utils import skill_graph

    return {"id": skill_id, "name": skill_graph.node(skill_id)["name"]}


def progress_brief(entry: ProgressEvent) -> dict[str, Any]:
    return {
        "id": entry.id,
        "week": entry.week,
        "skill_id": entry.skill_id,
        "event_type": entry.event_type,
        "quiz_score": entry.quiz_score,
        "notes": entry.notes,
        "logged_at": entry.created_at.isoformat(),
    }


def progress_tracker(roadmap_row: Roadmap, progress_rows: list[ProgressEvent]) -> dict[str, Any]:
    weeks = [m for m in roadmap_row.active_milestones if not m.get("is_blackout")]
    by_week: dict[int, list[ProgressEvent]] = {}
    for entry in progress_rows:
        by_week.setdefault(entry.week, []).append(entry)

    rows = []
    completed_weeks = 0
    for milestone in weeks:
        week = milestone["week"]
        entries = by_week.get(week, [])
        scheduled = set(milestone.get("skill_ids", []))
        done_skills = {e.skill_id for e in entries if e.event_type == "completed" and e.skill_id}
        whole_week_logged = any(e.event_type == "completed" and not e.skill_id for e in entries)
        is_done = whole_week_logged or (bool(scheduled) and scheduled.issubset(done_skills))
        has_missed = any(e.event_type == "missed" for e in entries)
        has_partial = any(e.event_type == "partial" for e in entries)

        if is_done:
            status = "completed"
            completed_weeks += 1
        elif has_missed:
            status = "missed"
        elif has_partial:
            status = "partial"
        elif entries:
            status = "in_progress"
        else:
            status = "not_started"

        display_hours = (
            milestone["original_hours"]
            if milestone.get("is_missed") and milestone.get("original_hours")
            else milestone.get("hours", 0)
        )
        rows.append({
            "week": week,
            "status": status,
            "skill_ids": milestone.get("skill_ids", []),
            "hours": display_hours,
            "logged_count": len(entries),
            # Reflow metadata - both flags come from the milestone, not from the
            # progress event, so they survive even when the progress event list
            # is empty (a freshly-reflowed week has no new events yet).
            "is_missed": bool(milestone.get("is_missed")),
            "is_merged": bool(milestone.get("is_merged")),
            "merged_from_weeks": milestone.get("merged_from_weeks") or [],
        })

    total = len(weeks)
    percent = round((completed_weeks / total) * 100) if total else 0
    return {
        "total_weeks": total,
        "completed_weeks": completed_weeks,
        "percent_complete": min(100, percent),
        "weeks": rows,
        "recent_events": [progress_brief(e) for e in progress_rows[-12:]],
    }


def unlocked_week_numbers(progress: dict[str, Any]) -> set[int]:
    unlocked: set[int] = set()
    chain_open = True
    for week_row in progress["weeks"]:
        if chain_open:
            unlocked.add(week_row["week"])
        if week_row.get("is_missed"):
            chain_open = True
        else:
            chain_open = week_row["status"] == "completed"
    return unlocked
