from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import Resource
from backend.utils import llm, skill_graph, tracing

TRUST_FLOOR = 0.55
PICKS_PER_SKILL = 2


async def _candidates(session: AsyncSession, skill_id: str) -> list[Resource]:
    rows = await session.execute(
        select(Resource).where(Resource.skill_id == skill_id).order_by(Resource.trust_score.desc())
    )
    return list(rows.scalars().all())


def _entry(resource: Resource, skill_name: str) -> dict:
    narrated = llm.get_llm_provider().narrate("resource_why", {
        "resource_title": resource.title,
        "source": resource.source,
        "skill_name": skill_name,
        "trust_score": resource.trust_score,
        "resource_type": resource.resource_type,
    })
    return {
        "resource_id": resource.id,
        "skill_id": resource.skill_id,
        "title": resource.title,
        "url": resource.url,
        "source": resource.source,
        "resource_type": resource.resource_type,
        "difficulty": resource.difficulty,
        "bloom_level": resource.bloom_level,
        "cost": resource.cost,
        "trust_score": resource.trust_score,
        "why": narrated.text,
    }


def _apply_budget_filter(
    qualified: list[Resource],
    budget_mode: str,
    limit: int,
) -> list[Resource]:
    if budget_mode == "paid":
        paid = [r for r in qualified if r.cost == "paid"]
        free = [r for r in qualified if r.cost == "free"]
        return (paid + free)[:limit]
    return [r for r in qualified if r.cost == "free"][:limit]


async def run(
    session: AsyncSession,
    skill_ids: list[str],
    *,
    limit_per_skill: int = PICKS_PER_SKILL,
    budget_mode: str = "free",
) -> dict:
    ordered_unique = skill_graph.topo_rank(list(dict.fromkeys(skill_ids)))

    with tracing.traced_step(
        "resource_curator", "curate_resources",
        input_summary=(
            f"{len(ordered_unique)} skills, trust floor {TRUST_FLOOR:.2f}, "
            f"budget={budget_mode}"
        ),
    ) as record:
        picks: dict[str, list[dict]] = {}
        trust_values: list[float] = []
        below_floor = 0
        skills_with_no_match = 0

        for skill_id in ordered_unique:
            candidates = await _candidates(session, skill_id)
            qualified = [r for r in candidates if r.trust_score >= TRUST_FLOOR]
            below_floor += len(candidates) - len(qualified)

            chosen = _apply_budget_filter(qualified, budget_mode, limit_per_skill)
            if not chosen:
                skills_with_no_match += 1
            skill_name = skill_graph.node(skill_id)["name"]
            picks[skill_id] = [_entry(resource, skill_name) for resource in chosen]
            trust_values.extend(resource.trust_score for resource in chosen)

        average_trust = round(sum(trust_values) / len(trust_values), 3) if trust_values else 0.0
        total_picked = sum(len(v) for v in picks.values())

        record["output_summary"] = (
            f"{total_picked} resources picked across {len(ordered_unique)} skills "
            f"(budget={budget_mode}, avg trust {average_trust:.2f}, "
            f"{below_floor} below floor excluded"
            f"{f', {skills_with_no_match} skills unmatched' if skills_with_no_match else ''})"
        )
        record["confidence"] = average_trust

    return {
        "resource_picks": picks,
        "average_trust": average_trust,
        "below_floor_excluded": below_floor,
        "trust_floor": TRUST_FLOOR,
        "budget_mode": budget_mode,
        "trace": dict(record),
    }
