from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from backend.agents import learning_recovery, weekly_test
from backend.models.database import FsrsCard, ProgressEvent, RecoveryEvaluation, Resource, WeeklyTestAttempt
from backend.models.schemas import WeeklyTestAnswerIn, WeeklyTestStartIn
from backend.routers import deps
from backend.routers.deps import SessionDep

router = APIRouter(tags=["weekly-test"])

_QUESTION_KEY_FIELDS = ("answer", "explainer", "justification")


def _public_question(question: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in question.items() if key not in _QUESTION_KEY_FIELDS}


async def _attempts_for_profile(session: SessionDep, profile_id: str) -> list[WeeklyTestAttempt]:
    rows = (await session.execute(
        select(WeeklyTestAttempt).where(WeeklyTestAttempt.profile_id == profile_id)
        .order_by(WeeklyTestAttempt.started_at)
    )).scalars().all()
    return list(rows)


_RESOURCE_TRUST_FLOOR = 0.55  # mirrors `resource_curator.TRUST_FLOOR` - the line below which nothing surfaces


async def _top_resource_briefs(session: SessionDep, skill_ids: list[str]) -> dict[str, dict]:
    if not skill_ids:
        return {}
    rows = (await session.execute(
        select(Resource)
        .where(Resource.skill_id.in_(skill_ids), Resource.trust_score >= _RESOURCE_TRUST_FLOOR)
        .order_by(Resource.skill_id, Resource.trust_score.desc())
    )).scalars().all()
    briefs: dict[str, dict] = {}
    for row in rows:
        briefs.setdefault(row.skill_id, {
            "title": row.title,
            "resource_type": row.resource_type,
            "difficulty": row.difficulty,
            "source": row.source,
        })
    return briefs


async def _cards_for_skills(session: SessionDep, profile_id: str, skill_ids: list[str]) -> list[FsrsCard]:
    if not skill_ids:
        return []
    rows = (await session.execute(
        select(FsrsCard).where(FsrsCard.profile_id == profile_id, FsrsCard.skill_id.in_(skill_ids))
    )).scalars().all()
    return list(rows)


def _retake_gate(cards: list[FsrsCard], since: datetime | None) -> dict[str, Any]:
    if not cards:
        return {"cleared": True, "reviewed": 0, "total": 0}
    if since is None:
        return {"cleared": True, "reviewed": len(cards), "total": len(cards)}
    reviewed = sum(1 for card in cards if card.last_review and card.last_review > since)
    return {"cleared": reviewed >= len(cards), "reviewed": reviewed, "total": len(cards)}


def _week_state(
    *, week_row: dict[str, Any], attempts: list[WeeklyTestAttempt], gate: dict[str, Any] | None, unlocked: bool,
    recovery_blocked: bool = False, recovery_triggered: bool = False,
) -> dict[str, Any]:
    week = week_row["week"]
    week_attempts = [a for a in attempts if a.week == week and a.status == "submitted"]
    best_band = None
    for attempt in week_attempts:
        if attempt.band == "passed":
            best_band = "passed"
            break
        if attempt.band == "partial" and best_band != "passed":
            best_band = "partial"
        elif best_band is None:
            best_band = attempt.band

    log_cleared = any(
        a.score is not None and a.score >= weekly_test.LOG_FLOOR for a in week_attempts
    )

    if not unlocked:
        lock_state = "locked"
        reason = "Log the week ahead of this one as done first - its resources and this checkpoint open together."
    elif best_band == "passed":
        lock_state = "cleared"
        reason = "Cleared - no retake needed. Log this week from the progress tab to move the chain forward."
    elif not week_attempts:
        lock_state = "ready"
        reason = (
            "Open - the resources for this week are unlocked. Sit the checkpoint first; "
            f"{round(weekly_test.LOG_FLOOR * 100)} percent or higher is what then lets you log the week as done."
        )
    elif recovery_blocked:
        lock_state = "recovery_required"
        reason = (
            "Three sittings have now landed under the line in a row - a plain retake stays closed until "
            "the Learning Recovery panel below has been read through and its short, weighted check cleared."
        )
    elif gate and not gate["cleared"]:
        lock_state = "revision_required"
        reason = (
            f"Work back through the revision deck for this week's skills "
            f"({gate['reviewed']}/{gate['total']} cards reviewed since the last sitting) before retaking."
        )
    else:
        lock_state = "retake_ready"
        reason = (
            "Revision pass complete - a retake is open. "
            + ("Last sitting cleared the logging bar already - log the week whenever you are ready."
               if log_cleared else
               f"Last sitting sat under {round(weekly_test.LOG_FLOOR * 100)} percent, so logging the week stays closed until a retake clears it.")
        )

    return {
        "week": week,
        "modules_status": week_row["status"],
        "lock_state": lock_state,
        "reason": reason,
        "attempt_count": len(week_attempts),
        "best_band": best_band,
        "last_score": week_attempts[-1].score if week_attempts else None,
        "log_unlocked": log_cleared,
        "recovery_triggered": recovery_triggered,
    }


