"""Tests for the Tiers score-to-duration mapping."""

from boring_mcp.config import BackpressureConfig
from boring_mcp.scoring.tiers import Tiers


def _tiers() -> Tiers:
    return Tiers.from_config(BackpressureConfig.from_env({}))


def test_tier_boundaries():
    t = _tiers()
    assert t.tier_for(39) == "lazy"
    assert t.tier_for(40) == "partial"
    assert t.tier_for(79) == "partial"
    assert t.tier_for(80) == "excellent"


def test_duration_per_tier():
    t = _tiers()
    assert t.duration_for(10) == 30
    assert t.duration_for(50) == 10
    assert t.duration_for(90) == 0


def test_message_excellent_thanks():
    t = _tiers()
    assert "Thanks for being so structured" in t.message_for(90)


def test_message_lazy_is_boring():
    t = _tiers()
    assert "30 seconds" in t.message_for(5)


def test_message_partial():
    t = _tiers()
    assert "Partially structured" in t.message_for(50)
