from __future__ import annotations

import random
from typing import Any

from backend.utils import skill_graph, tracing

PASS_FLOOR = 0.80
PARTIAL_FLOOR = 0.40
LOG_FLOOR = 0.50
CELEBRATION_FLOOR = LOG_FLOOR
MINUTES_PER_QUESTION = 1.5
VIOLATION_AUTOSUBMIT_THRESHOLD = 5
QUESTION_COUNT = 10

_DIFFICULTY_TIME: dict[str, int] = {"Easy": 60, "Medium": 90, "Hard": 120}

_SLOT_PLAN: tuple[tuple[str, str, str], ...] = (
    ("Conceptual",    "Easy",   "angle"),
    ("Conceptual",    "Easy",   "angle"),
    ("Conceptual",    "Medium", "angle"),
    ("Conceptual",    "Medium", "angle"),
    ("Application",   "Easy",   "application"),
    ("Application",   "Medium", "application"),
    ("Application",   "Hard",   "application"),
    ("Code Analysis", "Medium", "numeric"),
    ("Code Analysis", "Hard",   "numeric"),
    ("Synthesis",     "Hard",   "synthesis"),
)


def band_for(score: float) -> str:
    if score >= PASS_FLOOR:
        return "passed"
    if score >= PARTIAL_FLOOR:
        return "partial"
    return "failed"


_BAND_HEADLINES = {
    "passed": "Cleared - the next week just unlocked.",
    "partial": "Partially there - one more revision pass and a retake will open up.",
    "failed": "Under the bar this time - a revision pass comes before the retake does.",
}


def band_headline(band: str) -> str:
    return _BAND_HEADLINES.get(band, "")


def _rng(profile_id: str, week: int, attempt_number: int, slot: int) -> random.Random:
    return random.Random(f"checkpoint:{profile_id}:{week}:{attempt_number}:{slot}")


def _build_justification(
    options: list[str],
    answer: str,
    why_correct: str,
    why_wrong_fn,
) -> dict[str, str | None]:
    letters = ("A", "B", "C", "D")
    result: dict[str, str | None] = {"whyCorrect": why_correct}
    for letter, opt in zip(letters, options):
        result[f"why{letter}IsWrong"] = None if opt == answer else why_wrong_fn(opt)
    return result


def _resource_trace_for(skill_id: str, resource: dict | None) -> str:
    info = skill_graph.node(skill_id)
    title = (resource or {}).get("title")
    res_type = (resource or {}).get("resource_type")
    difficulty = (resource or {}).get("difficulty")
    if title and res_type:
        level_tag = f" {difficulty}" if difficulty else ""
        return (
            f"This week's resource for {info['name']}: \"{title}\" is a"
            f"{level_tag} {res_type} covering {info['name']} in the {info['family']} domain."
        )
    return (
        f"Skill graph entry: {info['name']} is a {info['difficulty']}-level "
        f"{info['family']} concept."
    )


_NUMERIC_SUBTYPE_TAGS = (
    "Numerical Aptitude - Speed Distance Time",
    "Numerical Aptitude - Percentage",
    "Numerical Aptitude - Simple Interest",
    "Numerical Aptitude - Ratio and Proportion",
)

_NUMERIC_SUBTYPE_TRACES = (
    "Aptitude preparation: speed-distance-time problems appear in timed placement screens across all major company profiles.",
    "Aptitude preparation: percentage calculations are a standard component of quantitative aptitude sections.",
    "Aptitude preparation: simple interest (P x R x T / 100) is tested in quantitative aptitude and banking-pattern papers.",
    "Aptitude preparation: ratio and proportion problems appear across all placement-drive aptitude sections.",
)

_NUMERIC_ERROR_HINTS = (
    "Check the total-distance formula (train length + platform length) and the m/s-to-km/h conversion factor (3.6).",
    "Check whether you multiplied total by the percentage rate and then divided by 100 correctly.",
    "Check that you applied the formula P x R x T / 100 with the correct values for each variable.",
    "Check that you scaled by the ratio (target servings / base servings) rather than adding the difference.",
)