@router.get("/api/weekly-test/{profile_id}/board")
async def get_weekly_test_board(profile_id: str, session: SessionDep) -> dict[str, Any]:
    profile = await deps.get_profile_or_404(session, profile_id)
    roadmap_row = await deps.get_latest_roadmap_or_404(session, profile_id)
    progress_rows = (await session.execute(
        select(ProgressEvent).where(ProgressEvent.profile_id == profile_id)
    )).scalars().all()
    progress = deps.progress_tracker(roadmap_row, progress_rows)
    unlocked_weeks = deps.unlocked_week_numbers(progress)
    attempts = await _attempts_for_profile(session, profile_id)
    attempts_by_week = {}
    for attempt in attempts:
        attempts_by_week.setdefault(attempt.week, []).append(attempt)

    recovery_rows = (await session.execute(
        select(RecoveryEvaluation).where(RecoveryEvaluation.profile_id == profile_id)
        .order_by(RecoveryEvaluation.created_at.desc())
    )).scalars().all()
    latest_recovery_by_week: dict[int, RecoveryEvaluation] = {}
    for row in recovery_rows:
        latest_recovery_by_week.setdefault(row.week, row)

    boards = []
    for week_row in progress["weeks"]:
        week_attempts = attempts_by_week.get(week_row["week"], [])
        last_failed_or_partial = next(
            (a for a in reversed(week_attempts) if a.status == "submitted" and a.band in ("partial", "failed")), None,
        )
        gate = None
        if last_failed_or_partial is not None:
            cards = await _cards_for_skills(session, profile_id, week_row["skill_ids"])
            gate = _retake_gate(cards, last_failed_or_partial.submitted_at)
        recovery_triggered = learning_recovery.eligible_for_recovery(week_attempts)
        recovery_blocked = learning_recovery.retake_blocked_by_recovery(
            week_attempts, latest_recovery_by_week.get(week_row["week"]),
        )
        boards.append(_week_state(
            week_row=week_row, attempts=week_attempts, gate=gate, unlocked=week_row["week"] in unlocked_weeks,
            recovery_blocked=recovery_blocked, recovery_triggered=recovery_triggered,
        ))

    _ = profile  # the profile load is the auth/existence check; nothing else here needs its fields
    return {"weeks": boards, "violation_autosubmit_threshold": weekly_test.VIOLATION_AUTOSUBMIT_THRESHOLD}


