from __future__ import annotations

import copy
from datetime import datetime
from typing import Any



def apply_reflow(
    active_milestones: list[dict[str, Any]],
    missed_week_number: int,
    deadline_weeks: int,
    weekly_hours: int = 10,
) -> dict[str, Any]:
    milestones = [dict(m) for m in active_milestones]
    milestones.sort(key=lambda m: m["week"])

    missed_m = next((m for m in milestones if m["week"] == missed_week_number), None)
    if missed_m is None:
        raise ValueError(
            f"Week {missed_week_number} does not appear in this roadmap's active schedule."
        )
    if missed_m.get("is_blackout"):
        raise ValueError(
            f"Week {missed_week_number} is a blackout week and cannot be marked missed."
        )
    if missed_m.get("is_missed"):
        raise ValueError(
            f"Week {missed_week_number} has already been marked missed and reflowed."
        )

    displaced_skills: list[str] = list(missed_m.get("skill_ids") or [])
    displaced_hours: float = float(missed_m.get("hours") or 0)

    missed_m["is_missed"] = True
    missed_m["original_hours"] = displaced_hours
    missed_m["skill_ids"] = []
    missed_m["hours"] = 0.0
    missed_m["note"] = (
        f"Week {missed_week_number} was not completed - "
        f"{len(displaced_skills)} skill(s) and {displaced_hours:.0f}h carried forward."
    )

    future_active = [
        m for m in milestones
        if m["week"] > missed_week_number
        and not m.get("is_blackout")
        and not m.get("is_missed")
    ]

    if not future_active:
        return {
            "active_milestones": milestones,
            "deadline_breach": False,
            "compression_applied": False,
            "compression_detail": None,
            "reflow_summary": (
                f"Week {missed_week_number} marked as missed. "
                "It was the last scheduled week, so no further merge is needed."
            ),
            "breach_message": None,
        }

    merge_target = future_active[0]
    original_target_week = merge_target["week"]

    existing_skills: list[str] = list(merge_target.get("skill_ids") or [])
    added_skills = [s for s in displaced_skills if s not in existing_skills]
    merge_target["skill_ids"] = added_skills + existing_skills
    merge_target["hours"] = round(
        float(merge_target.get("hours") or 0) + displaced_hours, 1
    )
    merge_target["is_merged"] = True
    merge_target["merged_from_weeks"] = sorted(
        set(list(merge_target.get("merged_from_weeks") or [original_target_week])
            + [missed_week_number])
    )
    merge_target["note"] = (
        f"Merged: absorbs {len(added_skills)} skill(s) and {displaced_hours:.0f}h "
        f"from missed week {missed_week_number}."
    )

    active_count = sum(1 for m in milestones if not m.get("is_blackout"))
    calendar_breach = active_count > deadline_weeks
    workload_breach = weekly_hours > 0 and merge_target["hours"] > weekly_hours * 1.5
    deadline_breach = calendar_breach or workload_breach

    compression_applied = False
    compression_detail = None

    if calendar_breach:
        milestones, compression_applied, compression_detail = _compress(
            milestones,
            protected_weeks={missed_week_number, merge_target["week"]},
        )

    breach_message: str | None = None
    if deadline_breach:
        if compression_applied:
            breach_message = (
                "The reflowed plan exceeded the "
                f"{deadline_weeks}-week target. Two lighter weeks were merged "
                "to bring it back within the deadline."
            )
        elif calendar_breach:
            breach_message = (
                f"The reflowed plan now exceeds the {deadline_weeks}-week target "
                "by one week. There were not enough light weeks available to "
                "compress - consider extending your deadline by one week."
            )
        else:
            breach_message = (
                f"Week {merge_target['week']} now carries {merge_target['hours']:.0f}h - "
                f"about {merge_target['hours'] / max(weekly_hours, 1):.1f}x your usual "
                f"{weekly_hours}h budget. Consider splitting it with a study partner "
                "or extending your deadline by one week."
            )

    reflow_summary = (
        f"Week {missed_week_number}: {len(displaced_skills)} skill(s) and "
        f"{displaced_hours:.0f}h carried into week {original_target_week} "
        f"(now {merge_target['hours']:.0f}h total). "
        + (
            "Deadline breach resolved by merging two lighter weeks."
            if compression_applied
            else "Deadline breach - consider extending by one week."
            if deadline_breach
            else "Schedule fits within the original deadline."
        )
    )

    milestones.sort(key=lambda m: m["week"])
    return {
        "active_milestones": milestones,
        "deadline_breach": deadline_breach,
        "compression_applied": compression_applied,
        "compression_detail": compression_detail,
        "reflow_summary": reflow_summary,
        "breach_message": breach_message,
    }



