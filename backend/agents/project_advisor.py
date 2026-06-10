from __future__ import annotations

from backend.data.project_bank import ProjectEntry, projects_for_tracks
from backend.utils import llm, skill_graph, tracing

PICKS = 4
_DIFFICULTY_RANK = {"beginner": 0, "intermediate": 1, "advanced": 2}


def _balanced_shortlist(candidates: list[ProjectEntry], limit: int) -> list[ProjectEntry]:
    chosen: list[ProjectEntry] = []
    seen_difficulty: set[str] = set()
    remaining = list(candidates)

    for difficulty in ("beginner", "intermediate", "advanced"):
        match = next((p for p in remaining if p.difficulty == difficulty), None)
        if match is not None:
            chosen.append(match)
            seen_difficulty.add(difficulty)
            remaining.remove(match)
        if len(chosen) == limit:
            break

    for project in remaining:
        if len(chosen) == limit:
            break
        chosen.append(project)

    chosen.sort(key=lambda p: _DIFFICULTY_RANK.get(p.difficulty, 1))
    return chosen


def _entry(project: ProjectEntry, target_role: str) -> dict:
    narrated = llm.get_llm_provider().narrate("project_why", {
        "project_title": project.title,
        "target_role": target_role,
        "difficulty": project.difficulty,
        "estimated_hours": project.estimated_hours,
        "skills_practiced": list(project.skills_practiced),
    })
    return {
        "title": project.title,
        "summary": project.summary,
        "difficulty": project.difficulty,
        "estimated_hours": project.estimated_hours,
        "stack": list(project.stack),
        "skills_practiced": list(project.skills_practiced),
        "stretch_goal": project.stretch_goal,
        "why": narrated.text,
    }


def run(*, target_role: str, limit: int = PICKS) -> dict:
    tracks = set(skill_graph.role_track_chain_names(target_role))

    with tracing.traced_step(
        "project_advisor", "suggest_projects",
        input_summary=f"role '{target_role}', tracks {sorted(tracks)}",
    ) as record:
        candidates = projects_for_tracks(tracks)
        shortlist = _balanced_shortlist(candidates, limit)
        picks = [_entry(project, target_role) for project in shortlist]

        record["output_summary"] = (
            f"{len(picks)} projects shortlisted from {len(candidates)} track-matched candidates "
            f"(difficulty spread: {', '.join(p['difficulty'] for p in picks)})"
        )
        record["confidence"] = round(len(picks) / limit, 3) if limit else 0.0

    return {
        "project_picks": picks,
        "matched_tracks": sorted(tracks),
        "candidate_count": len(candidates),
        "trace": dict(record),
    }
