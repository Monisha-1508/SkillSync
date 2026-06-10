"""
Generates the 50-row golden evaluation set at backend/data/golden_eval.json.

Design choice that matters for the demo: rows store *inputs* plus the policy
thresholds (trust floor, max permitted Bloom regression). They do not store
hand-guessed "expected outputs" like milestone counts, because the only
trustworthy expectation for a generative planner is one derived from the same
graph the planner reads at run time. Pre-baking a fixed "expected_milestones:
[9, 14]" would silently go stale the moment someone edits skill_chains.py, and
a stale golden file is worse than none - it fails honest changes and passes
broken ones. So test_golden.py derives every structural expectation
(prerequisite order, hour-based milestone bounds, Bloom progression) live from
backend.utils.skill_graph, and only the *policy* numbers - which are product
decisions, not graph properties - travel with the row.

Run:
    python -m backend.data.scripts.build_golden_eval
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.data.skill_chains import ROLE_TRACKS  # noqa: E402

ROLES = list(ROLE_TRACKS.keys())
PLACEMENT_MODES = ["tcs_nqt", "cap_exceller", "infytq", "wipro_nlth", "general"]
BACKGROUNDS = ["cs", "cs", "cs", "non_cs", "diploma"]

SKILL_LABELS = [
    "Python", "SQL", "Data Structures & Algorithms", "Java", "Aptitude",
    "Communication", "Excel", "Statistics", "Object-Oriented Programming",
    "JavaScript", "System Design", "Data Visualization",
]

ARCHETYPES = {
    "weak": (1, 2),
    "mixed": (1, 4),
    "strong": (3, 5),
}

TRUST_FLOOR = 0.55
MAX_BLOOM_REGRESSION = 1


def _lcg(seed: int):
    """Tiny linear-congruential generator - deterministic across machines and
    Python versions, unlike relying on `random` module internals."""
    state = seed
    while True:
        state = (1103515245 * state + 12345) % (2 ** 31)
        yield state


def build_rows(count: int = 50) -> list[dict]:
    rng = _lcg(seed=20260607)
    rows = []
    for i in range(count):
        role = ROLES[i % len(ROLES)]
        archetype_name = list(ARCHETYPES.keys())[i % len(ARCHETYPES)]
        lo, hi = ARCHETYPES[archetype_name]

        n1, n2, n3, n4 = (next(rng) for _ in range(4))
        weekly_hours = 6 + (n1 % 20)               # 6..25
        deadline_weeks = 8 + (n2 % 17)              # 8..24
        skill_count = 4 + (n3 % 3)                  # 4..6 stated skills
        chosen_skills = [SKILL_LABELS[(i + j * 3) % len(SKILL_LABELS)] for j in range(skill_count)]
        ratings = {
            label: lo + ((n4 + idx * 7) % (hi - lo + 1))
            for idx, label in enumerate(chosen_skills)
        }

        row = {
            "id": f"golden-{i + 1:03d}",
            "label": f"{role} / {archetype_name} profile / {deadline_weeks}w @ {weekly_hours}h",
            "input": {
                "name": f"Golden Scenario {i + 1:03d}",
                "target_role": role,
                "target_companies": ["Capgemini"],
                "current_skills": ratings,
                "weekly_hours": weekly_hours,
                "deadline_weeks": deadline_weeks,
                "budget_mode": "free" if i % 3 else "paid",
                "placement_mode": PLACEMENT_MODES[i % len(PLACEMENT_MODES)],
                "background": BACKGROUNDS[i % len(BACKGROUNDS)],
                "exam_blackouts": [],
            },
            "trust_floor": TRUST_FLOOR,
            "max_bloom_regression": MAX_BLOOM_REGRESSION,
        }
        rows.append(row)
    return rows


def main() -> None:
    rows = build_rows(50)
    out_path = Path(__file__).resolve().parents[1] / "golden_eval.json"
    out_path.write_text(json.dumps({"version": 1, "rows": rows}, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} golden rows to {out_path}")
    by_role: dict[str, int] = {}
    for row in rows:
        by_role[row["input"]["target_role"]] = by_role.get(row["input"]["target_role"], 0) + 1
    for role, n in by_role.items():
        print(f"  {role}: {n} rows")


if __name__ == "__main__":
    main()
