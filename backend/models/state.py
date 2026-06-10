from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class TraceEvent(TypedDict):
    timestamp: str
    agent: str
    action: str
    input_summary: str
    output_summary: str
    duration_ms: int
    confidence: float
    trace_id: str


class SkillSyncState(TypedDict, total=False):
    profile_id: str
    learner_profile: dict[str, Any]
    gap_map: dict[str, Any]
    gap_summary: str
    gap_confidence: float
    radar_axes: list[dict[str, Any]]
    roadmap_variants: dict[str, Any]
    resource_picks: dict[str, Any]
    selected_variant: str
    active_milestones: list[dict[str, Any]]
    feasibility_score: float
    feasibility_explanation: str
    fsrs_deck: list[dict[str, Any]]
    interview_sessions: list[dict[str, Any]]
    engagement_signals: dict[str, Any]
    audit_log: Annotated[list[dict[str, Any]], operator.add]
    trace_events: Annotated[list[TraceEvent], operator.add]
    pending_replan: dict[str, Any] | None
    validation_report: dict[str, Any]
    trigger: dict[str, Any]
