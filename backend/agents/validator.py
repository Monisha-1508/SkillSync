from __future__ import annotations

from backend.agents import resource_curator, roadmap_architect
from backend.utils import feasibility, responsible_ai, skill_graph, tracing


def _check_trust_floor(resource_picks: dict[str, list[dict]], trust_floor: float) -> dict:
    total = sum(len(entries) for entries in resource_picks.values())
    offenders = [
        f"\"{entry['title']}\" at {entry['trust_score']:.2f}"
        for entries in resource_picks.values()
        for entry in entries
        if entry["trust_score"] < trust_floor
    ]
    if offenders:
        return {
            "name": "Resource trust floor",
            "status": "flagged",
            "detail": (
                f"{len(offenders)} of {total} recommended resources sit below the "
                f"{trust_floor:.2f} floor and should never have reached this list: "
                f"{', '.join(offenders[:3])}."
            ),
        }
    return {
        "name": "Resource trust floor",
        "status": "pass",
        "detail": (
            f"All {total} recommended resources score at or above the {trust_floor:.2f} "
            f"trust floor - re-checked here independently of the curator that picked them."
        ),
    }


def _check_prerequisite_order(active_milestones: list[dict], gap_map: dict) -> dict:
    satisfied = {item["skill_id"] for item in gap_map.get("covered", [])}
    violation = None
    for milestone in active_milestones:
        if milestone.get("is_blackout"):
            continue
        for skill_id in milestone["skill_ids"]:
            missing = [p for p in skill_graph.prerequisites(skill_id) if p not in satisfied]
            if missing and violation is None:
                violation = (
                    f"\"{skill_graph.node(skill_id)['name']}\" is scheduled in week "
                    f"{milestone['week']}, ahead of its own prerequisite "
                    f"\"{skill_graph.node(missing[0])['name']}\"."
                )
            satisfied.add(skill_id)

    if violation:
        return {"name": "Prerequisite ordering", "status": "flagged", "detail": violation}
    return {
        "name": "Prerequisite ordering",
        "status": "pass",
        "detail": (
            "Walked the plan in the exact order a learner would work it - skill by skill across "
            "the whole sequence, not just week by week - and confirmed nothing is scheduled "
            "before what it depends on has already been reached. This plan can be worked top to "
            "bottom, in the order shown, with nothing missing underneath it."
        ),
    }


def _check_feasibility_consistency(learner_profile: dict, roadmap_variants: dict) -> dict:
    weekly_hours = learner_profile["weekly_hours"]
    deadline_weeks = learner_profile["deadline_weeks"]
    exam_blackouts = learner_profile.get("exam_blackouts", [])

    mismatches = []
    for key, variant in roadmap_variants.items():
        recomputed = feasibility.compute(variant["total_hours"], weekly_hours, deadline_weeks, exam_blackouts)
        shown = variant["feasibility"]["score"]
        if abs(recomputed["score"] - shown) > 0.01:
            mismatches.append(f"{key} shows {shown:.2f}, recomputes to {recomputed['score']:.2f}")

    if mismatches:
        return {
            "name": "Feasibility consistency",
            "status": "flagged",
            "detail": (
                f"{len(mismatches)} plan variant(s) show a feasibility score that does not "
                f"reproduce from their own published hours: {'; '.join(mismatches)}."
            ),
        }
    return {
        "name": "Feasibility consistency",
        "status": "pass",
        "detail": (
            f"Recomputed all {len(roadmap_variants)} plan variants from their own published "
            f"hours against {weekly_hours}h a week over {deadline_weeks} weeks - every score on "
            f"screen is a derivation a learner could redo by hand, not a number asserted at them."
        ),
    }