def _add_numeric_meta(question: dict, shape_index: int) -> None:
    idx = shape_index % 4
    question["concept_tag"] = _NUMERIC_SUBTYPE_TAGS[idx]
    question["resource_trace"] = _NUMERIC_SUBTYPE_TRACES[idx]
    hint = _NUMERIC_ERROR_HINTS[idx]
    question["justification"] = _build_justification(
        question["options"],
        question["answer"],
        question.get("explainer", ""),
        lambda opt, h=hint: f"This value does not match the formula result. {h}",
    )


def _q_speed(rng: random.Random) -> dict:
    speed = rng.choice([36, 45, 54, 60, 72, 90])
    seconds = rng.choice([10, 15, 20, 25, 30])
    total_metres = round(speed * 1000 / 3600 * seconds)
    train = rng.randint(2, 4) * 50
    platform = total_metres - train
    if platform <= 0:
        platform = total_metres + rng.randint(1, 3) * 50
        total_metres = train + platform
        speed = round(total_metres / seconds * 3.6)
    correct = f"{speed} km/h"
    options = _scatter_numeric(rng, speed, step=9, unit=" km/h")
    return {
        "prompt": (
            f"A train {train} metres long crosses a platform {platform} metres long "
            f"in {seconds} seconds. What is its speed?"
        ),
        "kind": "numerical",
        "options": options,
        "answer": correct,
        "explainer": (
            f"Total distance covered is {train} + {platform} = {total_metres} m in {seconds} s, "
            f"which is {round(total_metres / seconds, 1)} m/s - multiply by 3.6 to get {speed} km/h."
        ),
    }


def _q_percentage(rng: random.Random) -> dict:
    total = rng.choice([40, 50, 60, 80, 120, 150, 200])
    pct = rng.choice([15, 20, 25, 30, 35, 40, 45])
    correct_value = round(total * pct / 100)
    correct = f"{correct_value} students"
    options = _scatter_numeric(rng, correct_value, step=max(2, round(total * 0.05)), unit=" students")
    return {
        "prompt": (
            f"In a batch of {total} learners, {pct} percent cleared a screening round. "
            f"How many learners cleared it?"
        ),
        "kind": "numerical",
        "options": options,
        "answer": correct,
        "explainer": (
            f"{pct} percent of {total} is {total} times {pct} over 100, "
            f"which comes to {correct_value} learners."
        ),
    }


def _q_interest(rng: random.Random) -> dict:
    principal = rng.choice([2000, 4000, 5000, 8000, 10000])
    rate = rng.choice([4, 5, 6, 8, 10])
    years = rng.choice([2, 3, 4])
    correct_value = round(principal * rate * years / 100)
    correct = f"Rs {correct_value}"
    options = _scatter_numeric(rng, correct_value, step=max(50, round(correct_value * 0.12)), unit="", prefix="Rs ")
    return {
        "prompt": (
            f"What is the simple interest on Rs {principal} at {rate} percent per annum "
            f"over {years} years?"
        ),
        "kind": "numerical",
        "options": options,
        "answer": correct,
        "explainer": (
            f"Simple interest is principal times rate times time over 100: "
            f"{principal} x {rate} x {years} / 100 = {correct_value}."
        ),
    }


def _q_ratio(rng: random.Random) -> dict:
    base_servings = rng.choice([4, 5, 6, 8])
    multiplier = rng.choice([2, 3, 4])
    target_servings = base_servings * multiplier
    grams = rng.choice([100, 150, 200, 250, 300])
    correct_value = grams * multiplier
    correct = f"{correct_value} g"
    options = _scatter_numeric(rng, correct_value, step=max(10, round(grams * 0.2)), unit=" g")
    return {
        "prompt": (
            f"A recipe meant for {base_servings} people needs {grams} g of an ingredient. "
            f"How much is needed to serve {target_servings} people, keeping the same ratio?"
        ),
        "kind": "numerical",
        "options": options,
        "answer": correct,
        "explainer": (
            f"{target_servings} people is {multiplier} times {base_servings}, so the ingredient "
            f"scales the same way: {grams} x {multiplier} = {correct_value} g."
        ),
    }


_NUMERIC_SHAPES = (_q_speed, _q_percentage, _q_interest, _q_ratio)


