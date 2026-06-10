from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.agents import interviewer
from backend.models.database import InterviewSession
from backend.models.schemas import InterviewAnswerIn, InterviewStartIn, ResumeXrayIn
from backend.routers import deps
from backend.routers.deps import SessionDep

router = APIRouter(tags=["interview"])


_ANSWER_KEY_FIELDS = ("answer", "explainer", "justification")


def _public_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {key: value for key, value in question.items() if key not in _ANSWER_KEY_FIELDS}
        for question in questions
    ]


def _session_summary(round_type: str, answers: list[dict[str, Any]]) -> str:
    count = len(answers)
    average = round(sum(entry["overall_score"] for entry in answers) / count, 3)
    band = (
        "a strong, ready-to-walk-in"
        if average >= 0.75
        else "a developing, worth-another-pass"
        if average >= 0.5
        else "an early-stage, keep-practising"
    )
    label = round_type.replace("_", " ")
    return (
        f"All {count} {label} questions answered, averaging {average:.2f} - "
        f"{band} showing for this round. The notes on each answer above are "
        f"the more useful read; this line is just the headline number."
    )


@router.post("/api/interview/{profile_id}/start", status_code=201)
async def start_interview_session(profile_id: str, payload: InterviewStartIn, session: SessionDep) -> dict[str, Any]:
    profile = await deps.get_profile_or_404(session, profile_id)
    gap_map_row = await deps.get_latest_gap_map(session, profile_id)
    gap_map = gap_map_row.skill_gaps if gap_map_row else None

    result = interviewer.start_session(payload.company, payload.round_type, profile.target_role, gap_map)
    session_row = InterviewSession(
        profile_id=profile_id,
        company=payload.company,
        round_type=payload.round_type,
        questions=result["questions"],
    )
    session.add(session_row)
    session.add(deps.audit_row_from_trace(profile_id, result["trace"]))
    await session.commit()
    await session.refresh(session_row)
    public_qs = _public_questions(result["questions"])
    total_seconds = sum(q.get("time_limit", 90) for q in public_qs)
    return {
        "session_id": session_row.id,
        "company_display": result["company_display"],
        "round_label": result["round_label"],
        "is_drive_curated": result.get("is_drive_curated", False),
        "total_questions": len(public_qs),
        "total_time_seconds": total_seconds,
        "questions": public_qs,
        "fairness_note": result["fairness_note"],
    }


@router.post("/api/interview/{profile_id}/answer")
async def submit_interview_answer(profile_id: str, payload: InterviewAnswerIn, session: SessionDep) -> dict[str, Any]:
    profile = await deps.get_profile_or_404(session, profile_id)
    session_row = await deps.get_or_404(session, InterviewSession, payload.session_id, label="interview session")
    if session_row.profile_id != profile_id:
        raise HTTPException(status_code=404, detail=f"No interview session found for id '{payload.session_id}'.")

    question = next((q for q in session_row.questions if q["id"] == payload.question_id), None)
    if question is None:
        raise HTTPException(status_code=404, detail=f"This session has no question '{payload.question_id}'.")

    already_at = next(
        (index for index, entry in enumerate(session_row.answers) if entry["question_id"] == payload.question_id), None,
    )
    if already_at is not None:
        answer_entry = session_row.answers[already_at]
        rubric_entry = session_row.rubric_scores[already_at]
    else:
        result = interviewer.score_answer(question, payload.answer, profile.target_role, session_row.company)
        answer_entry = {
            "question_id": payload.question_id,
            "prompt": question["prompt"],
            "answer": payload.answer,
            "overall_score": result["overall_score"],
            "feedback": result["feedback"],
        }
        rubric_entry = {"question_id": payload.question_id, "dimensions": result["rubric_dimensions"]}
        session_row.answers = [*session_row.answers, answer_entry]
        session_row.rubric_scores = [*session_row.rubric_scores, rubric_entry]
        session.add(deps.audit_row_from_trace(profile_id, result["trace"]))

    session_complete = len(session_row.answers) == len(session_row.questions)
    post_report = None
    if session_complete:
        if not session_row.feedback:
            session_row.feedback = _session_summary(session_row.round_type, session_row.answers)
        post_report = interviewer.post_interview_report(
            session_row.questions,
            session_row.answers,
            session_row.company,
            session_row.round_type,
        )

    await session.commit()
    return {
        "overall_score": answer_entry["overall_score"],
        "rubric_dimensions": rubric_entry["dimensions"],
        "feedback": answer_entry["feedback"],
        "correct_option": question.get("answer") if question.get("options") else None,
        "justification": question.get("justification") if question.get("justification") else None,
        "session_complete": session_complete,
        "session_summary": session_row.feedback or None,
        "post_interview_report": post_report,
    }


@router.post("/api/interview/{profile_id}/resume-xray")
async def run_resume_xray(profile_id: str, payload: ResumeXrayIn, session: SessionDep) -> dict[str, Any]:
    profile = await deps.get_profile_or_404(session, profile_id)
    result = interviewer.resume_xray(payload.resume_text, profile.target_role)
    session.add(deps.audit_row_from_trace(profile_id, result["trace"]))
    await session.commit()
    return {
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "matched_count": result["matched_count"],
        "missing_count": result["missing_count"],
        "redaction_summary": result["redaction_summary"],
        "narration": result["narration"],
    }
