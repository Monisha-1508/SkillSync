from __future__ import annotations

import random
from typing import Any

from backend.agents.weekly_test import (
    LOG_FLOOR,
    _NUMERIC_SHAPES,
    _describe,
    _q_concept,
    _q_relation,
    grade_attempt,
)
from backend.utils import skill_graph, tracing

RECOVERY_TRIGGER = 3
RECOVERY_FLOOR = LOG_FLOOR
CRITICAL_GAP_CEILING = 30
WEAK_GAP_CEILING = 49
CRITICAL_WEIGHT = 1.5
BASE_WEIGHT = 1.0
MICRO_EVAL_PASS_FLOOR = 0.50
APTITUDE_TOPIC = "Quantitative aptitude (speed, percentages, interest, ratios)"


def eligible_for_recovery(attempts: list[Any]) -> bool:
    submitted = sorted(
        (a for a in attempts if a.status == "submitted" and a.score is not None),
        key=lambda a: a.attempt_number,
    )
    if len(submitted) < RECOVERY_TRIGGER:
        return False
    last_three = submitted[-RECOVERY_TRIGGER:]
    numbers = [a.attempt_number for a in last_three]
    consecutive = all(b - a == 1 for a, b in zip(numbers, numbers[1:]))
    return consecutive and all(a.score < RECOVERY_FLOOR for a in last_three)


def failing_streak(attempts: list[Any]) -> list[Any]:
    submitted = sorted(
        (a for a in attempts if a.status == "submitted" and a.score is not None),
        key=lambda a: a.attempt_number,
    )
    return submitted[-RECOVERY_TRIGGER:]


def retake_blocked_by_recovery(attempts: list[Any], recovery_row: Any | None) -> bool:
    if not eligible_for_recovery(attempts):
        return False
    if recovery_row is None or not recovery_row.passed:
        return True
    streak = failing_streak(attempts)
    newest = max((a.submitted_at for a in streak if a.submitted_at), default=None)
    return not (newest is None or newest <= recovery_row.created_at)



def _topic_for(question: dict[str, Any]) -> str:
    skill_id = question.get("focus_skill")
    if skill_id:
        try:
            return skill_graph.node(skill_id)["name"]
        except KeyError:
            pass
    return APTITUDE_TOPIC


def _status_for(kgs: float) -> str | None:
    if kgs <= CRITICAL_GAP_CEILING:
        return "[CRITICAL GAP]"
    if kgs <= WEAK_GAP_CEILING:
        return "[WEAK]"
    return None


def _summary_for(week: int, weak: list[dict[str, Any]]) -> str:
    if not weak:
        return (
            f"Three sittings of week {week}'s checkpoint have now landed under the line without any single "
            "topic standing out as the cause - the misses read as spread thin across the paper rather than "
            "parked on one spot. The plan below still starts somewhere concrete instead of asking for a "
            "fourth blind run at the same questions."
        )
    names = [entry["topicName"] for entry in weak]
    if len(names) == 1:
        topic_phrase = f"\"{names[0]}\""
    elif len(names) == 2:
        topic_phrase = f"\"{names[0]}\" and \"{names[1]}\""
    else:
        topic_phrase = ", ".join(f"\"{name}\"" for name in names[:-1]) + f", and \"{names[-1]}\""
    critical = [entry for entry in weak if entry["status"] == "[CRITICAL GAP]"]
    if critical:
        critical_note = (
            f" {'One of them sits' if len(critical) == 1 else f'{len(critical)} of them sit'} low enough "
            "to flag as a critical gap rather than just a weak spot, which is what moves it to the front "
            "of the plan and gives it more weight in the check at the end."
        )
    else:
        critical_note = ""
    return (
        f"Across the last three sittings of week {week}'s checkpoint, the trouble kept landing on the same "
        f"ground rather than spreading evenly - {topic_phrase}{' is' if len(names) == 1 else ' are'} where "
        f"eighteen questions' worth of evidence point.{critical_note} The plan below works through each of "
        "those, worst first, then hands back a short check that has to clear its own line before the next "
        "checkpoint attempt opens back up."
    )