def _scatter_numeric(
    rng: random.Random, correct_value: int, *, step: int, unit: str, prefix: str = ""
) -> list[str]:
    step = max(1, step)
    offsets = rng.sample([-3, -2, -1, 1, 2, 3], k=5)
    values: set[int] = {correct_value}
    for off in offsets:
        candidate = correct_value + step * off
        if candidate > 0:
            values.add(candidate)
        if len(values) == 4:
            break
    bump = 4
    while len(values) < 4:
        values.add(correct_value + step * bump)
        bump += 1
    ordered = list(values)[:4]
    if correct_value not in ordered:
        ordered[0] = correct_value
    rng.shuffle(ordered)
    return [f"{prefix}{v}{unit}" for v in ordered]


_CONCEPT_FRAMES = (
    "Which of these correctly describes {skill}?",
    "A teammate asks you to place {skill} in context for a standup update. Which line is accurate?",
    "Which statement about {skill} would a reviewer sign off on as correct?",
)

_RESOURCE_FRAMES = (
    "This week's pick for {skill} was \"{resource}\". Going by what that resource is actually about, "
    "which of these correctly describes {skill}?",
    "\"{resource}\" is the resource this week pointed you at for {skill}. Which statement below is the "
    "one its own description would back up?",
    "Having worked through \"{resource}\" for {skill} this week, which line would you flag as the accurate one?",
)

_LEVEL_PHRASES = {
    "beginner": "a foundational skill, usually picked up early and built on by everything that follows it",
    "intermediate": "a working skill that sits in the middle of the track, leaning on the basics and feeding the advanced topics",
    "advanced": "an advanced skill, usually tackled once the foundations underneath it are already solid",
}


def _describe(skill_id: str) -> str:
    info = skill_graph.node(skill_id)
    level_phrase = _LEVEL_PHRASES.get(info["difficulty"], "a skill placed along this track")
    return f"{info['name']} sits in the {info['family']} part of the track - {level_phrase}."


def _pick_frame(frames: tuple[str, ...], attempt_number: int) -> str:
    return frames[(attempt_number - 1) % len(frames)]


def _q_concept(
    rng: random.Random, skill_id: str, role_node_ids: list[str],
    resource: dict | None = None, attempt_number: int = 1, slot: int = 0,
) -> dict | None:
    info = skill_graph.node(skill_id)
    pool = [s for s in role_node_ids if s != skill_id]
    if len(pool) < 3:
        return None
    distractor_ids = rng.sample(pool, k=3)
    correct = _describe(skill_id)
    options = [correct] + [_describe(d) for d in distractor_ids]
    rng.shuffle(options)
    title = (resource or {}).get("title")
    if title:
        frame = _pick_frame(_RESOURCE_FRAMES, attempt_number)
        prompt = frame.format(skill=info["name"], resource=title)
    else:
        frame = _pick_frame(_CONCEPT_FRAMES, attempt_number)
        prompt = frame.format(skill=info["name"])
    explainer = (
        f"{info['name']} is a {info['difficulty']}-level topic in {info['family']} - "
        f"the other options describe different skills on this track, not this one."
    )
    justification = _build_justification(
        options, correct, explainer,
        lambda opt: (
            "This accurately describes a different skill on the track. "
            "The question names a specific concept - match each option against that concept's own definition."
        ),
    )
    return {
        "prompt": prompt,
        "kind": "conceptual",
        "options": options,
        "answer": correct,
        "explainer": explainer,
        "concept_tag": info["name"],
        "resource_trace": _resource_trace_for(skill_id, resource),
        "justification": justification,
    }


_RELATION_FRAMES_PREREQ = (
    "Before {skill} clicks, which of these is the one thing this track expects you to already have a handle on?",
    "{skill} does not stand alone on this track - which of the following is the piece it leans on?",
    "A reviewer says {skill} only makes sense once one earlier topic is solid. Which one are they pointing at?",
)

_RELATION_FRAMES_UNLOCK = (
    "Once {skill} is solid, which of these is the one thing this track opens up right behind it?",
    "{skill} is not the end of this thread - which of the following is the topic it directly leads into?",
    "A reviewer says getting {skill} right is what clears the way for one specific topic next. Which one?",
)