def _compress(
    milestones: list[dict[str, Any]],
    protected_weeks: set[int],
) -> tuple[list[dict[str, Any]], bool, str | None]:
    candidates = sorted(
        [
            m for m in milestones
            if not m.get("is_blackout")
            and not m.get("is_missed")
            and m["week"] not in protected_weeks
        ],
        key=lambda m: m["week"],
    )

    if len(candidates) < 2:
        return milestones, False, None

    best_pair: tuple[dict, dict] | None = None
    best_hours = float("inf")

    for i in range(len(candidates) - 1):
        a, b = candidates[i], candidates[i + 1]
        weeks_between = [
            m["week"] for m in milestones
            if not m.get("is_blackout")
            and a["week"] < m["week"] < b["week"]
        ]
        if weeks_between:
            continue  # not truly adjacent
        combined = float(a.get("hours") or 0) + float(b.get("hours") or 0)
        if combined < best_hours:
            best_hours = combined
            best_pair = (a, b)

    if best_pair is None:
        return milestones, False, None

    lighter, heavier = (
        (best_pair[0], best_pair[1])
        if (best_pair[0].get("hours") or 0) <= (best_pair[1].get("hours") or 0)
        else (best_pair[1], best_pair[0])
    )
    absorbed_week = lighter["week"]
    receive_week = heavier["week"]

    h_skills: list[str] = list(heavier.get("skill_ids") or [])
    added = [s for s in (lighter.get("skill_ids") or []) if s not in h_skills]
    heavier["skill_ids"] = added + h_skills
    heavier["hours"] = round(
        float(heavier.get("hours") or 0) + float(lighter.get("hours") or 0), 1
    )
    heavier["is_merged"] = True
    prior = list(heavier.get("merged_from_weeks") or [receive_week])
    heavier["merged_from_weeks"] = sorted(set(prior + [absorbed_week]))
    existing_note = heavier.get("note") or ""
    heavier["note"] = (
        (existing_note + " " if existing_note else "")
        + f"Compressed with week {absorbed_week} to fit the deadline."
    ).strip()

    # Remove the lighter week from the schedule
    milestones = [m for m in milestones if m["week"] != absorbed_week]

    detail = (
        f"Week {absorbed_week} ({lighter.get('hours', 0):.0f}h) merged into "
        f"week {receive_week} ({heavier['hours']:.0f}h combined) to fit the deadline."
    )
    return milestones, True, detail



def reflow_log_entry(
    missed_week: int,
    result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "operation": "reflow",
        "missed_week": missed_week,
        "merged_into_week": next(
            (
                m["week"]
                for m in result["active_milestones"]
                if m.get("is_merged") and missed_week in (m.get("merged_from_weeks") or [])
            ),
            None,
        ),
        "deadline_breach": result["deadline_breach"],
        "compression_applied": result["compression_applied"],
        "compression_detail": result["compression_detail"],
        "reflow_summary": result["reflow_summary"],
        "breach_message": result["breach_message"],
        "applied_at": datetime.utcnow().isoformat(),
    }