def diagnose(attempts: list[Any], *, week: int) -> tuple[dict[str, Any], dict[str, str | None]]:
    ordered = sorted(attempts, key=lambda a: a.attempt_number)[-RECOVERY_TRIGGER:]
    tally: dict[str, dict[str, int]] = {}
    topic_skill_ids: dict[str, str | None] = {}

    for attempt in ordered:
        questions = attempt.questions or []
        topic_by_question_id: dict[str, str] = {}
        for question in questions:
            topic = _topic_for(question)
            topic_by_question_id[question.get("id")] = topic
            topic_skill_ids.setdefault(topic, question.get("focus_skill"))
        replay = grade_attempt(questions, attempt.answers or [])
        for entry in replay["scored"]:
            topic = topic_by_question_id.get(entry["question_id"], APTITUDE_TOPIC)
            bucket = tally.setdefault(topic, {"correct": 0, "total": 0})
            bucket["total"] += 1
            if entry["is_correct"]:
                bucket["correct"] += 1

    ranked: list[dict[str, Any]] = []
    for topic, counts in tally.items():
        total = counts["total"] or 1
        kgs = round(counts["correct"] / total * 100, 1)
        ranked.append({"topicName": topic, "knowledgeGapScore": kgs, "status": _status_for(kgs)})
    ranked.sort(key=lambda entry: (entry["knowledgeGapScore"], entry["topicName"]))

    weak = [entry for entry in ranked if entry["status"]]
    if not weak and ranked:
        weak = [{**ranked[0], "status": "[WEAK]"}]

    for rank, entry in enumerate(weak, start=1):
        entry["rank"] = rank

    weakness_report = {
        "summary": _summary_for(week, weak),
        "passingThreshold": (
            f"{round(MICRO_EVAL_PASS_FLOOR * 100)} percent, weighted, averaged across the short check below"
        ),
        "topics": [
            {
                "rank": entry["rank"],
                "topicName": entry["topicName"],
                "knowledgeGapScore": entry["knowledgeGapScore"],
                "status": entry["status"],
            }
            for entry in weak
        ],
    }
    selected_skill_ids = {entry["topicName"]: topic_skill_ids.get(entry["topicName"]) for entry in weak}
    return weakness_report, selected_skill_ids


_ANALOGY_BANK = (
    "Treat {topic} like a single junction on a route driven often - skip learning that one turn properly "
    "and the rest of the route stops making sense, however well every other turn is known.",
    "Picture {topic} as one ingredient in a recipe that only tastes right when it is measured correctly - "
    "the rest of the dish can be done perfectly and the result still comes out wrong.",
    "Think of {topic} as a page in a manual that every later page quietly assumes was already read - skim "
    "it once and the pages after it start to read like they are missing a step.",
    "{topic} behaves like a single muscle in a movement built around it - the form can look right "
    "everywhere else, and the whole thing still gives way under that one weak point.",
    "{topic} works like a tool in a kit that does one job and no other - reach for it to do a "
    "neighbouring tool's job and the result looks close enough to pass at a glance, and wrong up close.",
)


def _analogy_for(topic_name: str, rank: int) -> str:
    return _ANALOGY_BANK[(rank - 1) % len(_ANALOGY_BANK)].format(topic=topic_name)


def _concept_for(topic_name: str, skill_id: str | None) -> str:
    if skill_id:
        return _describe(skill_id)
    return (
        f"{topic_name} is the timed numerical-reasoning thread running through every sitting - speed, "
        "distance and time, percentages, simple interest, ratios - each one a short calculation with "
        "exactly one correct value and three numbers placed close enough to it to catch a rushed read."
    )


def _contrast_for(topic_name: str, skill_id: str | None, role_node_ids: list[str]) -> str:
    if not skill_id:
        return (
            f"On {topic_name}, the wrong option chosen is rarely the result of a wrong method - it is "
            "almost always the right method aimed at the wrong quantity, because the question's wording "
            "buried which number it was actually asking for. The fix is reading for that one number first, "
            "and only then reaching for the calculation."
        )
    info = skill_graph.node(skill_id)
    track = set(role_node_ids)
    prereqs = [s for s in skill_graph.prerequisites(skill_id) if s in track]
    if prereqs:
        related = skill_graph.node(prereqs[0])
        return (
            f"{info['name']} keeps getting answered as though it were {related['name']} - the two sit "
            f"right next to each other on this track, but {related['name']} is the groundwork underneath "
            f"it, and {info['name']} is the step built on top. Mixing the two up, far more than a flat "
            f"lack of effort, is the most common way a question naming {info['name']} goes wrong."
        )
    successors = [s for s in skill_graph.unlocks(skill_id) if s in track]
    if successors:
        related = skill_graph.node(successors[0])
        return (
            f"{info['name']} is easy to answer as though it already covers {related['name']} - it does "
            f"not; {related['name']} is what {info['name']} leads into, not what it includes, and folding "
            f"the two together is what tends to turn a question about one of them into a wrong answer "
            f"about the other."
        )
    return (
        f"{info['name']} tends to go wrong less from not knowing the topic and more from reaching for a "
        f"neighbouring idea on this track that sounds close enough to fit. The fix is naming, in plain "
        f"words, exactly what {info['name']} covers - and just as importantly, what it does not."
    )