def _q_relation(
    rng: random.Random, skill_id: str, role_node_ids: list[str],
    resource: dict | None = None, attempt_number: int = 1, slot: int = 0,
) -> dict | None:
    info = skill_graph.node(skill_id)
    track = set(role_node_ids)
    prereqs = [s for s in skill_graph.prerequisites(skill_id) if s in track]
    successors = [s for s in skill_graph.unlocks(skill_id) if s in track]
    use_unlocks = bool(successors) and (not prereqs or attempt_number % 2 == 1)
    related = successors if use_unlocks else prereqs
    if not related:
        return None
    target_id = related[(attempt_number - 1 + slot) % len(related)]
    target = skill_graph.node(target_id)
    correct = target["name"]
    pool = [s for s in role_node_ids if s != skill_id and s not in related]
    if len(pool) < 3:
        return None
    distractor_ids = rng.sample(pool, k=3)
    options = [correct] + [skill_graph.node(d)["name"] for d in distractor_ids]
    rng.shuffle(options)
    frame = _pick_frame(_RELATION_FRAMES_UNLOCK if use_unlocks else _RELATION_FRAMES_PREREQ, attempt_number)
    prompt = frame.format(skill=info["name"])
    relation_word = "leads into" if use_unlocks else "leans on"
    explainer = (
        f"On this track, {info['name']} {relation_word} {correct} - the other names sit "
        f"elsewhere on the map and are not the link this question is naming."
    )
    justification = _build_justification(
        options, correct, explainer,
        lambda opt: (
            f"{opt} is a real skill on this track but it is not the one directly "
            f"{'leading out of' if use_unlocks else 'required before'} {info['name']}. "
            f"Check the track graph for the direct connection."
        ),
    )
    return {
        "prompt": prompt,
        "kind": "conceptual",
        "options": options,
        "answer": correct,
        "explainer": explainer,
        "concept_tag": f"{info['name']} - Track Relationship",
        "resource_trace": (
            f"Skill graph: {info['name']} {relation_word} {correct} on this track."
        ),
        "justification": justification,
    }


_RESOURCE_TYPE_PHRASES = {
    "article": "a written explainer you read at your own pace",
    "course": "a structured, multi-part course",
    "doc": "official reference documentation",
    "problem": "a hands-on problem set you work through rather than read",
    "video": "a watch-along walkthrough",
    "book": "a book-length treatment",
}

_DIFFICULTY_PHRASES = {
    "beginner": "pitched at someone just starting out with it",
    "intermediate": "pitched at someone past the basics, building toward real fluency",
    "advanced": "pitched at someone already comfortable, pushing into the harder corners",
}

_RESOURCE_TYPES = ("article", "course", "doc", "problem", "video", "book")
_DIFFICULTIES = ("beginner", "intermediate", "advanced")

_RESOURCE_FOCUS_FRAMES = (
    "This week's pick for {skill} was \"{resource}\". Which line below correctly names what that "
    "resource actually is - its format and the level it is pitched at?",
    "Think back to \"{resource}\", the resource lined up for {skill} this week. Which of these "
    "actually matches it, rather than just sounding like it could?",
    "Of the four descriptions below, which one is genuinely \"{resource}\" - this week's {skill} "
    "pick - and not a plausible-sounding stand-in for it?",
)


def _resource_phrase(resource_type: str, difficulty: str, source: str | None) -> str:
    type_phrase = _RESOURCE_TYPE_PHRASES.get(resource_type, f"a {resource_type} resource")
    level_phrase = _DIFFICULTY_PHRASES.get(difficulty, f"pitched at {difficulty} level")
    tail = f", from {source}" if source else ""
    return f"{type_phrase[0].upper()}{type_phrase[1:]}, {level_phrase}{tail}."


