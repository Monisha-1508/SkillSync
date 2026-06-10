from __future__ import annotations

REALISM_FACTOR = 0.8

_ANCHORS: list[tuple[float, float]] = [
    (0.40, 0.12),
    (0.70, 0.40),
    (0.90, 0.58),
    (1.00, 0.68),
    (1.20, 0.82),
    (1.50, 0.93),
    (2.00, 0.97),
]


def _interpolate(ratio: float) -> float:
    if ratio <= _ANCHORS[0][0]:
        return _ANCHORS[0][1]
    if ratio >= _ANCHORS[-1][0]:
        return _ANCHORS[-1][1]
    for (x0, y0), (x1, y1) in zip(_ANCHORS, _ANCHORS[1:]):
        if x0 <= ratio <= x1:
            t = (ratio - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return 0.5  # unreachable given the bounds above; keeps the type checker calm


def blackout_weeks(exam_blackouts: list[dict]) -> int:
    total = 0
    for window in exam_blackouts:
        start, end = window.get("start_week", 0), window.get("end_week", 0)
        if end >= start:
            total += (end - start + 1)
    return total


def compute(total_hours: float, weekly_hours: int, deadline_weeks: int,
            exam_blackouts: list[dict] | None = None) -> dict:
    blackouts = blackout_weeks(exam_blackouts or [])
    effective_weeks = max(1, deadline_weeks - blackouts)
    available_hours = round(effective_weeks * weekly_hours * REALISM_FACTOR, 1)
    ratio = available_hours / total_hours if total_hours > 0 else 1.0
    score = round(_interpolate(ratio), 3)

    if score >= 0.8:
        verdict = "comfortably achievable"
    elif score >= 0.6:
        verdict = "achievable but with little slack"
    elif score >= 0.4:
        verdict = "tight - expect to trim scope or extend the deadline"
    else:
        verdict = "unrealistic as scoped - the plan needs to shrink or the runway needs to grow"

    blackout_clause = f", after setting aside {blackouts} blackout week{'s' if blackouts != 1 else ''}," if blackouts else ""
    explanation = (
        f"At {weekly_hours}h a week for {effective_weeks} working weeks{blackout_clause} "
        f"and assuming a realistic {int(REALISM_FACTOR * 100)} percent of that gets used most weeks, "
        f"there are roughly {available_hours:.0f} hours available against {total_hours:.0f} needed "
        f"(a {ratio:.2f}x margin). That makes this path {verdict}."
    )

    return {
        "score": score,
        "ratio": round(ratio, 3),
        "available_hours": available_hours,
        "effective_weeks": effective_weeks,
        "blackout_weeks": blackouts,
        "verdict": verdict,
        "explanation": explanation,
    }
