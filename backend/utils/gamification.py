from __future__ import annotations

from dataclasses import dataclass

POINTS_PER_COMPLETED_WEEK = 40
POINTS_PER_CHECKPOINT_PASSED = 120
POINTS_PER_CHECKPOINT_PARTIAL = 50
POINTS_PER_CHECKPOINT_FAILED_ATTEMPT = 10
POINTS_PER_INTERVIEW_ROUND = 30
POINTS_PER_STRONG_INTERVIEW_ANSWER = 15

_LEVELS = (
    ("Getting your bearings", 0),
    ("Building momentum", 150),
    ("Finding your rhythm", 350),
    ("Pulling ahead of the plan", 650),
    ("Interview-ready", 1050),
    ("Placement-floor sharp", 1600),
)


@dataclass(frozen=True)
class CheckpointFact:
    week: int
    band: str          # passed | partial | failed
    attempt_number: int


def _checkpoint_points(facts: list[CheckpointFact]) -> tuple[int, dict[str, int]]:
    best_per_week: dict[int, str] = {}
    rank = {"failed": 0, "partial": 1, "passed": 2}
    attempts_seen = 0
    for fact in facts:
        attempts_seen += 1
        current = best_per_week.get(fact.week)
        if current is None or rank[fact.band] > rank[current]:
            best_per_week[fact.week] = fact.band
    tally = {"passed": 0, "partial": 0, "failed": 0}
    points = 0
    for band in best_per_week.values():
        tally[band] += 1
        if band == "passed":
            points += POINTS_PER_CHECKPOINT_PASSED
        elif band == "partial":
            points += POINTS_PER_CHECKPOINT_PARTIAL
        else:
            points += POINTS_PER_CHECKPOINT_FAILED_ATTEMPT
    return points, {**tally, "weeks_scored": len(best_per_week), "attempts": attempts_seen}


def _level_for(points: int) -> dict:
    name, floor = _LEVELS[0]
    next_floor = _LEVELS[1][1] if len(_LEVELS) > 1 else floor
    for index, (level_name, level_floor) in enumerate(_LEVELS):
        if points >= level_floor:
            name, floor = level_name, level_floor
            next_floor = _LEVELS[index + 1][1] if index + 1 < len(_LEVELS) else level_floor
        else:
            break
    span = max(1, next_floor - floor)
    progress = min(1.0, round((points - floor) / span, 3)) if next_floor != floor else 1.0
    return {
        "name": name,
        "floor": floor,
        "next_floor": next_floor if next_floor != floor else None,
        "progress_to_next": progress,
    }


def _badges(*, completed_weeks: int, total_weeks: int, checkpoint_tally: dict[str, int],
            interview_rounds: int, strong_interview_answers: int, perfect_checkpoints: int) -> list[dict]:
    shelf = [
        {
            "id": "first_week",
            "label": "First week logged",
            "note": "Marked one full plan-week as done.",
            "earned": completed_weeks >= 1,
        },
        {
            "id": "halfway",
            "label": "Halfway through the plan",
            "note": f"Completed at least half of the {total_weeks}-week roadmap." if total_weeks else "Halfway through the roadmap.",
            "earned": total_weeks > 0 and completed_weeks * 2 >= total_weeks,
        },
        {
            "id": "checkpoint_cleared",
            "label": "First checkpoint cleared",
            "note": "Passed a weekly proctored test on the keyed-answer band.",
            "earned": checkpoint_tally.get("passed", 0) >= 1,
        },
        {
            "id": "checkpoint_streak",
            "label": "Three checkpoints cleared",
            "note": "Passed three different weekly tests outright.",
            "earned": checkpoint_tally.get("passed", 0) >= 3,
        },
        {
            "id": "perfect_paper",
            "label": "Clean sheet",
            "note": "Answered every question correctly on a checkpoint sitting.",
            "earned": perfect_checkpoints >= 1,
        },
        {
            "id": "interview_warm",
            "label": "Interview rehearsal underway",
            "note": "Finished a full mock interview round.",
            "earned": interview_rounds >= 1,
        },
        {
            "id": "interview_sharp",
            "label": "Answers landing well",
            "note": "Scored in the strong-answer band on multiple interview questions.",
            "earned": strong_interview_answers >= 3,
        },
        {
            "id": "plan_complete",
            "label": "Roadmap complete",
            "note": "Finished every week the active roadmap scheduled.",
            "earned": total_weeks > 0 and completed_weeks >= total_weeks,
        },
    ]
    return shelf


def summarize(
    *, completed_weeks: int, total_weeks: int,
    checkpoint_facts: list[CheckpointFact],
    perfect_checkpoints: int = 0,
    interview_rounds: int = 0,
    strong_interview_answers: int = 0,
) -> dict:
    module_points = completed_weeks * POINTS_PER_COMPLETED_WEEK
    checkpoint_points, checkpoint_tally = _checkpoint_points(checkpoint_facts)
    interview_points = (interview_rounds * POINTS_PER_INTERVIEW_ROUND) + (strong_interview_answers * POINTS_PER_STRONG_INTERVIEW_ANSWER)

    total = module_points + checkpoint_points + interview_points
    return {
        "points": total,
        "breakdown": {
            "modules": module_points,
            "checkpoints": checkpoint_points,
            "interviews": interview_points,
        },
        "level": _level_for(total),
        "badges": _badges(
            completed_weeks=completed_weeks, total_weeks=total_weeks, checkpoint_tally=checkpoint_tally,
            interview_rounds=interview_rounds, strong_interview_answers=strong_interview_answers,
            perfect_checkpoints=perfect_checkpoints,
        ),
        "checkpoint_tally": checkpoint_tally,
    }