def _q_resource_focus(
    rng: random.Random, skill_id: str, role_node_ids: list[str],
    resource: dict | None = None, attempt_number: int = 1, slot: int = 0,
) -> dict | None:
    if not resource:
        return None
    title = resource.get("title")
    resource_type = resource.get("resource_type")
    difficulty = resource.get("difficulty")
    if not (title and resource_type and difficulty):
        return None
    info = skill_graph.node(skill_id)
    source = resource.get("source")
    correct = _resource_phrase(resource_type, difficulty, source)
    wrong_types = [t for t in _RESOURCE_TYPES if t != resource_type]
    if len(wrong_types) < 2:
        return None
    combos: set[tuple[str, str]] = set()
    guard = 0
    while len(combos) < 3 and guard < 30:
        guard += 1
        candidate = (rng.choice(wrong_types), rng.choice(_DIFFICULTIES))
        if candidate != (resource_type, difficulty):
            combos.add(candidate)
    if len(combos) < 3:
        return None
    options = [correct] + [_resource_phrase(t, d, source) for t, d in combos]
    rng.shuffle(options)
    frame = _pick_frame(_RESOURCE_FOCUS_FRAMES, attempt_number)
    prompt = frame.format(skill=info["name"], resource=title)
    explainer = (
        f"\"{title}\" is the resource this week actually pointed you at for {info['name']} - "
        f"its real format and level are what the right answer names, not a guess dressed up to sound right."
    )
    justification = _build_justification(
        options, correct, explainer,
        lambda opt: (
            "This describes the resource with the wrong format or difficulty level. "
            "The correct option matches what this week's actual resource row records."
        ),
    )
    return {
        "prompt": prompt,
        "kind": "conceptual",
        "options": options,
        "answer": correct,
        "explainer": explainer,
        "concept_tag": f"{info['name']} - Resource Recognition",
        "resource_trace": (
            f"Resource row: \"{title}\" is a {resource_type} at {difficulty} level"
            + (f", from {source}" if source else "") + "."
        ),
        "justification": justification,
    }


_ANGLE_BUILDERS = (_q_concept, _q_relation, _q_resource_focus)


_APP_FRAMES = (
    "A developer working on a {family} task needs to apply the right concept at the {level} level. "
    "Which of the following is the skill this scenario calls for?",
    "A placement interviewer describes a {family} scenario at the {level} level and asks you to name "
    "the concept you would use. Which answer is correct?",
    "A code review flags that the wrong concept was applied to a {family} problem at the {level} level. "
    "Which of these would have been the right choice?",
)


def _q_application(
    rng: random.Random, skill_id: str, role_node_ids: list[str],
    resource: dict | None = None, attempt_number: int = 1, slot: int = 0,
) -> dict | None:
    info = skill_graph.node(skill_id)
    pool = [s for s in role_node_ids if s != skill_id]
    if len(pool) < 3:
        return None
    distractor_ids = rng.sample(pool, k=3)
    distractor_infos = [skill_graph.node(d) for d in distractor_ids]

    correct = (
        f"{info['name']} - the {info['difficulty']}-level {info['family']} concept "
        f"this scenario specifically requires."
    )
    options = [correct] + [
        f"{d['name']} - a {d['difficulty']}-level {d['family']} concept."
        for d in distractor_infos
    ]
    rng.shuffle(options)

    frame = _APP_FRAMES[(attempt_number - 1 + slot) % len(_APP_FRAMES)]
    prompt = frame.format(family=info["family"], level=info["difficulty"])
    explainer = (
        f"{info['name']} is the {info['difficulty']}-level {info['family']} concept this scenario "
        f"is built around. The other options name real skills but address different levels or domains."
    )
    why_correct = (
        f"{info['name']} is defined on this track as a {info['difficulty']}-level {info['family']} "
        f"skill - the scenario's constraints (domain and level) point directly at it."
    )
    justification = _build_justification(
        options, correct, why_correct,
        lambda opt: (
            "This names a real skill on the track but at the wrong difficulty level or in the wrong "
            "domain for the scenario described - it would not be the expected choice here."
        ),
    )
    return {
        "prompt": prompt,
        "kind": "application",
        "options": options,
        "answer": correct,
        "explainer": explainer,
        "concept_tag": f"{info['name']} - Application",
        "resource_trace": _resource_trace_for(skill_id, resource),
        "justification": justification,
        "focus_skill": skill_id,
    }