def _lesson_for(topic_name: str, skill_id: str | None, role_node_ids: list[str], status: str, rank: int) -> str:
    weight_line = (
        "This one is flagged as a critical gap, so it carries one and a half times the usual weight in the "
        "check below - getting it solid is worth more there, on purpose."
        if status == "[CRITICAL GAP]" else
        "This one reads as a weak spot rather than a critical one, but closing it now is still what keeps "
        "it from hardening into one."
    )
    return (
        f"Concept - {_concept_for(topic_name, skill_id)} "
        f"Contrast - {_contrast_for(topic_name, skill_id, role_node_ids)} "
        f"Analogy - {_analogy_for(topic_name, rank)} "
        f"{weight_line}"
    )


def build_remediation(
    topics: list[dict[str, Any]], topic_skill_ids: dict[str, str | None], role_node_ids: list[str],
) -> list[dict[str, Any]]:
    return [
        {
            "topicName": entry["topicName"],
            "priority": entry["rank"],
            "biteSizedLesson": _lesson_for(
                entry["topicName"], topic_skill_ids.get(entry["topicName"]), role_node_ids, entry["status"], entry["rank"],
            ),
        }
        for entry in topics
    ]


_DIFFICULTY_LABELS = {
    "conceptual": "conceptual",
    "applied": "applied-diagnosis",
    "synthesis": "synthesis-application",
}
_RULE_OF_THREE = ("conceptual", "applied", "synthesis")

_DIAGNOSIS_FRAMES = (
    "A learner's attempts at {skill} keep going wrong in the same place, and a mentor traces the actual "
    "fault back to one earlier topic not being solid yet. Which one are they pointing at?",
    "Something about how {skill} gets used keeps tripping this learner up, and the root cause sits one "
    "step back on the track rather than inside {skill} itself. Which topic is that root cause sitting in?",
    "Working out why {skill} will not land for this learner, a reviewer names one specific topic "
    "underneath it as the real issue. Which of these is it?",
)

_SYNTHESIS_FRAMES = (
    "Once {skill} is genuinely solid, which of these is the one thing it directly opens up next on this track?",
    "Putting {skill} to use well is what clears the way for one specific next step here. Which of these is that step?",
    "A learner who has {skill} solid is asked what they can now take on that they could not before. Which "
    "of these is the honest answer?",
)


def _q_diagnosis(rng: random.Random, skill_id: str, role_node_ids: list[str]) -> dict | None:
    info = skill_graph.node(skill_id)
    track = set(role_node_ids)
    prereqs = [s for s in skill_graph.prerequisites(skill_id) if s in track]
    if not prereqs:
        return None
    target_id = prereqs[0] if len(prereqs) == 1 else rng.choice(prereqs)
    correct = skill_graph.node(target_id)["name"]
    pool = [s for s in role_node_ids if s != skill_id and s not in prereqs]
    if len(pool) < 3:
        return None
    distractor_ids = rng.sample(pool, k=3)
    options = [correct] + [skill_graph.node(d)["name"] for d in distractor_ids]
    rng.shuffle(options)
    return {
        "prompt": rng.choice(_DIAGNOSIS_FRAMES).format(skill=info["name"]),
        "options": options,
        "answer": correct,
        "explainer": (
            f"{info['name']} leans directly on {correct} - a shaky grip there is exactly the kind of root "
            f"cause that keeps resurfacing as a recurring mistake in {info['name']} itself, which is what "
            "makes it the one worth checking first."
        ),
    }


