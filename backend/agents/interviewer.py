from __future__ import annotations

import re
from itertools import zip_longest

from backend.data import drive_banks
from backend.utils import llm, responsible_ai, seed, skill_graph, tracing

_ROUND_LABEL_FALLBACKS: dict[str, str] = {
    "hr": "HR Round",
}

_ROUND_TAG_HINTS: dict[str, set[str]] = {
    "aptitude": {"aptitude", "mathematics"},
    "technical": {"dsa", "programming", "design", "backend", "systems"},
    "behavioral": {"communication", "placement", "business"},
}

_STOP_WORDS = {
    "and", "the", "for", "with", "of", "to", "a", "an", "basics", "fundamentals",
    "principles", "introduction", "core", "advanced", "essentials",
}

_STRUCTURE_MARKERS = (
    "because", "first", "then", "for example", "situation", "result", "so that",
    "which meant", "i decided", "i chose", "as a result", "i started by",
)
_REFLECTION_MARKERS = (
    "learned", "learnt", "next time", "realised", "realized", "differently",
    "in hindsight", "going forward", "would change",
)

_LENGTH_ANCHORS = [(0, 0.18), (12, 0.38), (30, 0.58), (60, 0.74), (110, 0.86), (180, 0.93), (280, 0.97)]


def _interpolate(x: float, anchors: list[tuple[float, float]]) -> float:
    if x <= anchors[0][0]:
        return anchors[0][1]
    if x >= anchors[-1][0]:
        return anchors[-1][1]
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return 0.5


def _length_score(word_count: int) -> float:
    return round(_interpolate(word_count, _LENGTH_ANCHORS), 2)


def _structure_score(lowered: str) -> float:
    hits = sum(1 for marker in _STRUCTURE_MARKERS if marker in lowered)
    return round(min(0.97, 0.30 + 0.15 * hits), 2)


def _keyword_score(lowered: str, keywords: list[str]) -> float:
    keys = [k.lower() for k in keywords if k]
    if not keys:
        return 0.6
    hits = sum(1 for key in keys if key in lowered)
    return round(min(0.97, 0.28 + 0.20 * hits), 2)


def _words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 2 and w not in _STOP_WORDS]


def _topic_keywords(skill_id: str | None, target_role: str) -> list[str]:
    if not skill_id:
        return _words(target_role)
    try:
        info = skill_graph.node(skill_id)
    except KeyError:
        return _words(target_role)
    return list(dict.fromkeys(_words(info["name"]) + list(info["tags"])))


def _pick(bank: list, count: int, seed_key: str) -> list:
    if len(bank) <= count:
        return list(bank)
    start = sum(ord(ch) for ch in seed_key) % len(bank)
    return [bank[(start + i) % len(bank)] for i in range(count)]


_TECHNICAL_TEMPLATES = (
    "Walk me through how you would approach a problem involving {skill}. What is your first move, and why?",
    "Where have you actually used {skill}, even in a small project, and what tripped you up the first time?",
    "If a teammate asked you to explain {skill} in two minutes, what would you say, and what would you deliberately leave out?",
    "What is a mistake people commonly make with {skill}, and how would you catch it during a code review?",
    "How would you decide whether {skill} is the right tool for a problem, versus reaching for something else?",
)

_ROUND_QUESTION_COUNTS: dict[str, int] = {
    "technical": 20,
}
_DEFAULT_QUESTION_COUNT = 4