def _q_synthesis(
    rng: random.Random, skill_id1: str, skill_id2: str, role_node_ids: list[str],
    attempt_number: int = 1,
) -> dict | None:
    info1 = skill_graph.node(skill_id1)
    info2 = skill_graph.node(skill_id2)
    if not info1 or not info2:
        return None

    correct = (
        f"Both are on this track: {info1['name']} is a {info1['difficulty']}-level "
        f"{info1['family']} skill and {info2['name']} is a {info2['difficulty']}-level "
        f"{info2['family']} skill - they address different layers of the same roadmap."
    )
    wrong1 = (
        f"{info1['name']} and {info2['name']} are both {info1['difficulty']}-level - "
        f"they sit at the same point in the difficulty curve."
    )
    wrong2 = (
        f"{info1['name']} is a strict prerequisite for {info2['name']} - the second "
        f"cannot begin until the first is fully mastered, with no exceptions."
    )
    wrong3 = (
        f"Only {info1['name']} is part of this week's scope - {info2['name']} belongs "
        f"to a separate, unrelated track."
    )

    options = [correct, wrong1, wrong2, wrong3]
    rng.shuffle(options)

    prompt = (
        f"This week covered both {info1['name']} and {info2['name']}. "
        f"Which statement most accurately describes how these two skills fit into the same roadmap?"
    )
    explainer = (
        f"{info1['name']} and {info2['name']} both appear on this roadmap at different levels and "
        f"in different domains. The correct option names both accurately. The other options introduce "
        f"errors about level, domain, or strict prerequisite ordering."
    )
    why_correct = (
        f"The skill graph places {info1['name']} at {info1['difficulty']}-level in {info1['family']} "
        f"and {info2['name']} at {info2['difficulty']}-level in {info2['family']}. "
        f"The correct option names both accurately without overstating any strict dependency."
    )
    justification = _build_justification(
        options, correct, why_correct,
        lambda opt: (
            "This option misrepresents the difficulty level, domain, or dependency relationship "
            "between the two skills. Check the skill track definitions to see where each one sits."
        ),
    )
    return {
        "prompt": prompt,
        "kind": "synthesis",
        "options": options,
        "answer": correct,
        "explainer": explainer,
        "concept_tag": f"{info1['name']} + {info2['name']} - Synthesis",
        "resource_trace": (
            f"Skill graph: {info1['name']} ({info1['difficulty']}, {info1['family']}) and "
            f"{info2['name']} ({info2['difficulty']}, {info2['family']}) both appear in this "
            f"week's scope."
        ),
        "justification": justification,
        "focus_skill": skill_id1,
    }


def _milestone_skills(active_milestones: list[dict[str, Any]], week: int) -> list[str]:
    for milestone in active_milestones:
        if milestone.get("week") == week and not milestone.get("is_blackout"):
            return list(milestone.get("skill_ids", []))
    return []


