from __future__ import annotations

from backend.utils import feasibility, llm, skill_graph, tracing

WEEK_SLACK = 1.15

_DEFAULT_STRETCH_ADDONS = ["xtra.genai_prompting", "xtra.cloud_computing"]

_STRETCH_ADDONS: dict[str, list[str]] = {
    "Software Development Engineer": ["xtra.docker_containers", "xtra.genai_prompting"],
    "Data Analyst": ["xtra.genai_prompting", "xtra.technical_writing"],
    "Capgemini Technology Analyst": ["xtra.llm_apps_langchain", "xtra.cloud_computing"],
    "Data Scientist": ["xtra.llm_apps_langchain", "xtra.cloud_computing"],
    "Full Stack Developer": ["xtra.docker_containers", "xtra.genai_prompting"],
}

_VARIANT_ORDER = ("safe", "target", "stretch")


def _expand_addons(headline_ids: list[str]) -> list[str]:
    expanded: set[str] = set()
    for skill_id in headline_ids:
        expanded.add(skill_id)
        expanded.update(p for p in skill_graph.all_prerequisites(skill_id) if p.startswith("xtra."))
    return skill_graph.topo_rank(list(expanded))


def _expand_blackout_weeks(exam_blackouts: list[dict]) -> set[int]:
    weeks: set[int] = set()
    for window in exam_blackouts or []:
        start, end = window.get("start_week", 0), window.get("end_week", 0)
        if end >= start:
            weeks.update(range(start, end + 1))
    return weeks


def _build_milestones(
    skill_ids: list[str],
    weekly_hours: int,
    deadline_weeks: int,
    exam_blackouts: list[dict],
    *,
    start_week: int = 1,
) -> tuple[list[dict], list[str]]:
    blackout_weeks = _expand_blackout_weeks(exam_blackouts)
    queue = list(skill_ids)
    milestones: list[dict] = []
    week = start_week

    while week <= deadline_weeks and queue:
        if week in blackout_weeks:
            milestones.append({
                "week": week, "skill_ids": [], "hours": 0.0, "is_blackout": True,
                "note": "Exam window - kept deliberately light so revision does not compete with new ground.",
            })
            week += 1
            continue

        bucket: list[str] = []
        used = 0.0
        budget = weekly_hours * WEEK_SLACK
        while queue:
            hours = skill_graph.node(queue[0])["estimated_hours"]
            if not bucket or used + hours <= budget:
                bucket.append(queue.pop(0))
                used += hours
            else:
                break

        note = ""
        if used > budget + 0.01 and bucket:
            heavy = skill_graph.node(bucket[-1])
            note = (
                f"Runs heavier than the usual {weekly_hours}h week - \"{heavy['name']}\" is a "
                f"{heavy['estimated_hours']}-hour topic that holds together better as one push "
                f"than split across two weeks."
            )

        milestones.append({
            "week": week, "skill_ids": bucket, "hours": round(used, 1),
            "is_blackout": False, "note": note,
        })
        week += 1

    return milestones, queue


def replan_schedule(
    current_milestones: list[dict],
    reordered_pending_ids: list[str],
    weekly_hours: int,
    deadline_weeks: int,
    exam_blackouts: list[dict],
    from_week: int,
) -> tuple[list[dict], list[str]]:
    history = [m for m in current_milestones if m["week"] < from_week]
    fresh, overflow = _build_milestones(
        reordered_pending_ids, weekly_hours, deadline_weeks, exam_blackouts, start_week=from_week,
    )
    return history + fresh, overflow


def _variant_skill_ids(role: str, gap_ids: list[str]) -> dict[str, list[str]]:
    target_ids = gap_ids
    target_set = set(target_ids)
    safe_ids = [n for n in target_ids if "stretch" not in skill_graph.node(n)["tags"]]

    headline = _STRETCH_ADDONS.get(role, _DEFAULT_STRETCH_ADDONS)
    addons = [n for n in _expand_addons(headline) if n not in target_set]
    stretch_ids = target_ids + addons

    return {"safe": safe_ids, "target": target_ids, "stretch": stretch_ids}


def _build_variant(
    key: str, skill_ids: list[str], weekly_hours: int, deadline_weeks: int, exam_blackouts: list[dict],
) -> dict:
    milestones, overflow = _build_milestones(skill_ids, weekly_hours, deadline_weeks, exam_blackouts)
    total_hours = round(sum(skill_graph.node(n)["estimated_hours"] for n in skill_ids), 1)
    feas = feasibility.compute(total_hours, weekly_hours, deadline_weeks, exam_blackouts)
    focus = [skill_graph.node(n)["name"] for n in skill_ids[:3]]

    narrated = llm.get_llm_provider().narrate("roadmap_rationale", {
        "variant": key,
        "milestone_count": len(milestones),
        "total_hours": total_hours,
        "weekly_hours": weekly_hours,
        "deadline_weeks": deadline_weeks,
        "feasibility_score": feas["score"],
        "focus_skills": focus,
    })

    return {
        "variant": key,
        "skill_ids": skill_ids,
        "skill_count": len(skill_ids),
        "total_hours": total_hours,
        "milestone_count": len(milestones),
        "milestones": milestones,
        "overflow_skill_ids": overflow,
        "feasibility": feas,
        "rationale": narrated.text,
    }


def select_variant(roadmap_variants: dict, variant: str) -> dict:
    chosen = roadmap_variants[variant]
    return {
        "selected_variant": variant,
        "active_milestones": chosen["milestones"],
        "feasibility_score": chosen["feasibility"]["score"],
        "feasibility_explanation": chosen["feasibility"]["explanation"],
    }


async def run(learner_profile: dict, gap_map: dict) -> dict:
    role = learner_profile["target_role"]
    weekly_hours = learner_profile["weekly_hours"]
    deadline_weeks = learner_profile["deadline_weeks"]
    exam_blackouts = learner_profile.get("exam_blackouts", [])

    with tracing.traced_step(
        "roadmap_architect", "build_variants",
        input_summary=f"{role} | {weekly_hours}h/week x {deadline_weeks} weeks",
    ) as record:
        covered_ids = {item["skill_id"] for item in gap_map.get("covered", [])}
        ordered = skill_graph.role_node_ids(role)
        gap_ids = [n for n in ordered if n not in covered_ids]

        skill_id_sets = _variant_skill_ids(role, gap_ids)
        variants = {
            key: _build_variant(key, skill_id_sets[key], weekly_hours, deadline_weeks, exam_blackouts)
            for key in _VARIANT_ORDER
        }

        selected = "target"
        projection = select_variant(variants, selected)

        chosen = variants[selected]
        record["output_summary"] = (
            f"3 variants built (safe {variants['safe']['total_hours']:.0f}h / "
            f"target {chosen['total_hours']:.0f}h / stretch {variants['stretch']['total_hours']:.0f}h); "
            f"target feasibility {chosen['feasibility']['score']:.2f} over {chosen['milestone_count']} weeks"
        )
        record["confidence"] = chosen["feasibility"]["score"]

    return {
        "roadmap_variants": variants,
        **projection,
        "trace": dict(record),
    }