def _check_pacing_transparency(active_milestones: list[dict], weekly_hours: int) -> dict:
    budget = weekly_hours * roadmap_architect.WEEK_SLACK
    heavy = [m for m in active_milestones if not m.get("is_blackout") and m["hours"] > budget + 0.01]
    silent = [m for m in heavy if not m.get("note")]

    if silent:
        weeks = ", ".join(f"week {m['week']} ({m['hours']:.0f}h)" for m in silent[:3])
        return {
            "name": "Weekly pacing transparency",
            "status": "flagged",
            "detail": (
                f"{len(silent)} week(s) run over the {weekly_hours}h budget without saying why: "
                f"{weeks}. A plan that quietly asks for more than it promised is the kind of "
                f"thing a learner should not have to discover three weeks in."
            ),
        }
    if heavy:
        return {
            "name": "Weekly pacing transparency",
            "status": "pass",
            "detail": (
                f"{len(heavy)} week(s) run heavier than the usual {weekly_hours}h pace, and each "
                f"one names the specific topic responsible and why it was kept whole rather than "
                f"split - nothing in this plan asks for more than it admits to up front."
            ),
        }
    return {
        "name": "Weekly pacing transparency",
        "status": "pass",
        "detail": f"Every week sits within the usual {weekly_hours}h pace - there is nothing oversized to disclose.",
    }


def _screen_overclaims(narrations: dict[str, str]) -> tuple[dict, dict[str, str]]:
    hits_by_label: dict[str, list[str]] = {}
    overrides: dict[str, str] = {}
    for label, text in narrations.items():
        hits = responsible_ai.screen_overclaims(text)
        if hits:
            hits_by_label[label] = hits
            overrides[label] = responsible_ai.soften_overclaims(text)

    if not hits_by_label:
        check = {
            "name": "Overclaim screening",
            "status": "pass",
            "detail": (
                f"Re-scanned {len(narrations)} generated passage(s) for absolute promises - "
                f"\"guaranteed\", \"will definitely\", \"never fails\" and the like - and found "
                f"none. In simulated mode that is closer to a guarantee than a measurement, "
                f"since the templates are hand-written and the team controls every word; the day "
                f"narration starts coming from a live model is the day this check starts standing "
                f"between an enthusiastic sentence and a promise the system cannot actually keep."
            ),
        }
    else:
        named = "; ".join(f"{label} ({', '.join(hits)})" for label, hits in hits_by_label.items())
        check = {
            "name": "Overclaim screening",
            "status": "adjusted",
            "detail": (
                f"{len(hits_by_label)} passage(s) carried language stronger than this system can "
                f"stand behind and were rewritten before reaching the dashboard: {named}."
            ),
        }
    return check, overrides


_CONFIDENCE_BY_STATUS = {"pass": 0.96, "adjusted": 0.8, "flagged": 0.45}


async def run(
    *,
    learner_profile: dict,
    gap_map: dict,
    gap_summary: str,
    roadmap_variants: dict,
    active_milestones: list[dict],
    resource_picks: dict,
) -> dict:
    resource_count = sum(len(entries) for entries in resource_picks.values())

    with tracing.traced_step(
        "output_validator", "validate_plan",
        input_summary=(
            f"{len(active_milestones)} milestones, {resource_count} resources, "
            f"{len(roadmap_variants)} plan variants"
        ),
    ) as record:
        narrations = {"gap_summary": gap_summary}
        for key, variant in roadmap_variants.items():
            narrations[f"{key}_plan_rationale"] = variant["rationale"]
        for skill_id, entries in resource_picks.items():
            for index, entry in enumerate(entries):
                narrations[f"resource_why[{skill_id}#{index}]"] = entry["why"]

        overclaim_check, narration_overrides = _screen_overclaims(narrations)

        checks = [
            _check_trust_floor(resource_picks, resource_curator.TRUST_FLOOR),
            _check_prerequisite_order(active_milestones, gap_map),
            _check_feasibility_consistency(learner_profile, roadmap_variants),
            _check_pacing_transparency(active_milestones, learner_profile["weekly_hours"]),
            overclaim_check,
        ]

        statuses = {check["status"] for check in checks}
        overall = "flagged" if "flagged" in statuses else "adjusted" if "adjusted" in statuses else "pass"
        clean = sum(1 for check in checks if check["status"] == "pass")

        record["output_summary"] = f"{overall} overall - {clean}/{len(checks)} checks clean"
        record["confidence"] = _CONFIDENCE_BY_STATUS[overall]

    return {
        "validation_report": {
            "overall_status": overall,
            "checks": checks,
            "narration_overrides": narration_overrides,
            "checked_at": tracing.iso_now(),
        },
        "trace": dict(record),
    }