def generate_questions(
    *,
    profile_id: str,
    target_role: str,
    week: int,
    attempt_number: int,
    skill_ids: list[str],
    count: int = QUESTION_COUNT,
    resource_briefs: dict[str, dict] | None = None,
    checkpoint_history: list[dict] | None = None,
) -> list[dict]:
    role_node_ids = skill_graph.role_node_ids(target_role) or skill_ids
    pool = list(skill_ids or role_node_ids[:6])
    if len(pool) < 6:
        supplemental = [s for s in role_node_ids if s not in set(pool)]
        pool = pool + supplemental[: max(0, 6 - len(pool))]
    briefs = resource_briefs or {}
    pool_len = max(1, len(pool))
    used_combos: set[tuple[str, str]] = set()
    for past_session in (checkpoint_history or []):
        for past_q in past_session.get("questionsAsked", []):
            tag = past_q.get("conceptTag") or past_q.get("concept_tag") or ""
            qtype = past_q.get("questionType") or past_q.get("question_type") or ""
            if tag and qtype:
                used_combos.add((tag, qtype))

    questions: list[dict] = []
    seen_signatures: set[tuple[str, str]] = set()
    slot_plan = _SLOT_PLAN[:count]
    angle_count = len(_ANGLE_BUILDERS)

    for slot, (q_type, difficulty, builder_tag) in enumerate(slot_plan):
        rng = _rng(profile_id, week, attempt_number, slot)
        time_limit = _DIFFICULTY_TIME[difficulty]
        question: dict | None = None

        if builder_tag == "angle":
            pool_index = (slot + attempt_number - 1) % pool_len
            angle_index = (slot + week + attempt_number - 1) % angle_count

            for nudge in range(angle_count * pool_len):
                skill_offset = nudge // angle_count
                candidate_skill = pool[(pool_index + skill_offset) % pool_len]
                candidate_angle = (angle_index + nudge) % angle_count
                candidate = _ANGLE_BUILDERS[candidate_angle](
                    rng, candidate_skill, role_node_ids, briefs.get(candidate_skill),
                    attempt_number=attempt_number, slot=slot,
                )
                if not candidate:
                    continue
                sig = (candidate_skill, candidate["prompt"])
                if sig in seen_signatures:
                    continue
                tag = candidate.get("concept_tag") or skill_graph.node(candidate_skill).get("name", candidate_skill)
                if (tag, q_type) in used_combos and nudge < angle_count * pool_len - 1:
                    continue
                if "concept_tag" not in candidate:
                    candidate["concept_tag"] = tag
                if "resource_trace" not in candidate:
                    candidate["resource_trace"] = _resource_trace_for(candidate_skill, briefs.get(candidate_skill))
                if "justification" not in candidate:
                    candidate["justification"] = _build_justification(
                        candidate["options"], candidate["answer"],
                        candidate.get("explainer", ""),
                        lambda opt: (
                            "This option describes a different skill on the track. "
                            "Check each option against the specific concept this question names."
                        ),
                    )
                candidate["focus_skill"] = candidate_skill
                seen_signatures.add(sig)
                question = candidate
                break

        elif builder_tag == "application":
            pool_index = (slot + attempt_number - 1) % pool_len
            for nudge in range(pool_len):
                candidate_skill = pool[(pool_index + nudge) % pool_len]
                candidate = _q_application(
                    rng, candidate_skill, role_node_ids, briefs.get(candidate_skill),
                    attempt_number=attempt_number, slot=slot,
                )
                if not candidate:
                    continue
                tag = candidate["concept_tag"]
                if (tag, q_type) in used_combos and nudge < pool_len - 1:
                    continue
                question = candidate
                break
            if not question:
                shape_index = (slot + week + attempt_number - 1) % len(_NUMERIC_SHAPES)
                question = _NUMERIC_SHAPES[shape_index](rng)
                _add_numeric_meta(question, shape_index)

        elif builder_tag == "numeric":
            shape_index = (slot + week + attempt_number - 1) % len(_NUMERIC_SHAPES)
            question = _NUMERIC_SHAPES[shape_index](rng)
            _add_numeric_meta(question, shape_index)

        elif builder_tag == "synthesis":
            if pool_len >= 2:
                skill_id1 = pool[(slot + attempt_number - 1) % pool_len]
                skill_id2 = pool[(slot + attempt_number) % pool_len]
                # Ensure the two slots are different skills when possible
                if skill_id1 == skill_id2 and pool_len > 1:
                    skill_id2 = pool[(slot + attempt_number + 1) % pool_len]
                question = _q_synthesis(
                    rng, skill_id1, skill_id2, role_node_ids, attempt_number=attempt_number,
                )
            if not question:
                shape_index = (slot + week + attempt_number - 1) % len(_NUMERIC_SHAPES)
                question = _NUMERIC_SHAPES[shape_index](rng)
                _add_numeric_meta(question, shape_index)

        if question:
            question["question_type"] = q_type
            question["difficulty"] = difficulty
            question["time_limit_seconds"] = time_limit
            if "concept_tag" not in question:
                question["concept_tag"] = question.get("focus_skill", "General")
            if "resource_trace" not in question:
                fs = question.get("focus_skill", "")
                question["resource_trace"] = (
                    _resource_trace_for(fs, briefs.get(fs)) if fs else "Skill track resource."
                )
            if "justification" not in question:
                question["justification"] = _build_justification(
                    question["options"], question["answer"],
                    question.get("explainer", ""),
                    lambda opt: "This option is incorrect. Review the concept explanation provided.",
                )
            questions.append(question)

    for index, question in enumerate(questions, start=1):
        question["id"] = f"WK{week}-Q{index:02d}"

    return questions


