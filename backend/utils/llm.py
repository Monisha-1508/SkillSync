from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from backend.config import Settings, get_settings
from backend.utils.narration import build_prompt, render_template


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    tokens_used: int = 0
    extra: dict = field(default_factory=dict)


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def narrate(self, kind: str, context: dict) -> LLMResult: ...


class SimulatedProvider(LLMProvider):
    name = "simulated"

    def narrate(self, kind: str, context: dict) -> LLMResult:
        text = render_template(kind, context)
        return LLMResult(text=text, provider=self.name, tokens_used=0)


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, settings: Settings):
        from openai import OpenAI

        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_chat_model

    def narrate(self, kind: str, context: dict) -> LLMResult:
        system, user = build_prompt(kind, context)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.4,
            max_tokens=320,
        )
        text = (response.choices[0].message.content or "").strip()
        used = response.usage.total_tokens if response.usage else 0
        return LLMResult(text=text, provider=self.name, tokens_used=used)


class AzureOpenAIProvider(LLMProvider):
    name = "azure_openai"

    def __init__(self, settings: Settings):
        from openai import AzureOpenAI

        self._client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )
        self._deployment = settings.azure_openai_chat_deployment

    def narrate(self, kind: str, context: dict) -> LLMResult:
        system, user = build_prompt(kind, context)
        response = self._client.chat.completions.create(
            model=self._deployment,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.4,
            max_tokens=320,
        )
        text = (response.choices[0].message.content or "").strip()
        used = response.usage.total_tokens if response.usage else 0
        return LLMResult(text=text, provider=self.name, tokens_used=used)


_provider_singleton: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _provider_singleton
    if _provider_singleton is not None:
        return _provider_singleton

    settings = get_settings()
    provider: LLMProvider
    try:
        if settings.llm_provider == "openai" and settings.openai_api_key:
            provider = OpenAIProvider(settings)
        elif settings.llm_provider == "azure_openai" and settings.azure_openai_api_key:
            provider = AzureOpenAIProvider(settings)
        else:
            provider = SimulatedProvider()
    except Exception:
        provider = SimulatedProvider()

    _provider_singleton = provider
    return provider


def reset_provider_cache() -> None:
    global _provider_singleton
    _provider_singleton = None