_DSA_APPROACH_BANK: dict[str, tuple[dict, ...]] = {
    "Software Development Engineer": (
        {"prompt": "You're scanning a huge stream of user click events and need to spot the first one that repeats. What approach would you reach for, and what does it cost in time and memory?", "focus_skill": "sde.hashing"},
        {"prompt": "How would you find the shortest hop count between two people in a friendship network modelled as a graph, and why does that approach beat just trying every path?", "focus_skill": "sde.graphs"},
        {"prompt": "Walk through how you would decide whether a problem actually needs dynamic programming, or whether a simpler greedy pass gets you the same answer for less work.", "focus_skill": "sde.dynamic_programming"},
        {"prompt": "Numbers are arriving one at a time and you need the running median at every point. What structure would you keep updated, and why that one over a plain sorted list?", "focus_skill": "sde.heaps"},
        {"prompt": "How would you check whether a binary tree is height-balanced, and what would the recursive shape of that check look like?", "focus_skill": "sde.trees"},
        {"prompt": "You need to tell whether a linked list loops back on itself, without allocating any extra memory to track what you've seen. What's the approach, and why does it actually work?", "focus_skill": "sde.linked_lists"},
    ),
    "Data Analyst": (
        {"prompt": "You need the top three products by revenue per region out of a sales table with tens of millions of rows. How would you shape that query so it stays fast as the table grows?", "focus_skill": "da.advanced_sql"},
        {"prompt": "A customer table has the same person spelled three different ways across rows. How would you go about finding and merging those duplicates without quietly merging people who are actually different?", "focus_skill": "da.data_cleaning"},
        {"prompt": "A metric moved five percent month over month. How would you work out whether that is a real shift worth acting on, or just the kind of wobble that metric normally has?", "focus_skill": "da.inferential_stats"},
        {"prompt": "You're asked to build a dashboard that has to stay fast even as the data behind it keeps growing. What would you think through before writing the first query for it?", "focus_skill": "da.bi_tools"},
        {"prompt": "Walk through how you would design an experiment to check whether a new checkout flow actually lifts conversion, rather than just looking like it did.", "focus_skill": "da.ab_testing"},
        {"prompt": "Two tables need to be joined and one of them barely fits in memory. How would you approach that join so it doesn't grind the whole pipeline to a halt?", "focus_skill": "da.sql_joins_agg"},
    ),
    "Capgemini Technology Analyst": (
        {"prompt": "A Spring Boot service has to call three downstream systems and combine what they return. How would you handle it if one of those three is slow or simply down?", "focus_skill": "cap.spring_boot_rest"},
        {"prompt": "How do you decide between a List, a Set and a Map for a given Java problem, and what is actually being traded off when you pick one over the others?", "focus_skill": "cap.collections_generics"},
        {"prompt": "A nightly batch job has quietly started taking twice as long as it used to. How would you go about working out why, with nothing to go on yet but that one observation?", "focus_skill": "cap.dbms_normalization"},
        {"prompt": "You need a database design that can show not just a record's current state but how it looked at any point in the past. How would you approach that schema?", "focus_skill": "cap.dbms_normalization"},
        {"prompt": "Walk through how you would write a JUnit and Mockito test suite for a service method that depends on calling an external API.", "focus_skill": "cap.junit_testing"},
        {"prompt": "How would you explain to a client why a change that looks like a one-line fix on their screen actually needs a full sprint to deliver safely?", "focus_skill": "cap.client_comm"},
    ),
    "Data Scientist": (
        {"prompt": "Less than two percent of your rows belong to the class that actually matters. How would you approach building a model that doesn't just learn to ignore it?", "focus_skill": "ds.classification"},
        {"prompt": "You're handed a raw, messy dataset and a vague business question. How would you decide which features to build first, and what you'd leave for later?", "focus_skill": "ds.feature_engineering"},
        {"prompt": "Walk through how you would choose between optimising for precision or recall on a model whose mistakes have very different costs depending on which way they go.", "focus_skill": "ds.model_evaluation"},
        {"prompt": "You need the handful of items most similar to a given one out of a million embeddings. What approach would you reach for, and why not simply compare it against everything?", "focus_skill": "ds.clustering"},
        {"prompt": "Training loss keeps falling but validation loss has started climbing. How would you go about figuring out what's actually going wrong?", "focus_skill": "ds.neural_networks"},
        {"prompt": "Walk through how you would design the path that gets a model out of a notebook and into something serving real predictions reliably.", "focus_skill": "ds.mlops"},
    ),
    "Full Stack Developer": (
        {"prompt": "A page listing thousands of items has started loading slowly. How would you work out whether the bottleneck is the API, the network, or the rendering itself?", "focus_skill": "fs.frontend_perf_testing"},
        {"prompt": "How would you structure the state for a form with a dozen fields that depend on each other, so it stays predictable as more fields get added later?", "focus_skill": "fs.react_hooks_state"},
        {"prompt": "Walk through how you would add pagination to an API that currently just returns everything in one response, without breaking whatever already calls it.", "focus_skill": "fs.rest_apis_node"},
        {"prompt": "How do you decide whether a piece of data belongs in a relational table or a document store, for a feature you're about to build?", "focus_skill": "fs.nosql_mongo"},
        {"prompt": "A user reports briefly seeing someone else's data right after logging in. How would you go about tracking down where that's leaking from?", "focus_skill": "fs.auth_security"},
        {"prompt": "Walk through how you would build a live search box that doesn't fire a request to the server on every single keystroke.", "focus_skill": "fs.es6_async"},
    ),
}


