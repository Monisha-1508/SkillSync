from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

from backend.config import get_settings

_initialised = False


def setup_tracing() -> None:
    global _initialised
    if _initialised:
        return
    settings = get_settings()
    provider = TracerProvider(resource=Resource.create({"service.name": settings.otel_service_name}))
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _initialised = True


def get_tracer():
    setup_tracing()
    return trace.get_tracer("skillsync")


def new_trace_id() -> str:
    return uuid.uuid4().hex[:12]


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def traced_step(agent_name: str, action: str, *, input_summary: str = "") -> Iterator[dict]:
    tracer = get_tracer()
    trace_id = new_trace_id()
    started = time.perf_counter()
    record: dict = {"output_summary": "", "confidence": 1.0}
    with tracer.start_as_current_span(f"{agent_name}.{action}") as span:
        span.set_attribute("skillsync.agent", agent_name)
        span.set_attribute("skillsync.action", action)
        span.set_attribute("skillsync.input_summary", input_summary[:200])
        try:
            yield record
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            span.set_attribute("skillsync.duration_ms", duration_ms)
            span.set_attribute("skillsync.confidence", float(record.get("confidence", 1.0)))
            record["agent"] = agent_name
            record["action"] = action
            record["input_summary"] = input_summary
            record["duration_ms"] = duration_ms
            record["trace_id"] = trace_id
            record["timestamp"] = iso_now()
