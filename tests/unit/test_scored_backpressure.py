"""Tests for BackpressureGuard.scored_backpressure."""

import pytest

import boring_mcp.backpressure as bp
from boring_mcp.backpressure import BackpressureGuard
from boring_mcp.config import BackpressureConfig
from boring_mcp.scoring.scorer import StructureScorer
from boring_mcp.scoring.tiers import Tiers

pytestmark = pytest.mark.asyncio


def _scorer() -> StructureScorer:
    return StructureScorer(
        tiers=Tiers.from_config(BackpressureConfig.from_env({})), sampling="auto"
    )


@pytest.fixture
def captured_sleep(monkeypatch):
    calls: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        calls.append(seconds)

    monkeypatch.setattr(bp.asyncio, "sleep", fake_sleep)
    return calls


async def test_excellent_input_no_sleep_and_thanks(captured_sleep):
    guard = BackpressureGuard()

    async def sampler(_p: str) -> str:
        return "95"

    msg = await guard.scored_backpressure("when X do Y", _scorer(), sampler)
    assert captured_sleep == [0]
    assert "Thanks for being so structured" in msg


async def test_lazy_input_full_sleep(captured_sleep):
    guard = BackpressureGuard()

    async def sampler(_p: str) -> str:
        return "5"

    await guard.scored_backpressure("eh", _scorer(), sampler)
    assert captured_sleep == [30]


async def test_partial_input_partial_sleep(captured_sleep):
    guard = BackpressureGuard()

    async def sampler(_p: str) -> str:
        return "60"

    await guard.scored_backpressure("respond with code", _scorer(), sampler)
    assert captured_sleep == [10]


async def test_scored_backpressure_marks_allowed(captured_sleep):
    guard = BackpressureGuard()

    async def sampler(_p: str) -> str:
        return "95"

    await guard.scored_backpressure("when X do Y", _scorer(), sampler)
    assert guard.is_allowed() is True
