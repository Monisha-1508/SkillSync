from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.agents import supervisor
from backend.models.database import Base
from backend.utils import seed


DEMO_PERSONAS = [
    "aarav",
    "priya",
    "rohan",
    "sneha",
    "vikram",
]


async def _make_test_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = async_session_factory()

    try:
        await seed.seed_resources(session)
        return session, engine
    except Exception:
        await session.close()
        await engine.dispose()
        raise


@pytest.mark.asyncio
@pytest.mark.parametrize("persona_key", DEMO_PERSONAS)
async def test_profiling_persona_cold_run(persona_key: str):
    from backend.models.database import LearnerProfile

    test_session, engine = await _make_test_session()
    try:
        match persona_key:
            case "aarav":
                profile = LearnerProfile(
                    name="Aarav Mehta",
                    target_role="Software Development Engineer",
                    target_companies=["TCS"],
                    current_skills={"Python": 3, "SQL": 2},
                    weekly_hours=12,
                    deadline_weeks=14,
                    budget_mode="limited",
                    placement_mode="tcs_nqt",
                    background="B.Tech (CSE), Tier-2 college",
                )
            case "priya":
                profile = LearnerProfile(
                    name="Priya Raman",
                    target_role="Capgemini Technology Analyst",
                    target_companies=["Capgemini"],
                    current_skills={"Python": 4, "Data Structures": 3, "SQL": 3},
                    weekly_hours=20,
                    deadline_weeks=10,
                    budget_mode="modest",
                    placement_mode="cap_exceller",
                    background="B.Tech (CSE), Tier-1 college",
                )
            case "rohan":
                profile = LearnerProfile(
                    name="Rohan Verma",
                    target_role="Data Analyst",
                    target_companies=["TCS", "Infosys"],
                    current_skills={"Excel": 3, "SQL": 2},
                    weekly_hours=8,
                    deadline_weeks=20,
                    budget_mode="limited",
                    placement_mode="general",
                    background="MCA graduate",
                )
            case "sneha":
                profile = LearnerProfile(
                    name="Sneha Iyer",
                    target_role="Data Scientist",
                    target_companies=["Infosys"],
                    current_skills={"Statistics": 4, "Python": 2},
                    weekly_hours=17,
                    deadline_weeks=18,
                    budget_mode="modest",
                    placement_mode="infytq",
                    background="M.Sc Statistics, Tier-2 college",
                )
            case "vikram":
                profile = LearnerProfile(
                    name="Vikram Nair",
                    target_role="Full Stack Developer",
                    target_companies=["Wipro"],
                    current_skills={"HTML": 3, "CSS": 3, "JavaScript": 2},
                    weekly_hours=18,
                    deadline_weeks=12,
                    budget_mode="limited",
                    placement_mode="wipro_nlth",
                    background="Diploma-to-B.E. lateral entry",
                )

        test_session.add(profile)
        await test_session.commit()
        await test_session.refresh(profile)

        learner_dict = {
            "id": profile.id,
            "name": profile.name,
            "target_role": profile.target_role,
            "target_companies": profile.target_companies,
            "current_skills": profile.current_skills,
            "weekly_hours": profile.weekly_hours,
            "deadline_weeks": profile.deadline_weeks,
            "budget_mode": profile.budget_mode,
            "placement_mode": profile.placement_mode,
            "background": profile.background,
        }

        state = await supervisor.run_pipeline(
            test_session,
            profile_id=profile.id,
            learner_profile=learner_dict,
            trigger={"kind": "onboarding", "note": "pytest smoke test"},
        )

        assert state is not None, "Pipeline returned None state"
        assert state["profile_id"] == profile.id
        assert state["gap_map"] is not None, "gap_map missing"
        assert len(state["gap_map"]) > 0, "gap_map empty"
        assert state["roadmap_variants"] is not None, "roadmap_variants missing"
        assert len(state["roadmap_variants"]) == 3, "roadmap should have exactly 3 variants"
        assert state["active_milestones"] is not None, "active_milestones missing"
        assert len(state["active_milestones"]) > 0, "active_milestones empty"
        assert state["fsrs_deck"] is not None, "fsrs_deck missing"
        assert len(state["fsrs_deck"]) > 0, "fsrs_deck empty"
        assert state["validation_report"] is not None, "validation_report missing"
        assert "overall_status" in state["validation_report"], "validation_report missing overall_status"
        assert state["validation_report"]["overall_status"] in ("pass", "flag"), \
            f"validation overall_status must be 'pass' or 'flag', got {state['validation_report']['overall_status']!r}"

        for milestone in state["active_milestones"]:
            assert "week" in milestone, "milestone missing 'week'"
            assert "skill_ids" in milestone, "milestone missing 'skill_ids'"
            assert isinstance(milestone["skill_ids"], list), "milestone skill_ids must be a list"

        for card in state["fsrs_deck"]:
            assert "skill_id" in card, "card missing skill_id"
            assert "front" in card, "card missing front"
            assert "back" in card, "card missing back"

        assert len(state["audit_log"]) == 5, \
            f"Pipeline should produce exactly 5 audit entries (one per agent), got {len(state['audit_log'])}"
        for entry in state["audit_log"]:
            assert "agent_name" in entry, "audit entry missing agent_name"
            assert "action" in entry, "audit entry missing action"
            assert "timestamp" in entry, "audit entry missing timestamp"
            assert entry["agent_name"] in (
                "profiling_diagnostician",
                "roadmap_architect",
                "resource_curator",
                "coach_adapter",
                "output_validator",
            ), f"unexpected agent name: {entry['agent_name']!r}"
    finally:
        await test_session.close()
        await engine.dispose()
