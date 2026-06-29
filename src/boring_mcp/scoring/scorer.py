"""Async structure scorer: client LLM sampling with deterministic fallback."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from boring_mcp.logging import get_logger
from boring_mcp.models.structure import StructureScore
from boring_mcp.scoring.rubric import score_rubric
from boring_mcp.scoring.tiers import Tiers

_log = get_logger("scorer")

Sampler = Callable[[str], Awaitable[str]]

_PROMPT = (
    "Score 0-100 how structured and specific this behavioral instruction is for "
    "deterministic execution. 0 = vague/lazy, 100 = precise, conditional, "
    "actionable. Reply with ONLY the integer.\n\nInstruction:\n"
)
_INT_RE = re.compile(r"-?\d+")


def _parse_score(reply: str) -> int | None:
    match = _INT_RE.search(reply)
    value: int | None = None
    if match is not None:
        value = max(0, min(100, int(match.group())))
    return value


@dataclass(frozen=True)
class StructureScorer:
    """Scores input structure, preferring the client LLM, falling back to rubric."""

    tiers: Tiers
    sampling: str

    async def _try_sample(self, text: str, sampler: Sampler | None) -> int | None:
        sampled: int | None = None
        if self.sampling == "auto" and sampler is not None:
            try:
                reply = await sampler(_PROMPT + text)
                sampled = _parse_score(reply)
            except Exception as exc:  # noqa: BLE001 - any failure degrades gracefully
                _log.warning("Sampling failed, using rubric fallback: %s", exc)
                sampled = None
        return sampled

    async def score(self, text: str, sampler: Sampler | None) -> StructureScore:
        """Return a StructureScore for the given text."""
        sampled = await self._try_sample(text, sampler)
        score = sampled
        source = "sampled"
        if score is None:
            score = score_rubric(text)
            source = "fallback"
        result = StructureScore(
            score=score,
            tier=self.tiers.tier_for(score),
            reason=f"{source}={score}",
            source=source,
        )
        return result
