from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s-]?)?\d{10}\b|\b\d{3}[\s-]\d{3}[\s-]\d{4}\b")
_URL_RE = re.compile(r"https?://\S+")

_OVERCLAIM_PHRASES = (
    "guaranteed", "guarantee", "100% chance", "always works", "never fails",
    "will definitely", "will certainly", "promise you", "no doubt you will",
    "perfect score", "every single time",
)


def confidence_from_signal_mix(direct_n: int, inferred_n: int, total_n: int) -> float:
    if total_n <= 0:
        return 0.0
    weighted = direct_n + 0.5 * inferred_n
    coverage = weighted / total_n
    return round(min(0.97, max(0.15, coverage)), 3)


def disclosure_for(confidence: float) -> dict:
    if confidence >= 0.7:
        label, message = "high confidence", \
            "Based mostly on what you told us directly - this should feel close to the mark."
    elif confidence >= 0.45:
        label, message = "moderate confidence", \
            "Part direct signal, part reasonable inference from the skill graph - useful as a strong starting point."
    else:
        label, message = "early read", \
            "Based on limited signal so far - treat this as a first draft that will sharpen as you log progress."
    return {"confidence": confidence, "label": label, "message": message}


def redact_pii(text: str) -> tuple[str, list[str]]:
    removed: list[str] = []
    out = text

    def _swap(pattern: re.Pattern, label: str, value: str) -> str:
        nonlocal out
        matches = pattern.findall(out)
        if matches:
            removed.append(f"{len(matches)} {label}{'s' if len(matches) != 1 else ''}")
            out = pattern.sub(value, out)
        return out

    _swap(_EMAIL_RE, "email address", "[redacted email]")
    _swap(_PHONE_RE, "phone number", "[redacted phone]")
    _swap(_URL_RE, "link", "[redacted link]")
    return out, removed


def screen_overclaims(text: str) -> list[str]:
    lowered = text.lower()
    return [phrase for phrase in _OVERCLAIM_PHRASES if phrase in lowered]


def soften_overclaims(text: str) -> str:
    out = text
    for phrase in _OVERCLAIM_PHRASES:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        out = pattern.sub("a strong chance of", out) if "guarant" in phrase or "promise" in phrase else pattern.sub("often", out)
    return out


def fairness_caveat(confidence_label: str, source_note: str) -> str | None:
    if confidence_label == "officially published":
        return None
    return f"Shown as indicative, not an official figure: {source_note}"
