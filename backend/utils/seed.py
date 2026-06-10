from __future__ import annotations

import json
from functools import lru_cache

from sqlalchemy import func, select

from backend.config import DATA_DIR
from backend.models.database import Resource, User
from backend.utils import auth

DEMO_EMAIL = "demo@skillsync.ai"
DEMO_PASSWORD = "skillsync-demo"
DEMO_NAME = "Demo Learner"


def _read_json(filename: str) -> dict:
    path = DATA_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_company_profiles() -> dict:
    return _read_json("company_profiles.json")


@lru_cache(maxsize=1)
def load_personas() -> dict:
    return _read_json("demo_personas.json")


@lru_cache(maxsize=1)
def load_skill_graph_snapshot() -> dict:
    return _read_json("skill_graph.json")


@lru_cache(maxsize=1)
def _resource_seed_rows() -> list[dict]:
    return _read_json("resources_seed.json")["resources"]


async def seed_resources(session) -> int:
    rows = _resource_seed_rows()

    existing_pairs = set(
        await session.execute(
            select(Resource.skill_id, Resource.title)
        )
    )

    new_rows = [
        r for r in rows
        if (r["skill_id"], r["title"]) not in existing_pairs
    ]
    if not new_rows:
        return 0

    session.add_all(
        Resource(
            skill_id=row["skill_id"],
            title=row["title"],
            url=row["url"],
            source=row["source"],
            resource_type=row["resource_type"],
            difficulty=row["difficulty"],
            bloom_level=row["bloom_level"],
            cost=row["cost"],
            published_year=row["published_year"],
            authority_score=row["authority_score"],
            recency_score=row["recency_score"],
            community_score=row["community_score"],
            quality_score=row["quality_score"],
            trust_score=row["trust_score"],
        )
        for row in new_rows
    )
    await session.commit()
    return len(new_rows)


async def seed_demo_account(session) -> bool:
    existing = (await session.execute(select(User).where(User.email == DEMO_EMAIL))).scalar_one_or_none()
    if existing is not None:
        return False

    password_hash, salt = auth.hash_password(DEMO_PASSWORD)
    session.add(User(name=DEMO_NAME, email=DEMO_EMAIL, password_hash=password_hash, password_salt=salt))
    await session.commit()
    return True
