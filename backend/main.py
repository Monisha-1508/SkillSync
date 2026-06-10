from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.models.database import SessionLocal, init_models
from backend.routers import auth, dashboard, explain, interview, profiles, recovery, revision, roadmap, weekly_test
from backend.utils import seed, tracing

settings = get_settings()


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    tracing.setup_tracing()
    await init_models()
    async with SessionLocal() as session:
        await seed.seed_resources(session)
        await seed.seed_demo_account(session)
    yield


app = FastAPI(
    title="SkillSync AI",
    description=(
        "Six small agents - profiling, roadmap architecture, resource curation, "
        "revision coaching, output validation and mock interviewing - turned "
        "into one traced pipeline that takes a learner from intake form to a "
        "placement-ready study plan, with every step shown rather than assumed."
    ),
    version="1.0.0",
    lifespan=_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

for _router in (auth.router, profiles.router, dashboard.router, roadmap.router, revision.router, interview.router, explain.router, weekly_test.router, recovery.router):
    app.include_router(_router)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.otel_service_name, "llm_provider": settings.llm_provider}
