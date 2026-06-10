from __future__ import annotations


def _join_names(names: list[str], limit: int = 3) -> str:
    names = [n for n in names if n]
    if not names:
        return "the basics"
    if len(names) == 1:
        return names[0]
    head, last = names[:limit][:-1], names[:limit][-1]
    if not head:
        return last
    return ", ".join(head) + " and " + last


def _pct(value: float) -> str:
    return f"{round(value * 100)} percent"


def _gap_summary(ctx: dict) -> str:
    name = ctx["name"]
    role = ctx["target_role"]
    strengths = _join_names(ctx.get("top_strengths", []))
    gaps = _join_names(ctx.get("top_gaps", []))
    weak_n = ctx.get("weak_count", 0)
    known_n = ctx.get("known_count", 0)
    lines = [
        f"{name}'s profile maps onto {role} with {known_n} skills already in good shape "
        f"and {weak_n} that need real attention before the deadline.",
        f"{strengths} are the strongest starting points - the plan leans on them early "
        f"so the harder climb gets more of the runway.",
        f"{gaps} carry the most weight in the gap map; closing those first is what "
        f"moves the feasibility needle the most.",
    ]
    return " ".join(lines)


def _skill_explainer(ctx: dict) -> str:
    skill = ctx["skill_name"]
    family = ctx["family"]
    hours = ctx["hours"]
    unlocks = _join_names(ctx.get("unlocks_sample", []))
    unlocks_n = ctx.get("unlocks_count", 0)
    placement = ctx.get("placement_relevance", False)
    bloom = ctx.get("bloom_level", 2)
    depth = {1: "remembering the vocabulary", 2: "understanding how it fits together",
             3: "applying it to small problems", 4: "analysing where it breaks down",
             5: "judging trade-offs between approaches", 6: "designing something new with it"}
    out = (
        f"{skill} sits in the {family} family and is scoped at roughly {hours} focused hours - "
        f"enough to move from a standing start to {depth.get(bloom, 'solid working knowledge')}."
    )
    if unlocks_n:
        out += f" Clearing it directly opens the door to {unlocks_n} downstream skill" \
               f"{'s' if unlocks_n != 1 else ''}, including {unlocks}."
    if placement:
        out += " It also shows up directly in placement screening, so the hours here pay twice."
    return out


def _roadmap_rationale(ctx: dict) -> str:
    variant = ctx["variant"]
    milestones = ctx["milestone_count"]
    hours = ctx["total_hours"]
    weekly = ctx["weekly_hours"]
    weeks = ctx["deadline_weeks"]
    feasibility = ctx["feasibility_score"]
    focus = _join_names(ctx.get("focus_skills", []))
    frame = {
        "safe": "keeps the weekly load comfortable and protects against a missed week or two",
        "target": "matches the stated runway closely - it assumes a normal week most weeks",
        "stretch": "front-loads extra ground for a learner who wants to arrive over-prepared",
    }
    capacity = weekly * weeks
    return (
        f"The {variant} path lays out {milestones} milestones across roughly {hours} hours of "
        f"work, against a budget of about {capacity} hours ({weekly} hours a week for {weeks} weeks). "
        f"It {frame.get(variant, 'balances pace against the deadline')}, leans first on "
        f"{focus}, and currently scores {feasibility:.2f} on feasibility - "
        f"{'comfortably inside' if feasibility >= 0.7 else 'within' if feasibility >= 0.55 else 'at the edge of'} "
        f"what the stated hours can realistically cover."
    )


def _resource_why(ctx: dict) -> str:
    title = ctx["resource_title"]
    source = ctx["source"]
    skill = ctx["skill_name"]
    trust = ctx["trust_score"]
    rtype = ctx["resource_type"]
    band = "a strong, well-trusted" if trust >= 0.8 else "a solid" if trust >= 0.65 else "a workable"
    return (
        f"\"{title}\" from {source} was matched to {skill} as {band} {rtype} - "
        f"its trust score of {trust:.2f} weighs how authoritative the source is, how current it stays, "
        f"how the community around it behaves, and how well its level lines up with where you are on this skill."
    )


def _replan_rationale(ctx: dict) -> str:
    reason = ctx["trigger_reason"]
    protected = _join_names(ctx.get("protected_skills", []))
    deferred = _join_names(ctx.get("deferred_skills", []))
    recovered = ctx.get("hours_recovered", 0)
    weeks_left = ctx.get("weeks_remaining", 0)
    return (
        f"Here is what changes and why: {reason}. "
        f"{protected} sit on the critical path to the deadline, so they stay exactly where they "
        f"were and absorb none of the slip. {deferred} can move later without breaking anything "
        f"downstream, which frees up roughly {recovered} hours. "
        f"That leaves {weeks_left} weeks to land the rest at a pace that still looks achievable."
    )


