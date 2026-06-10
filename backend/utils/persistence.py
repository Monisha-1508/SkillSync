from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import AuditLog, FsrsCard, GapMap, Roadmap
from backend.models.state import SkillSyncState
from backend.utils import fsrs_engine


def _fresh_card(profile_id: str, card: dict[str, Any]) -> FsrsCard:
    state = fsrs_engine.new_card_state()
    return FsrsCard(
        profile_id=profile_id,
        skill_id=card["skill_id"],
        front=card["front"],
        back=card["back"],
        state=state,
        due_date=datetime.fromisoformat(state["due"]),
    )


async def save_pipeline_result(session: AsyncSession, profile_id: str, state: SkillSyncState) -> dict[str, Any]:
    gap_map_row = GapMap(
        profile_id=profile_id,
        skill_gaps=state["gap_map"],
        radar_axes=state["radar_axes"],
        confidence=state["gap_confidence"],
        summary=state["gap_summary"],
    )
    roadmap_row = Roadmap(
        profile_id=profile_id,
        selected_variant=state["selected_variant"],
        variants=state["roadmap_variants"],
        active_milestones=state["active_milestones"],
        feasibility_score=state["feasibility_score"],
        feasibility_explanation=state["feasibility_explanation"],
    )
    card_rows = [_fresh_card(profile_id, card) for card in state["fsrs_deck"]]
    audit_rows = [AuditLog(**{**entry, "timestamp": datetime.fromisoformat(entry["timestamp"])}) for entry in state["audit_log"]]

    session.add_all([gap_map_row, roadmap_row, *card_rows, *audit_rows])
    await session.commit()

    return {"gap_map": gap_map_row, "roadmap": roadmap_row, "fsrs_cards": card_rows}
