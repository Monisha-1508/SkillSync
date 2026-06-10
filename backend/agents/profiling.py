from __future__ import annotations

from backend.utils import llm, responsible_ai, skill_graph, tracing

FAMILY_TO_AXIS: dict[str, str] = {
    "Digital Literacy": "Core Programming",
    "Programming & Development": "Core Programming",
    "Tools & Collaboration": "Core Programming",
    "Software Quality": "Core Programming",
    "Mathematics": "Core Programming",
    "Data Structures & Algorithms": "Data Structures & Algorithms",
    "Software Design": "Systems & Design",
    "Systems": "Systems & Design",
    "Cloud & Platform": "Systems & Design",
    "DevOps & Platform": "Systems & Design",
    "Process & Delivery": "Systems & Design",
    "Data & Databases": "Data & Intelligence",
    "Statistics & Analytics": "Data & Intelligence",
    "Machine Learning": "Data & Intelligence",
    "Deep Learning": "Data & Intelligence",
    "MLOps & Deployment": "Data & Intelligence",
    "Visualization & Storytelling": "Data & Intelligence",
    "Business Context": "Data & Intelligence",
    "Frontend Development": "Product Engineering",
    "Backend Development": "Product Engineering",
    "Aptitude & Placement": "Placement & Career",
    "Communication": "Placement & Career",
    "Career Readiness": "Placement & Career",
    "Bridge & Re-skilling": "Placement & Career",
    "Emerging Tech": "Placement & Career",
}

AXIS_ORDER = [
    "Core Programming",
    "Data Structures & Algorithms",
    "Systems & Design",
    "Data & Intelligence",
    "Product Engineering",
    "Placement & Career",
]

_DIRECT_MASTERY = {1: 15, 2: 35, 3: 60, 4: 85, 5: 100}
_INFERRED_KNOWN_MASTERY = 80
_INFERRED_WEAK_MASTERY = 28
_UNRATED_MASTERY = 12


def _classify(entry: dict | None) -> tuple[str, int, int | None]:
    if entry is None:
        return "unknown", _UNRATED_MASTERY, None
    kind, rating = entry["status"], entry.get("rating")
    if kind == "direct":
        bucket = "covered" if rating >= 4 else "developing" if rating == 3 else "gap"
        return bucket, _DIRECT_MASTERY[rating], rating
    if kind == "inferred-known":
        return "covered", _INFERRED_KNOWN_MASTERY, rating
    return "gap", _INFERRED_WEAK_MASTERY, rating


def _top_names(items: list[dict], *, reverse: bool, limit: int = 3) -> list[str]:
    ranked = sorted(items, key=lambda i: i["_topo"])
    ranked = sorted(ranked, key=lambda i: i["mastery"], reverse=reverse)
    return [i["name"] for i in ranked[:limit]]


def _build_radar(items_by_id: dict[str, dict]) -> list[dict]:
    buckets: dict[str, list[dict]] = {axis: [] for axis in AXIS_ORDER}
    for item in items_by_id.values():
        axis = FAMILY_TO_AXIS.get(item["family"], "Placement & Career")
        buckets[axis].append(item)

    axes = []
    for axis in AXIS_ORDER:
        members = buckets[axis]
        if not members:
            continue
        score = round(sum(m["mastery"] for m in members) / len(members), 1)
        covered = sum(1 for m in members if m["status"] == "covered")
        axes.append({
            "axis": axis,
            "score": score,
            "node_count": len(members),
            "covered_count": covered,
        })
    return axes


async def run(learner_profile: dict) -> dict:
    role = learner_profile["target_role"]
    current_skills = learner_profile.get("current_skills", {})

    with tracing.traced_step(
        "profiling_diagnostician", "build_gap_map",
        input_summary=f"{role} | {len(current_skills)} self-ratings",
    ) as record:
        node_ids = skill_graph.role_node_ids(role)
        topo_index = {n: i for i, n in enumerate(node_ids)}
        inferred = skill_graph.infer_known_nodes(current_skills)

        buckets: dict[str, list[dict]] = {"covered": [], "developing": [], "gap": [], "unknown": []}
        items_by_id: dict[str, dict] = {}
        direct_n = inferred_n = 0

        for skill_id in node_ids:
            info = skill_graph.node(skill_id)
            entry = inferred.get(skill_id)
            bucket, mastery, rating = _classify(entry)
            if entry is not None:
                if entry["status"] == "direct":
                    direct_n += 1
                else:
                    inferred_n += 1
            item = {
                "skill_id": skill_id,
                "name": info["name"],
                "family": info["family"],
                "status": bucket,
                "mastery": mastery,
                "rating": rating,
                "source": entry["source"] if entry else "no signal yet",
                "hours": info["estimated_hours"],
                "bloom_level": info["bloom_level"],
                "_topo": topo_index[skill_id],
            }
            buckets[bucket].append(item)
            items_by_id[skill_id] = item

        radar_axes = _build_radar(items_by_id)
        confidence = responsible_ai.confidence_from_signal_mix(direct_n, inferred_n, len(node_ids))
        disclosure = responsible_ai.disclosure_for(confidence)

        weak_items = buckets["gap"] + buckets["developing"]
        top_strengths = _top_names(buckets["covered"], reverse=True)
        top_gaps = _top_names(weak_items, reverse=False)

        narration_ctx = {
            "name": learner_profile.get("name", "there"),
            "target_role": role,
            "top_strengths": top_strengths,
            "top_gaps": top_gaps,
            "known_count": len(buckets["covered"]),
            "weak_count": len(weak_items),
        }
        result = llm.get_llm_provider().narrate("gap_summary", narration_ctx)

        for bucket in buckets.values():
            bucket.sort(key=lambda i: i["_topo"])
            for i in bucket:
                i.pop("_topo", None)

        record["output_summary"] = (
            f"{len(buckets['covered'])} covered, {len(buckets['developing'])} developing, "
            f"{len(buckets['gap'])} gaps, {len(buckets['unknown'])} unrated "
            f"(confidence {confidence:.2f}, {result.provider})"
        )
        record["confidence"] = confidence

    return {
        "gap_map": {
            **buckets,
            "counts": {key: len(value) for key, value in buckets.items()},
            "total": len(node_ids),
        },
        "radar_axes": radar_axes,
        "confidence": confidence,
        "disclosure": disclosure,
        "summary": result.text,
        "narration_provider": result.provider,
        "trace": dict(record),
    }