def _q_synthesis(rng: random.Random, skill_id: str, role_node_ids: list[str]) -> dict | None:
    info = skill_graph.node(skill_id)
    track = set(role_node_ids)
    successors = [s for s in skill_graph.unlocks(skill_id) if s in track]
    if not successors:
        return None
    target_id = successors[0] if len(successors) == 1 else rng.choice(successors)
    correct = skill_graph.node(target_id)["name"]
    pool = [s for s in role_node_ids if s != skill_id and s not in successors]
    if len(pool) < 3:
        return None
    distractor_ids = rng.sample(pool, k=3)
    options = [correct] + [skill_graph.node(d)["name"] for d in distractor_ids]
    rng.shuffle(options)
    return {
        "prompt": rng.choice(_SYNTHESIS_FRAMES).format(skill=info["name"]),
        "options": options,
        "answer": correct,
        "explainer": (
            f"{correct} is what this track opens up right behind {info['name']} - putting {info['name']} "
            f"to genuine use is what makes {correct} reachable, and that connection is exactly what this "
            "question is checking for."
        ),
    }


def _aptitude_question(rng: random.Random, slot_index: int) -> dict:
    shape = _NUMERIC_SHAPES[slot_index % len(_NUMERIC_SHAPES)]
    question = shape(rng)
    question.pop("kind", None)
    return question


def _topic_questions(rng: random.Random, topic_name: str, skill_id: str | None, role_node_ids: list[str]) -> list[dict]:
    if skill_id:
        builders = {
            "conceptual": lambda: _q_concept(rng, skill_id, role_node_ids),
            "applied": lambda: _q_diagnosis(rng, skill_id, role_node_ids)
            or _q_concept(rng, skill_id, role_node_ids),
            "synthesis": lambda: _q_synthesis(rng, skill_id, role_node_ids)
            or _q_relation(rng, skill_id, role_node_ids)
            or _q_concept(rng, skill_id, role_node_ids),
        }
    else:
        builders = {
            kind: (lambda index=index: _aptitude_question(rng, index))
            for index, kind in enumerate(_RULE_OF_THREE)
        }

    questions = []
    for kind in _RULE_OF_THREE:
        question = builders[kind]()
        if not question:
            continue
        question["topic"] = topic_name
        question["difficulty"] = _DIFFICULTY_LABELS[kind]
        questions.append(question)
    return questions


def generate_micro_eval(
    *, profile_id: str, week: int, cycle: int, topics: list[dict[str, Any]],
    topic_skill_ids: dict[str, str | None], role_node_ids: list[str],
) -> list[dict]:
    questions: list[dict] = []
    for slot, entry in enumerate(topics):
        topic_name = entry["topicName"]
        skill_id = topic_skill_ids.get(topic_name)
        rng = random.Random(f"recovery:{profile_id}:{week}:{cycle}:{slot}")
        weight = CRITICAL_WEIGHT if entry["status"] == "[CRITICAL GAP]" else BASE_WEIGHT
        for question in _topic_questions(rng, topic_name, skill_id, role_node_ids):
            question["weight"] = weight
            questions.append(question)
    for index, question in enumerate(questions, start=1):
        question["id"] = f"recovery-w{week}c{cycle}q{index}"
    return questions


def pass_criteria_text() -> str:
    return (
        f"Average a weighted score of {round(MICRO_EVAL_PASS_FLOOR * 100)} percent or higher across every "
        "question below to reopen the next checkpoint attempt."
    )


def weighting_note_text() -> str:
    return (
        f"Questions tied to a topic flagged [CRITICAL GAP] count {CRITICAL_WEIGHT} times as much toward "
        "that average as the rest - they carry more weight here on purpose, because they are where the "
        "last three sittings showed the steepest drop, and clearing them is what matters most before "
        "going back to the full checkpoint."
    )


def grade_micro_eval(questions: list[dict], answers: list[dict]) -> dict:
    by_id = {q["id"]: q for q in questions}
    scored = []
    earned = 0.0
    total_weight = 0.0
    for entry in answers:
        question = by_id.get(entry.get("question_id"))
        if not question:
            continue
        weight = question.get("weight", BASE_WEIGHT)
        keyed = (question.get("answer") or "").strip()
        chosen = (entry.get("choice") or "").strip()
        is_correct = chosen.casefold() == keyed.casefold()
        total_weight += weight
        if is_correct:
            earned += weight
        scored.append({
            "question_id": entry.get("question_id"),
            "topic": question.get("topic", ""),
            "prompt": question["prompt"],
            "chosen": chosen,
            "correct_option": keyed,
            "is_correct": is_correct,
            "weight": weight,
            "explainer": question.get("explainer", ""),
        })

    score = round(earned / total_weight, 3) if total_weight else 0.0
    return {
        "score": score,
        "passed": score >= MICRO_EVAL_PASS_FLOOR,
        "scored": scored,
        "correct_count": sum(1 for entry in scored if entry["is_correct"]),
        "total": len(scored),
    }