def _interleave(first: list[dict], second: list[dict]) -> list[dict]:
    merged: list[dict] = []
    for a, b in zip_longest(first, second):
        if a is not None:
            merged.append(a)
        if b is not None:
            merged.append(b)
    return merged


_APTITUDE_BANK = (
    {
        "prompt": "A train 150 metres long crosses a platform 350 metres long in 25 seconds. What is its speed in km/h?",
        "kind": "numerical",
        "options": ["54 km/h", "60 km/h", "72 km/h", "80 km/h"],
        "answer": "72 km/h",
        "explainer": "Total distance covered is 150 + 350 = 500 m in 25 s, which is 20 m/s - and 20 x 3.6 = 72 km/h.",
    },
    {
        "prompt": "Look at the series 3, 7, 15, 31, 63. What comes next?",
        "kind": "logical",
        "options": ["95", "111", "127", "135"],
        "answer": "127",
        "explainer": "Each term is double the one before it, plus one: 63 x 2 + 1 = 127.",
    },
    {
        "prompt": "Which word is closest in meaning to 'meticulous'?",
        "kind": "verbal",
        "options": ["Careless", "Thorough", "Hurried", "Indifferent"],
        "answer": "Thorough",
        "explainer": "'Meticulous' describes close, careful attention to detail - 'thorough' sits nearest that meaning of the four.",
    },
    {
        "prompt": "If CODING is written as DPEJOH, how would FLOWER be written under the same rule?",
        "kind": "logical",
        "options": ["GMPXFS", "GMPWFS", "FLOWFR", "GNQYFT"],
        "answer": "GMPXFS",
        "explainer": "Each letter shifts one place forward in the alphabet: F->G, L->M, O->P, W->X, E->F, R->S, giving GMPXFS.",
    },
    {
        "prompt": "A shop takes 20 percent off, then another 10 percent off the new price. What is the overall discount?",
        "kind": "numerical",
        "options": ["18%", "28%", "30%", "32%"],
        "answer": "28%",
        "explainer": "The price ends at 0.8 x 0.9 = 0.72 of the original, a 28 percent drop overall - the two discounts do not simply add to 30 percent because the second one applies to an already-reduced price.",
    },
    {
        "prompt": "A is the brother of B. B is the sister of C. C is the father of D. How is A related to D?",
        "kind": "logical",
        "options": ["Uncle", "Father", "Grandfather", "Brother"],
        "answer": "Uncle",
        "explainer": "A, B and C are siblings, and C is D's parent - which makes A, C's sibling, an uncle to D.",
    },
)

_BEHAVIORAL_BANK = (
    "Tell me about a time a project did not go the way you planned. What did you do once you noticed it was off track?",
    "Describe a time you had to learn something new under real time pressure. How did you decide where to start?",
    "Give an example of disagreeing with a teammate about a technical approach. How did it get resolved, and what would you do differently now?",
    "Tell me about a time you had to explain something technical to someone without that background.",
    "Describe a time you noticed a problem nobody had asked you to fix. What made you act on it?",
)

