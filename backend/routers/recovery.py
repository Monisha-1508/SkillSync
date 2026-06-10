from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from backend.agents import learning_recovery
from backend.models.database import RecoveryEvaluation, WeeklyTestAttempt
from backend.models.schemas import RecoveryAnswerIn
from backend.routers import deps
from backend.routers.deps import SessionDep
from backend.utils import skill_graph

router = APIRouter(tags=["learning-recovery"])

_QUESTION_KEY_FIELDS = ("answer", "explainer")


def _public_question(question: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in question.items() if key not in _QUESTION_KEY_FIELDS}


async def _attempts_for_week(session: SessionDep, profile_id: str, week: int) -> list[WeeklyTestAttempt]:
    rows = (await session.execute(
        select(WeeklyTestAttempt)
        .where(WeeklyTestAttempt.profile_id == profile_id, WeeklyTestAttempt.week == week)
        .order_by(WeeklyTestAttempt.attempt_number)
    )).scalars().all()
    return list(rows)


async def _latest_recovery_row(session: SessionDep, profile_id: str, week: int) -> RecoveryEvaluation | None:
    return (await session.execute(
        select(RecoveryEvaluation)
        .where(RecoveryEvaluation.profile_id == profile_id, RecoveryEvaluation.week == week)
        .order_by(RecoveryEvaluation.created_at.desc())
    )).scalars().first()


def _is_stale(row: RecoveryEvaluation | None, streak: list[WeeklyTestAttempt]) -> bool:
    if row is None:
        return True
    if not row.passed:
        return False
    newest = max((a.submitted_at for a in streak if a.submitted_at), default=None)
    return newest is not None and newest > row.created_at


def _topic_skill_ids_from_report(weakness_report: dict[str, Any], role_node_ids: list[str]) -> dict[str, str | None]:
    by_name = {skill_graph.node(skill_id)["name"]: skill_id for skill_id in role_node_ids}
    return {topic["topicName"]: by_name.get(topic["topicName"]) for topic in weakness_report.get("topics", [])}


def _evaluation_summary(row: RecoveryEvaluation) -> dict[str, Any]:
    return {
        "evaluation_id": row.id,
        "week": row.week,
        "status": row.status,
        "cycle": row.cycle,
        "passed": row.passed,
        "score": row.score,
        "weakness_report": row.diagnosis,
        "remediation_plan": row.remediation,
        "feedback": row.feedback,
    }


def _sitting_payload(row: RecoveryEvaluation, *, question_index: int, resumed: bool) -> dict[str, Any]:
    return {
        "evaluation_id": row.id,
        "week": row.week,
        "status": row.status,
        "cycle": row.cycle,
        "total_questions": len(row.questions),
        "weakness_report": row.diagnosis,
        "remediation_plan": row.remediation,
        "pass_criteria": learning_recovery.pass_criteria_text(),
        "weighting_note": learning_recovery.weighting_note_text(),
        "next_question": _public_question(row.questions[question_index - 1]),
        "question_index": question_index,
        "resumed": resumed,
    }


@router.get("/api/recovery/{profile_id}/{week}/status")
async def get_recovery_status(profile_id: str, week: int, session: SessionDep) -> dict[str, Any]:
    await deps.get_profile_or_404(session, profile_id)
    attempts = await _attempts_for_week(session, profile_id, week)
    streak = learning_recovery.failing_streak(attempts)
    triggered = learning_recovery.eligible_for_recovery(attempts)
    row = await _latest_recovery_row(session, profile_id, week)

    if row is None or _is_stale(row, streak):
        return {"triggered": triggered, "active": False}

    return {"triggered": True, "active": True, **_evaluation_summary(row)}


@router.post("/api/recovery/{profile_id}/{week}/start", status_code=201)
async def start_recovery(profile_id: str, week: int, session: SessionDep) -> dict[str, Any]:
    profile = await deps.get_profile_or_404(session, profile_id)
    roadmap_row = await deps.get_latest_roadmap_or_404(session, profile_id)
    attempts = await _attempts_for_week(session, profile_id, week)

    if not learning_recovery.eligible_for_recovery(attempts):
        raise HTTPException(
            status_code=409,
            detail=(
                "This path only opens once three sittings of this week's checkpoint have landed under "
                f"{round(learning_recovery.RECOVERY_FLOOR * 100)} percent in a row - that has not happened "
                "here yet, so a regular retake is still the right next step."
            ),
        )

    streak = learning_recovery.failing_streak(attempts)
    role_node_ids = skill_graph.role_node_ids(profile.target_role)
    row = await _latest_recovery_row(session, profile_id, week)

    if row is None or _is_stale(row, streak):
        row = await _build_fresh_evaluation(session, profile_id, roadmap_row.id, week, streak, role_node_ids)
        await session.commit()
        await session.refresh(row)
        return _sitting_payload(row, question_index=1, resumed=False)

    if row.passed:
        return {
            **_evaluation_summary(row),
            "message": "This recovery check is already cleared - the next checkpoint attempt is open from the board above.",
        }

    if row.status == "in_progress" and row.questions:
        answered = len(row.answers)
        if answered < len(row.questions):
            return _sitting_payload(row, question_index=answered + 1, resumed=True)
        await _finish_sitting(session, row)
        await session.commit()
        await session.refresh(row)
        if row.passed:
            return {**_evaluation_summary(row), "message": "That sitting had already answered every question - it has been graded and cleared. Refresh to continue."}
        row = await _regenerate_cycle(session, profile_id, row, role_node_ids)
        await session.commit()
        await session.refresh(row)
        return _sitting_payload(row, question_index=1, resumed=False)

    row = await _regenerate_cycle(session, profile_id, row, role_node_ids)
    await session.commit()
    await session.refresh(row)
    return _sitting_payload(row, question_index=1, resumed=False)


