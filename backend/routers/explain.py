from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.models.database import Resource, Roadmap
from backend.models.schemas import ExplainReplanIn, ExplainResourceIn, ExplainSkillIn
from backend.routers import deps
from backend.routers.deps import SessionDep
from backend.utils import llm, skill_graph

router = APIRouter(tags=["explain"])


def _skill_explainer_context(skill_id: str) -> dict[str, Any]:
    info = skill_graph.node(skill_id)
    downstream = skill_graph.unlocks(skill_id)
    return {
        "skill_name": info["name"],
        "family": info["family"],
        "hours": info["estimated_hours"],
        "unlocks_sample": [skill_graph.node(child)["name"] for child in downstream[:3]],
        "unlocks_count": len(downstream),
        "placement_relevance": "placement" in info["tags"],
        "bloom_level": info["bloom_level"],
    }


@router.post("/api/explain/{profile_id}/skill")
async def explain_skill(profile_id: str, payload: ExplainSkillIn, session: SessionDep) -> dict[str, Any]:
    await deps.get_profile_or_404(session, profile_id)
    try:
        context = _skill_explainer_context(payload.skill_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"No skill found for id '{payload.skill_id}'.")

    narrated = llm.get_llm_provider().narrate("skill_explainer", context)
    return {
        "agent": "profiling_diagnostician",
        "skill_id": payload.skill_id,
        "skill_name": context["skill_name"],
        "explanation": narrated.text,
    }


def _resource_why_context(resource: Resource) -> dict[str, Any]:
    return {
        "resource_title": resource.title,
        "source": resource.source,
        "skill_name": skill_graph.node(resource.skill_id)["name"],
        "trust_score": resource.trust_score,
        "resource_type": resource.resource_type,
    }


@router.post("/api/explain/{profile_id}/resource")
async def explain_resource(profile_id: str, payload: ExplainResourceIn, session: SessionDep) -> dict[str, Any]:
    await deps.get_profile_or_404(session, profile_id)
    resource = await deps.get_or_404(session, Resource, payload.resource_id, label="learning resource")

    narrated = llm.get_llm_provider().narrate("resource_why", _resource_why_context(resource))
    return {
        "agent": "resource_curator",
        "resource_id": resource.id,
        "resource_title": resource.title,
        "explanation": narrated.text,
    }


@router.post("/api/explain/{profile_id}/replan")
async def explain_replan(profile_id: str, payload: ExplainReplanIn, session: SessionDep) -> dict[str, Any]:
    await deps.get_profile_or_404(session, profile_id)
    roadmap = await deps.get_or_404(session, Roadmap, payload.roadmap_id, label="roadmap")
    if roadmap.profile_id != profile_id:
        raise HTTPException(status_code=404, detail=f"No roadmap found for id '{payload.roadmap_id}'.")

    proposal = roadmap.pending_replan or (roadmap.replan_log[-1] if roadmap.replan_log else None)
    if proposal is None:
        raise HTTPException(status_code=404, detail="This learner has no replan - proposed or decided - to explain yet.")

    return {
        "agent": "coach_adapter",
        "status": proposal["status"],
        "missed_week": proposal["missed_week"],
        "explanation": proposal["rationale"],
        "decided_at": proposal.get("decided_at"),
    }
