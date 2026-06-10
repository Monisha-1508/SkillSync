from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "simulated"
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"

    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-05-01-preview"
    azure_openai_chat_deployment: str = "gpt-4o"
    azure_openai_embed_deployment: str = "text-embedding-3-small"

    database_url: str = f"sqlite+aiosqlite:///{(DATA_DIR / 'skillsync.db').as_posix()}"
    secret_key: str = "dev-only-change-before-any-real-deployment"
    environment: str = "development"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    otel_traces_exporter: str = "console"
    otel_exporter_otlp_endpoint: str = ""
    otel_service_name: str = "skillsync-ai"

    @property
    def using_live_llm(self) -> bool:
        return self.llm_provider in ("openai", "azure_openai") and bool(
            self.openai_api_key or self.azure_openai_api_key
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
