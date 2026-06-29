"""Immutable result of scoring an input's structural quality."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StructureScore:
    """Score for how structured a behavioral input is.

    Attributes:
        score: Integer 0-100. Higher means more structured.
        tier: One of "lazy", "partial", "excellent".
        reason: Short human-readable explanation (path + signal summary).
        source: "sampled" (client LLM) or "fallback" (deterministic rubric).
    """

    score: int
    tier: str
    reason: str
    source: str