def run_diagnosis(*, profile_id: str, week: int, attempts: list[Any]) -> dict[str, Any]:
    with tracing.traced_step(
        "learning_recovery", "diagnose",
        input_summary=f"week {week}, replaying the last {RECOVERY_TRIGGER} failed sittings question by question",
    ) as record:
        weakness_report, topic_skill_ids = diagnose(attempts, week=week)
        topics = weakness_report["topics"]
        record["output_summary"] = (
            f"{len(topics)} topic(s) flagged - "
            + ", ".join(f"{topic['topicName']} {topic['status']} at {topic['knowledgeGapScore']}%" for topic in topics)
            if topics else "no single topic crossed the gap line on its own; lowest scorer carried forward"
        )
        record["confidence"] = 0.85

    return {"weakness_report": weakness_report, "topic_skill_ids": topic_skill_ids, "trace": dict(record)}


def run_remediation(
    *, profile_id: str, week: int, weakness_report: dict[str, Any],
    topic_skill_ids: dict[str, str | None], role_node_ids: list[str],
) -> dict[str, Any]:
    with tracing.traced_step(
        "learning_recovery", "build_remediation",
        input_summary=f"week {week}, {len(weakness_report['topics'])} flagged topic(s) to write up",
    ) as record:
        plan = build_remediation(weakness_report["topics"], topic_skill_ids, role_node_ids)
        record["output_summary"] = f"{len(plan)} concept-contrast-analogy note(s) built, worst gap first"
        record["confidence"] = 0.85

    return {"plan": plan, "trace": dict(record)}


def run_micro_eval_generation(
    *, profile_id: str, week: int, cycle: int, weakness_report: dict[str, Any],
    topic_skill_ids: dict[str, str | None], role_node_ids: list[str],
) -> dict[str, Any]:
    with tracing.traced_step(
        "learning_recovery", "generate_micro_eval",
        input_summary=f"week {week}, cycle {cycle}, {len(weakness_report['topics'])} flagged topic(s)",
    ) as record:
        topics = weakness_report["topics"]
        questions = generate_micro_eval(
            profile_id=profile_id, week=week, cycle=cycle, topics=topics,
            topic_skill_ids=topic_skill_ids, role_node_ids=role_node_ids,
        )
        critical_count = sum(1 for topic in topics if topic["status"] == "[CRITICAL GAP]")
        record["output_summary"] = (
            f"{len(questions)} question(s) across {len(topics)} topic(s)"
            + (f", {critical_count} carrying the {CRITICAL_WEIGHT}x critical-gap weight" if critical_count else "")
        )
        record["confidence"] = 0.85

    return {
        "questions": questions,
        "pass_criteria": pass_criteria_text(),
        "weighting_note": weighting_note_text(),
        "trace": dict(record),
    }


def run_micro_grading(*, profile_id: str, week: int, cycle: int, questions: list[dict], answers: list[dict]) -> dict[str, Any]:
    with tracing.traced_step(
        "learning_recovery", "grade_micro_eval",
        input_summary=f"week {week}, cycle {cycle}, {len(answers)} answer(s) to weigh and tally",
    ) as record:
        result = grade_micro_eval(questions, answers)
        record["output_summary"] = (
            f"{result['correct_count']}/{result['total']} correct, {round(result['score'] * 100)} percent "
            f"weighted -> {'cleared the line' if result['passed'] else 'still short of it'}"
        )
        record["confidence"] = result["score"]

    feedback = (
        f"Weighted score: {round(result['score'] * 100)} percent. "
        + (
            "That clears the line - the next checkpoint attempt is open again, and the gap this path "
            "was built for is the one thing this sitting just proved is no longer sitting where it was."
            if result["passed"] else
            f"That sits under the {round(MICRO_EVAL_PASS_FLOOR * 100)} percent line this time - "
            "another look at the notes above and a freshly built check will follow; nothing here repeats "
            "verbatim, so it is worth treating as a real second look rather than a rerun."
        )
    )
    return {**result, "feedback": feedback, "trace": dict(record)}