def grade_attempt(questions: list[dict], answers: list[dict]) -> dict:
    by_id = {q["id"]: q for q in questions}
    scored = []
    correct_count = 0
    weak_concepts: list[dict] = []
    failed_concepts: list[dict] = []

    for entry in answers:
        question = by_id.get(entry["question_id"])
        if not question:
            continue
        keyed = (question.get("answer") or "").strip()
        chosen = (entry.get("choice") or "").strip()
        is_correct = chosen.casefold() == keyed.casefold()
        if is_correct:
            correct_count += 1
        else:
            concept_tag = question.get("concept_tag", "")
            if concept_tag:
                concept_entry = {
                    "conceptTag": concept_tag,
                    "resourceId": question.get("focus_skill", ""),
                    "questionId": entry["question_id"],
                    "questionType": question.get("question_type", ""),
                    "difficulty": question.get("difficulty", ""),
                    "recommendedReview": (
                        f"Revisit the {concept_tag} section of this week's resources."
                    ),
                }
                failed_concepts.append(concept_entry)
                weak_concepts.append(concept_entry)

        scored.append({
            "question_id": entry["question_id"],
            "prompt": question["prompt"],
            "chosen": chosen,
            "correct_option": keyed,
            "is_correct": is_correct,
            "explainer": question.get("explainer", ""),
            "options": question.get("options", []),
            "justification": question.get("justification"),
            "concept_tag": question.get("concept_tag"),
            "question_type": question.get("question_type"),
            "difficulty": question.get("difficulty"),
        })

    total = len(questions) or 1
    score = round(correct_count / total, 3)
    band = band_for(score)
    return {
        "score": score,
        "band": band,
        "correct_count": correct_count,
        "total": total,
        "scored": scored,
        "weak_concepts": weak_concepts,
        "failed_concepts": failed_concepts,
    }


def feedback_for(band: str, score: float, week: int, correct_count: int, total: int) -> str:
    headline = band_headline(band)
    return (
        f"Week {week} checkpoint: {correct_count} of {total} correct, "
        f"{round(score * 100)} percent overall. {headline}"
    )


_BRIEF_FIELDS = ("title", "resource_type", "difficulty", "source")


def _resource_briefs(resource_picks: dict[str, list[dict]] | None, skill_ids: list[str]) -> dict[str, dict]:
    if not resource_picks:
        return {}
    briefs: dict[str, dict] = {}
    for skill_id in skill_ids:
        picks = resource_picks.get(skill_id) or []
        if not picks or not picks[0].get("title"):
            continue
        top = picks[0]
        briefs[skill_id] = {field: top.get(field) for field in _BRIEF_FIELDS}
    return briefs


def run_generation(
    *,
    profile_id: str,
    target_role: str,
    week: int,
    attempt_number: int,
    active_milestones: list[dict[str, Any]],
    time_limit_minutes: int | None = None,
    resource_picks: dict[str, list[dict]] | None = None,
    checkpoint_history: list[dict] | None = None,
) -> dict:
    with tracing.traced_step(
        "weekly_checkpoint",
        "generate_questions",
        input_summary=f"week {week}, attempt {attempt_number} for {target_role}",
    ) as record:
        skill_ids = _milestone_skills(active_milestones, week)
        briefs = _resource_briefs(resource_picks, skill_ids)
        questions = generate_questions(
            profile_id=profile_id,
            target_role=target_role,
            week=week,
            attempt_number=attempt_number,
            skill_ids=skill_ids,
            resource_briefs=briefs,
            checkpoint_history=checkpoint_history,
        )
        limit = time_limit_minutes or max(8, round(len(questions) * MINUTES_PER_QUESTION))
        grounded = sum(1 for q in questions if q.get("focus_skill") in briefs)
        record["output_summary"] = (
            f"{len(questions)} MCQs built for week {week}, attempt {attempt_number}"
            + (f", {grounded} resource-grounded" if grounded else "")
        )
        record["confidence"] = 0.9 if skill_ids else 0.6

    return {"questions": questions, "time_limit_minutes": limit, "trace": dict(record)}


def run_grading(
    *,
    profile_id: str,
    week: int,
    attempt_number: int,
    questions: list[dict],
    answers: list[dict],
) -> dict:
    with tracing.traced_step(
        "weekly_checkpoint",
        "grade_attempt",
        input_summary=f"week {week}, attempt {attempt_number}, {len(answers)} answers",
    ) as record:
        result = grade_attempt(questions, answers)
        feedback = feedback_for(
            result["band"], result["score"], week, result["correct_count"], result["total"]
        )
        record["output_summary"] = (
            f"{result['correct_count']}/{result['total']} correct -> {result['band']}"
        )
        record["confidence"] = result["score"]

    return {
        **result,
        "feedback": feedback,
        "celebration_trigger": result["score"] >= CELEBRATION_FLOOR,
        "trace": dict(record),
    }
