from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from backend.models.database import FsrsCard
from backend.models.schemas import FsrsReviewIn
from backend.routers import deps
from backend.routers.deps import SessionDep
from backend.utils import fsrs_engine, skill_graph

router = APIRouter(tags=["revision"])


def _card_detail(card: FsrsCard) -> dict[str, Any]:
    return {
        "id": card.id,
        "skill_id": card.skill_id,
        "skill_name": skill_graph.node(card.skill_id)["name"],
        "front": card.front,
        "back": card.back,
        "due_date": card.due_date.isoformat(),
        "is_due": card.due_date <= datetime.utcnow(),
        "retrievability": fsrs_engine.retrievability(card.state),
        "times_reviewed": len(card.review_history),
    }


@router.get("/api/revision/{profile_id}/deck")
async def get_revision_deck(profile_id: str, session: SessionDep) -> dict[str, Any]:
    await deps.get_profile_or_404(session, profile_id)
    cards = (await session.execute(
        select(FsrsCard).where(FsrsCard.profile_id == profile_id).order_by(FsrsCard.due_date)
    )).scalars().all()
    details = [_card_detail(card) for card in cards]
    return {
        "total_cards": len(details),
        "due_now": sum(1 for detail in details if detail["is_due"]),
        "cards": details,
    }


@router.post("/api/revision/{profile_id}/review")
async def submit_review(profile_id: str, payload: FsrsReviewIn, session: SessionDep) -> dict[str, Any]:
    await deps.get_profile_or_404(session, profile_id)
    card = await deps.get_or_404(session, FsrsCard, payload.card_id, label="revision card")
    if card.profile_id != profile_id:
        raise HTTPException(status_code=404, detail=f"No revision card found for id '{payload.card_id}'.")

    new_state, log = fsrs_engine.review(card.state, payload.rating)
    card.state = new_state
    card.due_date = datetime.fromisoformat(new_state["due"])
    card.last_review = datetime.utcnow()
    card.review_history = [*card.review_history, log]
    await session.commit()
    return {
        "id": card.id,
        "rating": payload.rating,
        "due_date": card.due_date.isoformat(),
        "retrievability": fsrs_engine.retrievability(card.state),
    }
