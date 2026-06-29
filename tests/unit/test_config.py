"""Tests for BackpressureConfig env loading."""

from boring_mcp.config import BackpressureConfig


def test_defaults_when_env_empty():
    cfg = BackpressureConfig.from_env({})
    assert cfg.lazy_max == 39
    assert cfg.partial_max == 79
    assert cfg.sleep_lazy == 30
    assert cfg.sleep_partial == 10
    assert cfg.sleep_excellent == 0
    assert cfg.sampling == "auto"


def test_env_overrides_applied():
    cfg = BackpressureConfig.from_env(
        {
            "BORING_MCP_TIER_LAZY_MAX": "20",
            "BORING_MCP_SLEEP_PARTIAL": "5",
            "BORING_MCP_SAMPLING": "off",
        }
    )
    assert cfg.lazy_max == 20
    assert cfg.sleep_partial == 5
    assert cfg.sampling == "off"


def test_malformed_int_falls_back_to_default():
    cfg = BackpressureConfig.from_env({"BORING_MCP_SLEEP_LAZY": "not-a-number"})
    assert cfg.sleep_lazy == 30


def test_unknown_sampling_value_falls_back_to_auto():
    cfg = BackpressureConfig.from_env({"BORING_MCP_SAMPLING": "weird"})
    assert cfg.sampling == "auto"
