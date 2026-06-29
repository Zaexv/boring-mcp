"""Tests for StructureScorer (sampling + rubric fallback)."""

import pytest

from boring_mcp.config import BackpressureConfig
from boring_mcp.scoring.scorer import StructureScorer
from boring_mcp.scoring.tiers import Tiers

pytestmark = pytest.mark.asyncio


def _scorer(sampling: str = "auto") -> StructureScorer:
    return StructureScorer(
        tiers=Tiers.from_config(BackpressureConfig.from_env({})), sampling=sampling
    )


async def test_uses_sampler_when_available():
    async def sampler(_prompt: str) -> str:
        return "The score is 85 out of 100"

    result = await _scorer().score("when X do Y", sampler)
    assert result.score == 85
    assert result.source == "sampled"
    assert result.tier == "excellent"


async def test_garbage_reply_falls_back():
    async def sampler(_prompt: str) -> str:
        return "no number here"

    result = await _scorer().score("be nice", sampler)
    assert result.source == "fallback"


async def test_sampler_exception_falls_back():
    async def sampler(_prompt: str) -> str:
        raise RuntimeError("sampling not supported")

    result = await _scorer().score("be nice", sampler)
    assert result.source == "fallback"


async def test_none_sampler_falls_back():
    result = await _scorer().score("be nice", None)
    assert result.source == "fallback"


async def test_sampling_off_ignores_sampler():
    async def sampler(_prompt: str) -> str:
        return "100"

    result = await _scorer(sampling="off").score("be nice", sampler)
    assert result.source == "fallback"


async def test_sampled_score_is_clamped():
    async def sampler(_prompt: str) -> str:
        return "250"

    result = await _scorer().score("when X do Y", sampler)
    assert result.score == 100