async def _build_fresh_evaluation(
    session: SessionDep, profile_id: str, roadmap_id: str, week: int,
    streak: list[WeeklyTestAttempt], role_node_ids: list[str],
) -> RecoveryEvaluation:
    diagnosis = learning_recovery.run_diagnosis(profile_id=profile_id, week=week, attempts=streak)
    remediation = learning_recovery.run_remediation(
        profile_id=profile_id, week=week, weakness_report=diagnosis["weakness_report"],
        topic_skill_ids=diagnosis["topic_skill_ids"], role_node_ids=role_node_ids,
    )
    micro = learning_recovery.run_micro_eval_generation(
        profile_id=profile_id, week=week, cycle=1, weakness_report=diagnosis["weakness_report"],
        topic_skill_ids=diagnosis["topic_skill_ids"], role_node_ids=role_node_ids,
    )
    row = RecoveryEvaluation(
        profile_id=profile_id, roadmap_id=roadmap_id, week=week, cycle=1, status="in_progress",
        diagnosis=diagnosis["weakness_report"], remediation=remediation["plan"], questions=micro["questions"],
    )
    session.add(row)
    session.add(deps.audit_row_from_trace(profile_id, diagnosis["trace"]))
    session.add(deps.audit_row_from_trace(profile_id, remediation["trace"]))
    session.add(deps.audit_row_from_trace(profile_id, micro["trace"]))
    return row


async def _regenerate_cycle(
    session: SessionDep, profile_id: str, row: RecoveryEvaluation, role_node_ids: list[str],
) -> RecoveryEvaluation:
    topic_skill_ids = _topic_skill_ids_from_report(row.diagnosis, role_node_ids)
    next_cycle = row.cycle + 1
    micro = learning_recovery.run_micro_eval_generation(
        profile_id=profile_id, week=row.week, cycle=next_cycle, weakness_report=row.diagnosis,
        topic_skill_ids=topic_skill_ids, role_node_ids=role_node_ids,
    )
    row.cycle = next_cycle
    row.status = "in_progress"
    row.questions = micro["questions"]
    row.answers = []
    row.score = None
    row.passed = False
    row.feedback = ""
    row.submitted_at = None
    session.add(deps.audit_row_from_trace(profile_id, micro["trace"]))
    return row


async def _finish_sitting(session: SessionDep, row: RecoveryEvaluation) -> dict[str, Any]:
    graded = learning_recovery.run_micro_grading(
        profile_id=row.profile_id, week=row.week, cycle=row.cycle, questions=row.questions, answers=row.answers,
    )
    row.status = "submitted"
    row.score = graded["score"]
    row.passed = graded["passed"]
    row.feedback = graded["feedback"]
    row.submitted_at = datetime.utcnow()
    session.add(deps.audit_row_from_trace(row.profile_id, graded["trace"]))
    return graded


@router.post("/api/recovery/{profile_id}/answer")
async def submit_recovery_answer(profile_id: str, payload: RecoveryAnswerIn, session: SessionDep) -> dict[str, Any]:
    await deps.get_profile_or_404(session, profile_id)
    row = await deps.get_or_404(session, RecoveryEvaluation, payload.evaluation_id, label="recovery evaluation")
    if row.profile_id != profile_id:
        raise HTTPException(status_code=404, detail=f"No recovery evaluation found for id '{payload.evaluation_id}'.")
    if row.status != "in_progress":
        raise HTTPException(status_code=409, detail="This recovery check is already finished - its result will not change.")

    questions = row.questions
    answers = list(row.answers)
    expected = questions[len(answers)] if len(answers) < len(questions) else None
    if expected is None or expected["id"] != payload.question_id:
        raise HTTPException(
            status_code=400,
            detail="That is not the next question in this check - they lock in one at a time, in order, same as the checkpoint itself.",
        )

    answers.append({"question_id": payload.question_id, "choice": payload.choice, "locked_at": datetime.utcnow().isoformat()})
    row.answers = answers

    finished = len(answers) == len(questions)
    response: dict[str, Any] = {"question_index": len(answers), "total_questions": len(questions)}

    if finished:
        graded = await _finish_sitting(session, row)
        response.update({
            "finished": True,
            "score": row.score,
            "passed": row.passed,
            "feedback": row.feedback,
            "scored_questions": graded["scored"],
            "celebrate": row.passed,
        })
    else:
        response.update({"finished": False, "next_question": _public_question(questions[len(answers)])})

    await session.commit()
    return response
