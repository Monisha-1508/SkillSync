from __future__ import annotations

import json
import traceback
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from backend.agents import supervisor
from backend.models.database import LearnerProfile, ProgressEvent, Roadmap, SessionLocal, User
from backend.models.schemas import MyPlanOut, OnboardingRequest, ProfileOut
from backend.routers import deps
from backend.routers.deps import SessionDep
from backend.utils import auth, persistence, seed

router = APIRouter(tags=["profiles"])


def _persona_card(key: str, persona: dict[str, Any]) -> dict[str, Any]:
    onboarding = persona["onboarding"]
    return {
        "persona_key": key,
        "name": persona["name"],
        "tagline": persona["tagline"],
        "avatar_color": persona["avatar_color"],
        "story": persona["story"],
        "target_role": onboarding["target_role"],
        "placement_mode": onboarding["placement_mode"],
        "weekly_hours": onboarding["weekly_hours"],
        "deadline_weeks": onboarding["deadline_weeks"],
    }


@router.get("/api/personas")
async def list_personas() -> dict[str, Any]:
    personas = seed.load_personas()
    return {"personas": [_persona_card(key, persona) for key, persona in personas.items()]}


async def _create_profile_row(
    session: SessionDep, payload: OnboardingRequest, persona_key: str | None, owner_id: str | None = None,
) -> LearnerProfile:
    profile = LearnerProfile(
        owner_id=owner_id,
        name=payload.name,
        persona_key=persona_key,
        target_role=payload.target_role,
        target_companies=payload.target_companies,
        current_skills=payload.current_skills,
        weekly_hours=payload.weekly_hours,
        deadline_weeks=payload.deadline_weeks,
        budget_mode=payload.budget_mode,
        placement_mode=payload.placement_mode,
        background=payload.background,
        exam_blackouts=payload.exam_blackouts,
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


@router.post("/api/profiles", response_model=ProfileOut, status_code=201)
async def create_profile(payload: OnboardingRequest, session: SessionDep, current_user: User = Depends(auth.get_current_user)):
    return await _create_profile_row(session, payload, persona_key=None, owner_id=current_user.id)


@router.post("/api/profiles/from-persona/{persona_key}", response_model=ProfileOut, status_code=201)
async def create_profile_from_persona(persona_key: str, session: SessionDep):
    persona = seed.load_personas().get(persona_key)
    if persona is None:
        raise HTTPException(status_code=404, detail=f"No demo persona named '{persona_key}'.")
    payload = OnboardingRequest(**persona["onboarding"])
    return await _create_profile_row(session, payload, persona_key=persona_key)


async def _plan_summary(session: SessionDep, profile: LearnerProfile) -> MyPlanOut:
    roadmap = await deps.get_latest_roadmap(session, profile.id)
    base = {
        "id": profile.id,
        "name": profile.name,
        "persona_key": profile.persona_key,
        "target_role": profile.target_role,
        "placement_mode": profile.placement_mode,
        "weekly_hours": profile.weekly_hours,
        "deadline_weeks": profile.deadline_weeks,
        "created_at": profile.created_at.isoformat(),
        "has_roadmap": roadmap is not None,
    }
    if roadmap is None:
        return MyPlanOut(**base, total_weeks=profile.deadline_weeks)

    total_weeks = len(roadmap.active_milestones) or profile.deadline_weeks
    completed_rows = (await session.execute(
        select(ProgressEvent.week)
        .where(ProgressEvent.profile_id == profile.id)
        .where(ProgressEvent.roadmap_id == roadmap.id)
        .where(ProgressEvent.event_type == "completed")
        .distinct()
    )).scalars().all()
    completed_weeks = len(completed_rows)
    percent = round((completed_weeks / total_weeks) * 100) if total_weeks else 0

    return MyPlanOut(
        **base,
        selected_variant=roadmap.selected_variant,
        feasibility_score=roadmap.feasibility_score,
        pending_replan=bool(roadmap.pending_replan),
        total_weeks=total_weeks,
        completed_weeks=completed_weeks,
        progress_percent=min(100, percent),
    )


@router.get("/api/profiles/mine", response_model=list[MyPlanOut])
async def list_my_profiles(session: SessionDep, current_user: User = Depends(auth.get_current_user)):
    result = await session.execute(
        select(LearnerProfile).where(LearnerProfile.owner_id == current_user.id).order_by(LearnerProfile.created_at.desc())
    )
    profiles = result.scalars().all()
    return [await _plan_summary(session, profile) for profile in profiles]


@router.get("/api/profiles/{profile_id}", response_model=ProfileOut)
async def get_profile(profile_id: str, session: SessionDep):
    return await deps.get_profile_or_404(session, profile_id)


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _step_payload(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent": event["agent"],
        "action": event["action"],
        "output_summary": event["output_summary"],
        "confidence": event["confidence"],
        "duration_ms": event["duration_ms"],
        "trace_id": event["trace_id"],
        "timestamp": event["timestamp"],
    }


async def _onboarding_stream(profile_id: str) -> AsyncIterator[str]:
    async with SessionLocal() as session:
        profile = await session.get(LearnerProfile, profile_id)
        if profile is None:
            yield _sse("error", {"detail": f"No learner profile found for id '{profile_id}'."})
            return

        if await deps.get_latest_roadmap(session, profile_id) is not None:
            yield _sse("complete", {"profile_id": profile_id, "already_built": True})
            return

        learner_profile = deps.profile_to_dict(profile)
        trigger = {"kind": "onboarding", "note": f"{profile.name} finished the intake form"}

        try:
            async for message in supervisor.stream_pipeline(
                session, profile_id=profile_id, learner_profile=learner_profile, trigger=trigger,
            ):
                if message["type"] == "step":
                    yield _sse("step", _step_payload(message["event"]))
                else:
                    saved = await persistence.save_pipeline_result(session, profile_id, message["state"])
                    yield _sse("complete", {
                        "profile_id": profile_id,
                        "gap_map_id": saved["gap_map"].id,
                        "roadmap_id": saved["roadmap"].id,
                        "already_built": False,
                    })
        except Exception:
            await session.rollback()
            traceback.print_exc()
            yield _sse("error", {"detail": "Building this learner's plan hit an unexpected snag - reloading will try again."})


@router.get("/api/profiles/{profile_id}/onboarding-stream")
async def stream_onboarding(profile_id: str):
    return StreamingResponse(
        _onboarding_stream(profile_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