_HR_TEMPLATES = (
    "Why {company}, and why this kind of role specifically, what makes it a good match for where you want to go?",
    "Where do you expect to be three years from now, and how does a {role} role fit into that path?",
    "What is something you are actively working on improving about how you work?",
    "Tell me about a time outside of coursework where you took initiative without being asked to.",
)


def _technical_questions(company_key: str, target_role: str, gap_map: dict | None, count: int) -> list[dict]:
    bank = drive_banks.technical_bank(company_key, target_role)
    if bank:
        raw = list(bank)[:count]
        return [
            {
                "id": f"q{i + 1}",
                "kind": "technical",
                "section": item.get("section", "Technical"),
                "difficulty": item.get("difficulty", "Medium"),
                "time_limit": item.get("time_limit", 90),
                "format": item.get("format", "Open-Ended"),
                "prompt": item["prompt"],
                "code_snippet": item.get("code_snippet"),
                "focus_skill": item.get("focus_skill"),
                "options": item.get("options"),
                "answer": item.get("answer"),
                "justification": item.get("justification"),
                "evaluation_rubric": item.get("evaluation_rubric"),
                "angle": "drive-curated",
            }
            for i, item in enumerate(raw)
        ]

    critical = skill_graph.critical_path(target_role)
    gap_ids = [item["skill_id"] for item in (gap_map or {}).get("gap", [])]
    pool = list(dict.fromkeys(gap_ids[:3] + critical))

    approach_bank = _DSA_APPROACH_BANK.get(target_role, ())
    approach_count = min(len(approach_bank), count // 2)
    concept_count = max(0, count - approach_count)

    if len(pool) < concept_count:
        pool = list(dict.fromkeys(pool + skill_graph.role_node_ids(target_role)))
    pool = skill_graph.topo_rank(pool)

    concepts = [
        {
            "kind": "technical",
            "section": "Technical",
            "difficulty": "Medium",
            "time_limit": 90,
            "format": "Open-Ended",
            "prompt": _TECHNICAL_TEMPLATES[index % len(_TECHNICAL_TEMPLATES)].format(
                skill=skill_graph.node(skill_id)["name"]
            ),
            "code_snippet": None,
            "focus_skill": skill_id,
            "options": None,
            "angle": "core concept",
        }
        for index, skill_id in enumerate(pool[:concept_count])
    ]
    approaches = [
        {
            "kind": "technical",
            "section": "Approach & Design",
            "difficulty": "Medium",
            "time_limit": 90,
            "format": "Open-Ended",
            "prompt": entry["prompt"],
            "code_snippet": None,
            "focus_skill": entry.get("focus_skill"),
            "options": None,
            "angle": "approach & design",
        }
        for entry in _pick(list(approach_bank), approach_count, target_role)
    ]

    mixed = _interleave(concepts, approaches)[:count]
    return [{**item, "id": f"q{index + 1}"} for index, item in enumerate(mixed)]


def _aptitude_questions(company_key: str, count: int) -> list[dict]:
    bank = drive_banks.aptitude_bank(company_key)
    source = list(bank) if bank else list(_APTITUDE_BANK)
    chosen = _pick(source, count, company_key)
    return [
        {
            "id": f"q{i + 1}",
            "kind": item.get("kind", "numerical"),
            "section": item.get("section", "Aptitude"),
            "difficulty": "Medium",
            "time_limit": item.get("time_limit", 60),
            "format": "MCQ",
            "prompt": item["prompt"],
            "code_snippet": None,
            "focus_skill": None,
            "options": item["options"],
            "answer": item["answer"],
            "explainer": item["explainer"],
        }
        for i, item in enumerate(chosen)
    ]


def _behavioral_questions(company_key: str, target_role: str, count: int) -> list[dict]:
    bank = drive_banks.behavioral_bank(company_key, target_role)
    if bank:
        chosen = _pick(list(bank), count, company_key + target_role)
        return [
            {
                "id": f"q{i + 1}",
                "kind": "behavioral",
                "section": "Behavioural - SAR",
                "difficulty": "Open-Ended",
                "time_limit": 180,
                "format": "Open-Ended",
                "prompt": prompt,
                "code_snippet": None,
                "focus_skill": None,
                "options": None,
            }
            for i, prompt in enumerate(chosen)
        ]
    chosen = _pick(list(_BEHAVIORAL_BANK), count, company_key)
    return [
        {
            "id": f"q{i + 1}",
            "kind": "behavioral",
            "section": "Behavioural - SAR",
            "difficulty": "Open-Ended",
            "time_limit": 180,
            "format": "Open-Ended",
            "prompt": prompt,
            "code_snippet": None,
            "focus_skill": None,
            "options": None,
        }
        for i, prompt in enumerate(chosen)
    ]


def _hr_questions(company_key: str, target_role: str, company_display: str, count: int) -> list[dict]:
    bank = drive_banks.hr_bank(company_key)
    if bank:
        chosen = _pick(list(bank), count, company_key + target_role)
        return [
            {
                "id": f"q{i + 1}",
                "kind": "hr",
                "section": item.get("group", "HR"),
                "difficulty": "Open-Ended",
                "time_limit": 180,
                "format": "Open-Ended",
                "prompt": item["template"].format(role=target_role),
                "code_snippet": None,
                "focus_skill": None,
                "options": None,
            }
            for i, item in enumerate(chosen)
        ]
    chosen = _pick(list(_HR_TEMPLATES), count, target_role)
    return [
        {
            "id": f"q{i + 1}",
            "kind": "hr",
            "section": "HR",
            "difficulty": "Open-Ended",
            "time_limit": 180,
            "format": "Open-Ended",
            "prompt": template.format(company=company_display, role=target_role),
            "code_snippet": None,
            "focus_skill": None,
            "options": None,
        }
        for i, template in enumerate(chosen)
    ]


def _select_section(profile: dict | None, round_type: str) -> dict | None:
    if not profile:
        return None
    hints = _ROUND_TAG_HINTS.get(round_type)
    if not hints:
        return None
    best, best_overlap = None, 0
    for section in profile.get("sections", []):
        overlap = len(hints & set(section.get("focus_tags", [])))
        if overlap > best_overlap:
            best, best_overlap = section, overlap
    return best


_DRIVE_BENCHMARKS: dict[str, dict] = {
    "cap_exceller": {"label": "Capgemini Exceller", "cutoff_pct": 65, "note": "indicative - based on widely-reported prep experiences, not officially published"},
    "tcs_nqt":       {"label": "TCS NQT", "cutoff_pct": 65, "note": "indicative - commonly cited by aspirants, unverified"},
    "infytq":        {"label": "InfyTQ", "cutoff_pct": 65, "note": "officially published in Infosys InfyTQ examination guidelines"},
    "wipro_nlth":    {"label": "Wipro NLTH", "cutoff_pct": 60, "note": "indicative - unverified"},
    "accenture_asset":  {"label": "Accenture ASSET", "cutoff_pct": 65, "note": "indicative - unverified"},
    "cognizant_genc":   {"label": "Cognizant GenC", "cutoff_pct": 60, "note": "indicative - unverified"},
}

_IMPROVEMENT_TOPICS: dict[str, list[dict]] = {
    "DSA": {"area": "Data Structures & Algorithms", "resources": ["NeetCode (neetcode.io) - curated problem list, free", "Striver's SDE Sheet - structured 180-problem plan"]},
    "Core CS": {"area": "Core CS Fundamentals (OS, DBMS, CN, OOPS)", "resources": ["GeeksforGeeks Last-Minute Notes - OS, DBMS, CN", "Interviewbit Core CS module - structured Q&A"]},
    "System Design": {"area": "System Design", "resources": ["System Design Primer (github.com/donnemartin) - free, comprehensive", "ByteByteGo newsletter - concise visual explainers"]},
    "Code Output": {"area": "Code Reading & Debugging", "resources": ["Python Tutor (pythontutor.com) - step-through visualiser, free", "Practice output-prediction questions on HackerRank"]},
    "Numerical": {"area": "Numerical Reasoning", "resources": ["IndiaBix - Aptitude section, free", "R.S. Aggarwal Quantitative Aptitude - standard campus prep book"]},
    "Logical": {"area": "Logical Reasoning", "resources": ["IndiaBix - Reasoning section, free", "M.K. Pandey Analytical Reasoning - standard campus prep book"]},
    "Verbal": {"area": "Verbal Ability", "resources": ["IndiaBix - Verbal Ability section, free", "Word Power Made Easy (Norman Lewis) - vocabulary building"]},
    "Behavioural - SAR": {"area": "Behavioural Interviewing (STAR method)", "resources": ["Big Interview (biginterview.com) - structured STAR practice", "STAR Method guide on Indeed Career Guide, free"]},
    "HR": {"area": "HR Round Preparation", "resources": ["Glassdoor company reviews - understand culture fit questions", "HR Interview Questions by Arihant - common campus HR Q&A"]},
}


def post_interview_report(
    questions: list[dict],
    answers: list[dict],
    company_key: str,
    round_type: str,
) -> dict:
    benchmark = _DRIVE_BENCHMARKS.get(company_key, {"label": company_key, "cutoff_pct": 65, "note": "indicative"})
    answered_map = {a["question_id"]: a for a in answers}

    section_totals: dict[str, dict] = {}
    for q in questions:
        sec = q.get("section", round_type.title())
        entry = section_totals.setdefault(sec, {"attempted": 0, "score_sum": 0.0})
        if q["id"] in answered_map:
            entry["attempted"] += 1
            entry["score_sum"] += answered_map[q["id"]].get("overall_score", 0.0)

    section_breakdown = []
    for sec, data in section_totals.items():
        if data["attempted"] == 0:
            pct = 0.0
        else:
            pct = round(data["score_sum"] / data["attempted"] * 100, 1)
        status = "STRONG" if pct >= 75 else ("AVERAGE" if pct >= 50 else "WEAK")
        section_breakdown.append({
            "section": sec,
            "attempted": data["attempted"],
            "section_score_pct": pct,
            "status": status,
        })

    total_answered = len(answers)
    raw_pct = round(
        sum(a.get("overall_score", 0.0) for a in answers) / max(1, total_answered) * 100, 1
    )
    cutoff = benchmark["cutoff_pct"]
    verdict = "PASS" if raw_pct >= cutoff else ("REVIEW REQUIRED" if round_type in ("behavioral", "hr") else "FAIL")

    weak_sections = sorted(
        [s for s in section_breakdown if s["status"] in ("WEAK", "AVERAGE")],
        key=lambda s: s["section_score_pct"],
    )[:3]
    top_improvements = []
    for weak in weak_sections:
        topic_data = _IMPROVEMENT_TOPICS.get(weak["section"], {
            "area": weak["section"],
            "resources": ["GeeksforGeeks - free topic reference", "YouTube - search the topic name for walkthroughs"],
        })
        top_improvements.append({
            "area": topic_data["area"],
            "section_score_pct": weak["section_score_pct"],
            "reason": f"Scored {weak['section_score_pct']}% in {weak['section']} - below the level a strong round in this drive typically needs.",
            "recommended_resources": topic_data["resources"],
        })

    readiness_pct = round(raw_pct / max(1, cutoff) * 100, 1)

    return {
        "raw_score_pct": raw_pct,
        "drive_benchmark": {
            "drive_label": benchmark["label"],
            "cutoff_pct": cutoff,
            "note": benchmark["note"],
        },
        "verdict": verdict,
        "section_breakdown": section_breakdown,
        "top_improvement_areas": top_improvements,
        "drive_readiness_pct": min(100.0, readiness_pct),
        "overall_feedback": (
            f"You scored {raw_pct}% overall in this {round_type} round, against a {benchmark['label']} "
            f"indicative cutoff of around {cutoff}%. "
            + (f"That puts you above the line - the areas below are still worth sharpening before the real thing."
               if raw_pct >= cutoff
               else f"Some focused work on the sections below should close that gap before the actual drive.")
        ),
    }


def start_session(company: str, round_type: str, target_role: str, gap_map: dict | None = None, *, count: int | None = None) -> dict:
    resolved_count = count if count is not None else _ROUND_QUESTION_COUNTS.get(round_type, _DEFAULT_QUESTION_COUNT)

    with tracing.traced_step(
        "mock_interview", "start_session", input_summary=f"{company}/{round_type} for {target_role}",
    ) as record:
        profile = seed.load_company_profiles().get(company)
        section = _select_section(profile, round_type)
        company_display = profile["display_name"] if profile else company.replace("_", " ").title()

        if round_type == "technical":
            questions = _technical_questions(company, target_role, gap_map, resolved_count)
        elif round_type == "aptitude":
            questions = _aptitude_questions(company, resolved_count)
        elif round_type == "behavioral":
            questions = _behavioral_questions(company, target_role, resolved_count)
        else:
            questions = _hr_questions(company, target_role, company_display, resolved_count)

        is_drive_curated = drive_banks.technical_bank(company, target_role) is not None if round_type == "technical" else False
        fairness_note = None
        if profile:
            fairness_note = responsible_ai.fairness_caveat(profile.get("confidence", "indicative"), profile.get("source_note", ""))

        record["output_summary"] = f"{len(questions)} {round_type} questions built for {company_display}"
        record["confidence"] = 0.95 if is_drive_curated else (0.92 if section or round_type == "behavioral" else 0.8)

    round_labels = {"technical": "Technical Round", "aptitude": "Aptitude Round", "behavioral": "Behavioural Round", "hr": "HR Round"}
    return {
        "company_display": company_display,
        "round_label": round_labels.get(round_type, round_type.replace("_", " ").title()),
        "is_drive_curated": is_drive_curated,
        "questions": questions,
        "fairness_note": fairness_note,
        "trace": dict(record),
    }


def _dimensions(round_type: str, question: dict, lowered: str, length: float, structure: float, target_role: str, company_display: str) -> list[dict]:
    if round_type == "technical":
        focus = question.get("focus_skill")
        try:
            topic = skill_graph.node(focus)["name"] if focus else target_role
        except KeyError:
            topic = target_role
        relevance = _keyword_score(lowered, _topic_keywords(focus, target_role))
        return [
            {"name": "Relevance", "score": relevance, "note": f"how directly this engages with {topic}"},
            {"name": "Depth", "score": length, "note": "how developed the explanation is beyond a one-line answer"},
            {"name": "Structure", "score": structure, "note": "whether the reasoning is organised into clear steps"},
        ]
    if round_type == "behavioral":
        reflection = _keyword_score(lowered, list(_REFLECTION_MARKERS))
        return [
            {"name": "Specificity", "score": length, "note": "whether this names a real situation rather than speaking in generalities"},
            {"name": "Structure", "score": structure, "note": "whether it follows a situation, action, result shape"},
            {"name": "Reflection", "score": reflection, "note": "whether it names what was learned or would change next time"},
        ]
    alignment_keywords = _words(target_role) + _words(company_display)
    return [
        {"name": "Authenticity", "score": length, "note": "whether this reads as considered rather than a rehearsed line"},
        {"name": "Alignment", "score": _keyword_score(lowered, alignment_keywords), "note": "whether it connects back to the role or company"},
        {"name": "Clarity", "score": structure, "note": "how clearly the answer is organised"},
    ]


def _mcq_dimensions(question: dict, choice: str) -> tuple[list[dict], bool]:
    correct = (question.get("answer") or "").strip()
    options = question.get("options")

    resolved_choice = choice.strip()
    if isinstance(options, list) and len(resolved_choice) == 1 and resolved_choice.upper() in "ABCD":
        idx = ord(resolved_choice.upper()) - 65
        if 0 <= idx < len(options):
            resolved_choice = options[idx]

    is_correct = resolved_choice.casefold() == correct.casefold()
    explainer = question.get("explainer", "")
    note = (
        f"Correct - {explainer}" if is_correct
        else f"The keyed answer is '{correct}'. {explainer}"
    )
    return [{"name": "Correct option chosen", "score": 1.0 if is_correct else 0.0, "note": note}], is_correct


def score_answer(question: dict, answer: str, target_role: str, company_key: str) -> dict:
    with tracing.traced_step(
        "mock_interview", "score_answer", input_summary=f"{question.get('kind', 'general')} | {len(answer.split())}-word answer",
    ) as record:
        company_display = (seed.load_company_profiles().get(company_key) or {}).get("display_name", company_key)
        is_mcq = bool(question.get("options"))

        if is_mcq:
            dimensions, is_correct = _mcq_dimensions(question, answer)
            overall = dimensions[0]["score"]
            feedback = (
                f"Correct - the keyed answer is '{question.get('answer')}'. {question.get('explainer', '')}"
                if is_correct
                else f"Not quite - the keyed answer is '{question.get('answer')}', not '{answer.strip()}'. {question.get('explainer', '')}"
            )
            record["output_summary"] = f"{'correct' if is_correct else 'incorrect'} option chosen for an aptitude question"
            record["confidence"] = overall
        else:
            lowered = answer.lower().strip()
            word_count = len(answer.split())
            length = _length_score(word_count)
            structure = _structure_score(lowered)

            dimensions = _dimensions(question.get("kind", "technical"), question, lowered, length, structure, target_role, company_display)
            overall = round(sum(d["score"] for d in dimensions) / len(dimensions), 3)

            feedback = llm.get_llm_provider().narrate("interview_feedback", {
                "overall_score": overall, "rubric_dimensions": dimensions, "company": company_display,
            }).text

            record["output_summary"] = f"scored {overall:.2f} across {len(dimensions)} dimensions ({word_count} words)"
            record["confidence"] = overall

    return {"overall_score": overall, "rubric_dimensions": dimensions, "feedback": feedback, "trace": dict(record)}


def _resume_terms(skill_id: str) -> set[str]:
    info = skill_graph.node(skill_id)
    terms = {info["name"].lower()}
    terms.update(_words(info["name"]))
    terms.update(tag.replace("-", " ") for tag in info["tags"])
    return terms


def resume_xray(resume_text: str, target_role: str) -> dict:
    with tracing.traced_step(
        "mock_interview", "resume_xray", input_summary=f"{len(resume_text)}-character resume for {target_role}",
    ) as record:
        redacted, removed = responsible_ai.redact_pii(resume_text)
        lowered = redacted.lower()

        node_ids = skill_graph.role_node_ids(target_role)
        matched, missing = [], []
        for skill_id in node_ids:
            terms = _resume_terms(skill_id)
            target = matched if any(term in lowered for term in terms) else missing
            target.append(skill_graph.node(skill_id)["name"])

        narrated = llm.get_llm_provider().narrate("resume_xray", {
            "target_role": target_role,
            "matched_skills": matched[:6],
            "missing_skills": missing[:6],
            "matched_count": len(matched),
            "missing_count": len(missing),
        })

        record["output_summary"] = (
            f"{len(matched)} skills matched, {len(missing)} missing, {len(removed)} PII item group(s) redacted"
        )
        record["confidence"] = round(len(matched) / max(1, len(node_ids)), 3)

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "matched_count": len(matched),
        "missing_count": len(missing),
        "redaction_summary": removed,
        "narration": narrated.text,
        "trace": dict(record),
    }