@router.post("/api/weekly-test/{profile_id}/start", status_code=201)
async def start_weekly_test(profile_id: str, payload: WeeklyTestStartIn, session: SessionDep) -> dict[str, Any]:
    profile = await deps.get_profile_or_404(session, profile_id)
    roadmap_row = await deps.get_latest_roadmap_or_404(session, profile_id)
    progress_rows = (await session.execute(
        select(ProgressEvent).where(ProgressEvent.profile_id == profile_id)
    )).scalars().all()
    progress = deps.progress_tracker(roadmap_row, progress_rows)

    week_row = next((w for w in progress["weeks"] if w["week"] == payload.week), None)
    if week_row is None:
        raise HTTPException(status_code=404, detail=f"Week {payload.week} is not part of this learner's active roadmap.")
    if payload.week not in deps.unlocked_week_numbers(progress):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Week {payload.week} is not open yet - log the week before it as done first, "
                "and both its resources and this checkpoint unlock together."
            ),
        )

    attempts = await _attempts_for_profile(session, profile_id)
    all_week_attempts = [a for a in attempts if a.week == payload.week]
    week_attempts = [a for a in all_week_attempts if a.status == "submitted"]
    if any(a.band == "passed" for a in week_attempts):
        raise HTTPException(status_code=409, detail=f"Week {payload.week}'s checkpoint is already cleared - no retake needed.")

    recovery_row = (await session.execute(
        select(RecoveryEvaluation)
        .where(RecoveryEvaluation.profile_id == profile_id, RecoveryEvaluation.week == payload.week)
        .order_by(RecoveryEvaluation.created_at.desc())
    )).scalars().first()
    if learning_recovery.retake_blocked_by_recovery(all_week_attempts, recovery_row):
        raise HTTPException(
            status_code=409,
            detail=(
                "Three sittings of this week's checkpoint have now landed under "
                f"{round(learning_recovery.RECOVERY_FLOOR * 100)} percent in a row - a plain retake stays "
                "closed until the Learning Recovery panel on this tab has been read through and its short, "
                "weighted check cleared. That is what reopens this attempt, in place of a fourth blind run "
                "at the same paper."
            ),
        )

    open_sitting = next((a for a in attempts if a.week == payload.week and a.status == "in_progress"), None)
    if open_sitting is not None:
        answered = len(open_sitting.answers)
        if answered >= len(open_sitting.questions):
            graded = weekly_test.run_grading(
                profile_id=profile_id, week=open_sitting.week, attempt_number=open_sitting.attempt_number,
                questions=open_sitting.questions, answers=open_sitting.answers,
            )
            open_sitting.status = "submitted"
            open_sitting.score = graded["score"]
            open_sitting.band = graded["band"]
            open_sitting.feedback = graded["feedback"]
            open_sitting.submitted_at = datetime.utcnow()
            session.add(deps.audit_row_from_trace(profile_id, graded["trace"]))
            session.add(ProgressEvent(
                profile_id=profile_id, roadmap_id=open_sitting.roadmap_id, week=open_sitting.week, skill_id="",
                event_type="quiz", quiz_score=graded["score"],
                notes=f"Weekly checkpoint attempt {open_sitting.attempt_number}: {graded['band']} ({round(graded['score'] * 100)} percent).",
            ))
            await session.commit()
            raise HTTPException(status_code=409, detail="That sitting had already answered every question - it has been graded and closed. Refresh to see the result.")
        elapsed_seconds = (datetime.utcnow() - open_sitting.started_at).total_seconds()
        seconds_remaining = max(0, open_sitting.time_limit_minutes * 60 - int(elapsed_seconds))
        return {
            "attempt_id": open_sitting.id,
            "week": payload.week,
            "attempt_number": open_sitting.attempt_number,
            "total_questions": len(open_sitting.questions),
            "time_limit_minutes": open_sitting.time_limit_minutes,
            "seconds_remaining": seconds_remaining,
            "pass_floor": weekly_test.PASS_FLOOR,
            "partial_floor": weekly_test.PARTIAL_FLOOR,
            "first_question": _public_question(open_sitting.questions[answered]),
            "question_index": answered + 1,
            "resumed": True,
        }

    if week_attempts:
        last = week_attempts[-1]
        cards = await _cards_for_skills(session, profile_id, week_row["skill_ids"])
        gate = _retake_gate(cards, last.submitted_at)
        if not gate["cleared"]:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Revise this week's flashcard deck again before retaking - "
                    f"{gate['reviewed']}/{gate['total']} cards reviewed since the last sitting."
                ),
            )

    attempt_number = len(week_attempts) + 1

    resource_briefs = await _top_resource_briefs(session, week_row["skill_ids"])

    checkpoint_history = [
        {
            "questionsAsked": [
                {
                    "conceptTag": q.get("concept_tag", ""),
                    "questionType": q.get("question_type", ""),
                }
                for q in (a.questions or [])
            ]
        }
        for a in week_attempts
    ]

    built = weekly_test.run_generation(
        profile_id=profile_id, target_role=profile.target_role, week=payload.week,
        attempt_number=attempt_number, active_milestones=roadmap_row.active_milestones,
        resource_picks={skill_id: [brief] for skill_id, brief in resource_briefs.items()},
        checkpoint_history=checkpoint_history,
    )
    attempt = WeeklyTestAttempt(
        profile_id=profile_id, roadmap_id=roadmap_row.id, week=payload.week, attempt_number=attempt_number,
        questions=built["questions"], time_limit_minutes=built["time_limit_minutes"],
    )
    session.add(attempt)
    session.add(deps.audit_row_from_trace(profile_id, built["trace"]))
    await session.commit()
    await session.refresh(attempt)

    return {
        "attempt_id": attempt.id,
        "week": payload.week,
        "attempt_number": attempt_number,
        "total_questions": len(built["questions"]),
        "time_limit_minutes": built["time_limit_minutes"],
        "seconds_remaining": built["time_limit_minutes"] * 60,
        "pass_floor": weekly_test.PASS_FLOOR,
        "partial_floor": weekly_test.PARTIAL_FLOOR,
        "first_question": _public_question(built["questions"][0]),
        "question_index": 1,
        "resumed": False,
    }