_NUDGE_BY_MOOD = {
    "crushing_it": "{name}, the last stretch has been ahead of pace - {streak} days running and "
                   "a {quiz} quiz score to back it up. This is a good week to pull a stretch topic forward.",
    "on_track": "{name}, steady week - {completion} of the plan logged and a {streak}-day rhythm going. "
                "Keep the same slot on the calendar and the rest takes care of itself.",
    "slipping": "{name}, this week slipped a bit - {completion} completion against the usual pace. "
                "That happens. The plan below trims the load rather than letting the gap compound.",
}


def _nudge(ctx: dict) -> str:
    mood = ctx.get("mood", "on_track")
    template = _NUDGE_BY_MOOD.get(mood, _NUDGE_BY_MOOD["on_track"])
    return template.format(
        name=ctx.get("name", "there"),
        streak=ctx.get("streak_days", 0),
        completion=_pct(ctx.get("completion_rate", 0.0)),
        quiz=_pct(ctx.get("recent_quiz_score", 0.0)),
    )


def _interview_feedback(ctx: dict) -> str:
    overall = ctx["overall_score"]
    dims = ctx.get("rubric_dimensions", [])
    company = ctx.get("company", "the panel")
    strongest = max(dims, key=lambda d: d["score"], default=None)
    weakest = min(dims, key=lambda d: d["score"], default=None)
    band = "a strong" if overall >= 0.75 else "a workable" if overall >= 0.5 else "an early-stage"
    out = f"Overall this reads as {band} answer for {company} - scoring {overall:.2f} across the rubric."
    if strongest and weakest and strongest["name"] != weakest["name"]:
        out += (f" {strongest['name']} carried it ({strongest['note']}); "
                f"{weakest['name']} is the one to tighten next time ({weakest['note']}).")
    elif strongest:
        out += f" {strongest['name']}: {strongest['note']}"
    return out


def _validation_note(ctx: dict) -> str:
    check = ctx["check_name"]
    status = ctx["status"]
    detail = ctx["detail"]
    verdict = {"pass": "passed clean", "adjusted": "needed a small correction", "flagged": "needs a human look"}
    return f"{check} {verdict.get(status, status)}: {detail}"


def _resume_xray(ctx: dict) -> str:
    role = ctx["target_role"]
    matched = _join_names(ctx.get("matched_skills", []), limit=4)
    missing = _join_names(ctx.get("missing_skills", []), limit=4)
    matched_n = ctx.get("matched_count", 0)
    missing_n = ctx.get("missing_count", 0)
    return (
        f"Against {role}, this resume already speaks to {matched_n} of the skills the role looks for - "
        f"{matched} read clearly. The gaps a reviewer would notice are {missing} ({missing_n} in total); "
        f"those are exactly the lines worth adding evidence for before this goes out."
    )


def _project_why(ctx: dict) -> str:
    title = ctx["project_title"]
    role = ctx["target_role"]
    practiced = _join_names(ctx.get("skills_practiced", []), limit=4)
    hours = ctx.get("estimated_hours", 0)
    band = "a strong capstone" if ctx.get("difficulty") == "advanced" else \
           "a solid portfolio piece" if ctx.get("difficulty") == "intermediate" else "a confidence-building first build"
    return (
        f"\"{title}\" is {band} for someone aiming at {role} - it leans on {practiced}, the exact "
        f"ground this roadmap just covered, and runs roughly {hours} focused hours end to end, "
        f"which is enough to leave something real in a portfolio without dragging on past the point of learning."
    )


_TEMPLATES = {
    "gap_summary": _gap_summary,
    "skill_explainer": _skill_explainer,
    "roadmap_rationale": _roadmap_rationale,
    "resource_why": _resource_why,
    "replan_rationale": _replan_rationale,
    "nudge": _nudge,
    "interview_feedback": _interview_feedback,
    "validation_note": _validation_note,
    "resume_xray": _resume_xray,
    "project_why": _project_why,
}


def render_template(kind: str, context: dict) -> str:
    renderer = _TEMPLATES.get(kind)
    if renderer is None:
        return f"({kind} narration is not wired up yet)"
    return renderer(context)


def _prompt_gap_summary(ctx: dict) -> tuple[str, str]:
    system = ("You are a calm, specific career mentor. Write 3 short sentences, no headers, "
              "no bullet points, no emoji. Use the learner's name once.")
    user = (f"Learner: {ctx['name']}. Target role: {ctx['target_role']}. "
            f"Known/strong skills: {ctx.get('top_strengths', [])}. "
            f"Weakest skills: {ctx.get('top_gaps', [])}. "
            f"Counts - known: {ctx.get('known_count', 0)}, weak: {ctx.get('weak_count', 0)}. "
            "Summarise the gap map and what the plan should lean on first.")
    return system, user


