from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from backend.config import get_settings


def new_id() -> str:
    return uuid.uuid4().hex[:16]


def now() -> datetime:
    return datetime.utcnow()


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(200))
    password_salt: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class LearnerProfile(Base):
    __tablename__ = "learner_profiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    owner_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(120))
    persona_key: Mapped[str | None] = mapped_column(String(40), nullable=True)
    target_role: Mapped[str] = mapped_column(String(80))
    target_companies: Mapped[list] = mapped_column(JSON, default=list)
    current_skills: Mapped[dict] = mapped_column(JSON, default=dict)
    weekly_hours: Mapped[int] = mapped_column(Integer, default=10)
    exam_blackouts: Mapped[list] = mapped_column(JSON, default=list)
    deadline_weeks: Mapped[int] = mapped_column(Integer, default=12)
    budget_mode: Mapped[str] = mapped_column(String(20), default="free")
    placement_mode: Mapped[str] = mapped_column(String(30), default="general")
    background: Mapped[str] = mapped_column(String(40), default="cs")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class GapMap(Base):
    __tablename__ = "gap_maps"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String(32), index=True)
    skill_gaps: Mapped[dict] = mapped_column(JSON, default=dict)
    radar_axes: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[str] = mapped_column(Text, default="")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String(32), index=True)
    selected_variant: Mapped[str] = mapped_column(String(20), default="target")
    variants: Mapped[dict] = mapped_column(JSON, default=dict)
    active_milestones: Mapped[list] = mapped_column(JSON, default=list)
    feasibility_score: Mapped[float] = mapped_column(Float, default=0.0)
    feasibility_explanation: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    pending_replan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    replan_log: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class FsrsCard(Base):
    __tablename__ = "fsrs_cards"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String(32), index=True)
    skill_id: Mapped[str] = mapped_column(String(80))
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    due_date: Mapped[datetime] = mapped_column(DateTime, default=now)
    last_review: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_history: Mapped[list] = mapped_column(JSON, default=list)


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    skill_id: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(400))
    source: Mapped[str] = mapped_column(String(80))
    resource_type: Mapped[str] = mapped_column(String(20))
    difficulty: Mapped[str] = mapped_column(String(20))
    bloom_level: Mapped[int] = mapped_column(Integer, default=2)
    cost: Mapped[str] = mapped_column(String(10), default="free")
    published_year: Mapped[int] = mapped_column(Integer, default=2024)
    authority_score: Mapped[float] = mapped_column(Float, default=0.7)
    recency_score: Mapped[float] = mapped_column(Float, default=0.7)
    community_score: Mapped[float] = mapped_column(Float, default=0.7)
    quality_score: Mapped[float] = mapped_column(Float, default=0.7)
    trust_score: Mapped[float] = mapped_column(Float, default=0.7)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String(32), index=True)
    company: Mapped[str] = mapped_column(String(40))
    round_type: Mapped[str] = mapped_column(String(30))
    questions: Mapped[list] = mapped_column(JSON, default=list)
    answers: Mapped[list] = mapped_column(JSON, default=list)
    rubric_scores: Mapped[list] = mapped_column(JSON, default=list)
    feedback: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class WeeklyTestAttempt(Base):
    __tablename__ = "weekly_test_attempts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String(32), index=True)
    roadmap_id: Mapped[str] = mapped_column(String(32), index=True)
    week: Mapped[int] = mapped_column(Integer)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")  # in_progress | submitted | abandoned
    questions: Mapped[list] = mapped_column(JSON, default=list)
    answers: Mapped[list] = mapped_column(JSON, default=list)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    band: Mapped[str | None] = mapped_column(String(20), nullable=True)  # passed | partial | failed
    feedback: Mapped[str] = mapped_column(Text, default="")
    proctoring_log: Mapped[list] = mapped_column(JSON, default=list)
    time_limit_minutes: Mapped[int] = mapped_column(Integer, default=12)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class RecoveryEvaluation(Base):
    __tablename__ = "recovery_evaluations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String(32), index=True)
    roadmap_id: Mapped[str] = mapped_column(String(32), index=True)
    week: Mapped[int] = mapped_column(Integer)
    cycle: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="diagnosed")  # diagnosed | in_progress | submitted
    diagnosis: Mapped[dict] = mapped_column(JSON, default=dict)
    remediation: Mapped[list] = mapped_column(JSON, default=list)
    questions: Mapped[list] = mapped_column(JSON, default=list)
    answers: Mapped[list] = mapped_column(JSON, default=list)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    feedback: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String(32), index=True)
    agent_name: Mapped[str] = mapped_column(String(60))
    action: Mapped[str] = mapped_column(String(120))
    input_summary: Mapped[str] = mapped_column(Text, default="")
    output_summary: Mapped[str] = mapped_column(Text, default="")
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    trace_id: Mapped[str] = mapped_column(String(40), default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=now)


class ProgressEvent(Base):
    __tablename__ = "progress_events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String(32), index=True)
    roadmap_id: Mapped[str] = mapped_column(String(32), index=True)
    week: Mapped[int] = mapped_column(Integer)
    skill_id: Mapped[str] = mapped_column(String(80), default="")
    event_type: Mapped[str] = mapped_column(String(20))  # completed | partial | missed | quiz
    quiz_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


_settings = get_settings()
engine = create_async_engine(_settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_models() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with SessionLocal() as session:
        yield session
