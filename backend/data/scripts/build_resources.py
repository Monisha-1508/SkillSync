from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.data.resource_bank import SOURCE_BANK, trust_score  # noqa: E402
from backend.data.skill_chains import ALL_CHAINS  # noqa: E402

DIFFICULTY_RANK = {"beginner": 0, "intermediate": 1, "advanced": 2}
BLOOM_FOR_DIFFICULTY = {"beginner": 2, "intermediate": 4, "advanced": 5}


def _quality_score(tag_overlap: int, source_authority: float, difficulty_gap: int) -> float:
    base = 0.55 + 0.1 * tag_overlap
    base += 0.05 * source_authority
    base -= 0.07 * difficulty_gap
    return round(max(0.35, min(0.97, base)), 3)


def _pick_resources(skill, max_free: int = 3, max_paid: int = 2) -> list[dict]:
    free_candidates: list = []
    paid_candidates: list = []

    for source in SOURCE_BANK:
        overlap = len(set(source.tags) & set(skill.tags))
        if overlap == 0:
            continue
        gap = abs(DIFFICULTY_RANK[source.base_difficulty] - DIFFICULTY_RANK[skill.difficulty])
        entry = (overlap, gap, source)
        if source.cost == "paid":
            paid_candidates.append(entry)
        else:
            free_candidates.append(entry)

    sort_key = lambda c: (-c[0], c[1], -c[2].authority)  # noqa: E731

    if not free_candidates and not paid_candidates:
        fallback = [
            (1, abs(DIFFICULTY_RANK[s.base_difficulty] - DIFFICULTY_RANK[skill.difficulty]), s)
            for s in SOURCE_BANK
            if "foundation" in s.tags or "career" in s.tags
        ]
        fallback.sort(key=sort_key)
        free_candidates = fallback

    free_candidates.sort(key=sort_key)
    paid_candidates.sort(key=sort_key)
    picked = free_candidates[:max_free] + paid_candidates[:max_paid]

    out = []
    for overlap, gap, source in picked:
        quality = _quality_score(overlap, source.authority, gap)
        score = trust_score(source.authority, source.recency, source.community, quality)
        out.append({
            "skill_id": skill.key,
            "title": source.title,
            "url": source.url,
            "source": source.source,
            "resource_type": source.resource_type,
            "difficulty": source.base_difficulty,
            "bloom_level": BLOOM_FOR_DIFFICULTY[source.base_difficulty],
            "cost": source.cost,
            "published_year": 2024,
            "authority_score": source.authority,
            "recency_score": source.recency,
            "community_score": source.community,
            "quality_score": quality,
            "trust_score": score,
            "tag_overlap": overlap,
        })
    return out


def build_corpus() -> list[dict]:
    corpus: list[dict] = []
    seen_skills: set[str] = set()
    for chain in ALL_CHAINS.values():
        for skill in chain:
            if skill.key in seen_skills:
                continue
            seen_skills.add(skill.key)
            corpus.extend(_pick_resources(skill))
    return corpus


def main() -> None:
    corpus = build_corpus()
    out_path = Path(__file__).resolve().parents[1] / "resources_seed.json"
    out_path.write_text(json.dumps({"version": 1, "resources": corpus}, indent=2), encoding="utf-8")

    unique_urls = {r["url"] for r in corpus}
    avg_trust = sum(r["trust_score"] for r in corpus) / len(corpus)
    below_floor = sum(1 for r in corpus if r["trust_score"] < 0.55)
    print(f"Wrote {len(corpus)} resource pairings from {len(unique_urls)} unique sources to {out_path}")
    print(f"Average trust score: {avg_trust:.3f} | pairings below 0.55 floor: {below_floor}")


if __name__ == "__main__":
    main()