def _prompt_skill_explainer(ctx: dict) -> tuple[str, str]:
    system = "Explain a learning topic in 2-3 sentences for a student. Plain language, no jargon padding, no emoji."
    user = (f"Skill: {ctx['skill_name']} (family: {ctx['family']}, ~{ctx['hours']}h, "
            f"Bloom level {ctx.get('bloom_level', 2)}/6). It unlocks: {ctx.get('unlocks_sample', [])}. "
            f"Placement-relevant: {ctx.get('placement_relevance', False)}. "
            "Explain what it is and why it is worth the hours.")
    return system, user


def _prompt_roadmap_rationale(ctx: dict) -> tuple[str, str]:
    system = "Explain a study-plan choice in 3-4 sentences. Concrete numbers, no hype, no emoji."
    user = (f"Path variant: {ctx['variant']}. Milestones: {ctx['milestone_count']}. "
            f"Total hours: {ctx['total_hours']}. Weekly capacity: {ctx['weekly_hours']}h x "
            f"{ctx['deadline_weeks']} weeks. Feasibility score: {ctx['feasibility_score']:.2f}. "
            f"Early focus: {ctx.get('focus_skills', [])}. Justify this plan to the learner.")
    return system, user


def _prompt_resource_why(ctx: dict) -> tuple[str, str]:
    system = "In 1-2 sentences, explain why a learning resource was recommended. No emoji, no hype words."
    user = (f"Resource: '{ctx['resource_title']}' from {ctx['source']} ({ctx['resource_type']}, "
            f"trust score {ctx['trust_score']:.2f}) recommended for the skill '{ctx['skill_name']}'.")
    return system, user


def _prompt_replan_rationale(ctx: dict) -> tuple[str, str]:
    system = "Explain a schedule adjustment in 3 short sentences. Reassuring but factual, no emoji."
    user = (f"Trigger: {ctx['trigger_reason']}. Skills protected on the critical path: "
            f"{ctx.get('protected_skills', [])}. Skills pushed later: {ctx.get('deferred_skills', [])}. "
            f"Hours recovered: {ctx.get('hours_recovered', 0)}. Weeks remaining: {ctx.get('weeks_remaining', 0)}.")
    return system, user


def _prompt_nudge(ctx: dict) -> tuple[str, str]:
    system = "Write one short, specific coaching message (1-2 sentences). Use the learner's name. No emoji, no exclamation overload."
    user = (f"Name: {ctx.get('name')}. Mood: {ctx.get('mood')}. "
            f"Streak days: {ctx.get('streak_days', 0)}. Completion rate: {ctx.get('completion_rate', 0):.2f}. "
            f"Recent quiz score: {ctx.get('recent_quiz_score', 0):.2f}.")
    return system, user


def _prompt_interview_feedback(ctx: dict) -> tuple[str, str]:
    system = "Give interview-answer feedback in 2-3 sentences: one strength, one improvement, grounded in the rubric. No emoji."
    user = (f"Company style: {ctx.get('company')}. Overall score: {ctx['overall_score']:.2f}. "
            f"Rubric dimensions: {ctx.get('rubric_dimensions', [])}.")
    return system, user


def _prompt_validation_note(ctx: dict) -> tuple[str, str]:
    system = "State a quality-check result in one sentence. Plain, factual, no emoji."
    user = f"Check: {ctx['check_name']}. Status: {ctx['status']}. Detail: {ctx['detail']}."
    return system, user


def _prompt_resume_xray(ctx: dict) -> tuple[str, str]:
    system = "Summarise a resume-to-role match in 2-3 sentences: what already lands, what is missing. No emoji."
    user = (f"Target role: {ctx['target_role']}. Matched skills: {ctx.get('matched_skills', [])}. "
            f"Missing skills: {ctx.get('missing_skills', [])}.")
    return system, user


def _prompt_project_why(ctx: dict) -> tuple[str, str]:
    system = "In 2 sentences, explain why a hands-on project suits a learner who just finished their plan. No emoji, no hype words."
    user = (f"Project: '{ctx['project_title']}' (difficulty {ctx.get('difficulty')}, "
            f"about {ctx.get('estimated_hours', 0)} hours). Target role: {ctx['target_role']}. "
            f"Skills it practises: {ctx.get('skills_practiced', [])}.")
    return system, user


_PROMPTS = {
    "gap_summary": _prompt_gap_summary,
    "skill_explainer": _prompt_skill_explainer,
    "roadmap_rationale": _prompt_roadmap_rationale,
    "resource_why": _prompt_resource_why,
    "replan_rationale": _prompt_replan_rationale,
    "nudge": _prompt_nudge,
    "interview_feedback": _prompt_interview_feedback,
    "validation_note": _prompt_validation_note,
    "resume_xray": _prompt_resume_xray,
    "project_why": _prompt_project_why,
}


def build_prompt(kind: str, context: dict) -> tuple[str, str]:
    builder = _PROMPTS.get(kind)
    if builder is None:
        return ("You are a helpful assistant.", f"Write one short paragraph about: {context}")
    return builder(context)
