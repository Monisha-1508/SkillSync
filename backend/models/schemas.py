from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class OnboardingRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    target_role: str
    target_companies: list[str] = Field(default_factory=list)
    current_skills: dict[str, int] = Field(default_factory=dict, description="skill name -> self rating 1-5")
    weekly_hours: int = Field(ge=1, le=80, default=10)
    deadline_weeks: int = Field(ge=1, le=104, default=12)
    budget_mode: Literal["free", "paid"] = "free"
    placement_mode: Literal["tcs_nqt", "infytq", "wipro_nlth", "cap_exceller", "general"] = "general"
    background: Literal["cs", "non_cs", "diploma", "other"] = "cs"
    exam_blackouts: list[dict[str, Any]] = Field(default_factory=list)


class ProfileOut(BaseModel):
    id: str
    owner_id: str | None = None
    name: str
    persona_key: str | None
    target_role: str
    target_companies: list[str]
    current_skills: dict[str, int]
    weekly_hours: int
    deadline_weeks: int
    budget_mode: str
    placement_mode: str
    background: str

    model_config = {"from_attributes": True}


class MyPlanOut(BaseModel):
    id: str
    name: str
    persona_key: str | None
    target_role: str
    placement_mode: str
    weekly_hours: int
    deadline_weeks: int
    created_at: str
    has_roadmap: bool
    selected_variant: str | None = None
    feasibility_score: float | None = None
    pending_replan: bool = False
    total_weeks: int = 0
    completed_weeks: int = 0
    progress_percent: int = 0


class RoadmapVariantSelect(BaseModel):
    variant: Literal["safe", "target", "stretch"]


class ProgressEventIn(BaseModel):
    roadmap_id: str
    week: int
    skill_id: str = ""
    event_type: Literal["completed", "partial", "missed", "quiz"]
    quiz_score: float | None = Field(default=None, ge=0, le=1)
    notes: str = ""


class ReplanProposeIn(BaseModel):
    missed_week: int = Field(ge=1, description="the plan week the learner logged as missed")


class ReplanDecision(BaseModel):
    decision: Literal["accept", "reject"]


class ReflowOut(BaseModel):
    active_milestones: list[dict[str, Any]]
    deadline_breach: bool
    compression_applied: bool
    compression_detail: str | None
    reflow_summary: str
    breach_message: str | None
    version: int


class FsrsReviewIn(BaseModel):
    card_id: str
    rating: int = Field(ge=1, le=4, description="FSRS rating: 1=Again 2=Hard 3=Good 4=Easy")


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=160)
    password: str = Field(min_length=8, max_length=200)


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str

    model_config = {"from_attributes": True}


class AuthOut(BaseModel):
    token: str
    user: UserOut


class InterviewStartIn(BaseModel):
    company: Literal["cap_exceller", "tcs_nqt", "infytq", "wipro_nlth", "accenture_asset", "cognizant_genc"]
    round_type: Literal["aptitude", "technical", "behavioral", "hr"]


class InterviewAnswerIn(BaseModel):
    session_id: str
    question_id: str
    answer: str


class WeeklyTestStartIn(BaseModel):
    week: int = Field(ge=1)


class WeeklyTestAnswerIn(BaseModel):
    attempt_id: str
    question_id: str
    choice: str
    proctor_events: list[dict[str, Any]] = Field(default_factory=list)


class RecoveryAnswerIn(BaseModel):
    evaluation_id: str
    question_id: str
    choice: str


class ResumeXrayIn(BaseModel):
    resume_text: str = Field(min_length=20)


class ExplainSkillIn(BaseModel):
    skill_id: str


class ExplainResourceIn(BaseModel):
    resource_id: str


class ExplainReplanIn(BaseModel):
    roadmap_id: str