@router.post("/api/weekly-test/{profile_id}/answer")
async def submit_weekly_test_answer(profile_id: str, payload: WeeklyTestAnswerIn, session: SessionDep) -> dict[str, Any]:
    profile = await deps.get_profile_or_404(session, profile_id)
    attempt = await deps.get_or_404(session, WeeklyTestAttempt, payload.attempt_id, label="weekly checkpoint attempt")
    if attempt.profile_id != profile_id:
        raise HTTPException(status_code=404, detail=f"No checkpoint attempt found for id '{payload.attempt_id}'.")
    if attempt.status != "in_progress":
        raise HTTPException(status_code=409, detail="This sitting is already finished - its result will not change.")

    questions = attempt.questions
    answers = list(attempt.answers)
    expected = questions[len(answers)] if len(answers) < len(questions) else None
    if expected is None or expected["id"] != payload.question_id:
        raise HTTPException(
            status_code=400,
            detail="That is not the next question in this paper - questions must be answered in order, none skipped.",
        )

    answers.append({"question_id": payload.question_id, "choice": payload.choice, "locked_at": datetime.utcnow().isoformat()})
    attempt.answers = answers
    if payload.proctor_events:
        attempt.proctoring_log = [*attempt.proctoring_log, *payload.proctor_events]

    violation_count = len(attempt.proctoring_log)
    forced = violation_count >= weekly_test.VIOLATION_AUTOSUBMIT_THRESHOLD
    finished = len(answers) == len(questions) or forced

    response: dict[str, Any] = {"question_index": len(answers), "total_questions": len(questions), "violation_count": violation_count}

    if finished:
        if forced and len(answers) < len(questions):
            for question in questions[len(answers):]:
                answers.append({"question_id": question["id"], "choice": "", "locked_at": datetime.utcnow().isoformat(), "auto_marked": True})
            attempt.answers = answers

        graded = weekly_test.run_grading(
            profile_id=profile_id, week=attempt.week, attempt_number=attempt.attempt_number,
            questions=questions, answers=answers,
        )
        attempt.status = "submitted"
        attempt.score = graded["score"]
        attempt.band = graded["band"]
        attempt.feedback = graded["feedback"]
        attempt.submitted_at = datetime.utcnow()
        session.add(deps.audit_row_from_trace(profile_id, graded["trace"]))
        session.add(ProgressEvent(
            profile_id=profile_id, roadmap_id=attempt.roadmap_id, week=attempt.week, skill_id="",
            event_type="quiz", quiz_score=graded["score"],
            notes=f"Weekly checkpoint attempt {attempt.attempt_number}: {graded['band']} ({round(graded['score'] * 100)} percent).",
        ))
        is_passing_celebration = graded.get("celebration_trigger", False)
        response.update({
            "finished": True,
            "auto_submitted": forced,
            "score": graded["score"],
            "band": graded["band"],
            "headline": weekly_test.band_headline(graded["band"]),
            "feedback": graded["feedback"],
            "scored_questions": graded["scored"],
            "celebrate": graded["band"] == "passed",
            "celebration_trigger": is_passing_celebration,
            "next_module_unlocked": is_passing_celebration,
            "weak_concepts_detected": graded.get("weak_concepts", []) if is_passing_celebration else [],
            "failed_concepts": graded.get("failed_concepts", []) if not is_passing_celebration else [],
            "recovery_triggered": not is_passing_celebration,
        })
    else:
        next_question = questions[len(answers)]
        response.update({"finished": False, "next_question": _public_question(next_question)})

    await session.commit()
    _ = profile
    return response
