"""Backpressure tier configuration, loaded from the environment."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

_DEFAULTS: dict[str, int] = {
    "BORING_MCP_TIER_LAZY_MAX": 39,
    "BORING_MCP_TIER_PARTIAL_MAX": 79,
    "BORING_MCP_SLEEP_LAZY": 30,
    "BORING_MCP_SLEEP_PARTIAL": 10,
    "BORING_MCP_SLEEP_EXCELLENT": 0,
}


def _int_env(env: Mapping[str, str], key: str) -> int:
    raw = env.get(key)
    value = _DEFAULTS[key]
    if raw is not None and raw.lstrip("-").isdigit():
        value = int(raw)
    return value


def _sampling_env(env: Mapping[str, str]) -> str:
    raw = env.get("BORING_MCP_SAMPLING", "auto")
    value = raw if raw in ("auto", "off") else "auto"
    return value


@dataclass(frozen=True)
class BackpressureConfig:
    """Tier thresholds and sleep durations for structure-gated backpressure."""

    lazy_max: int
    partial_max: int
    sleep_lazy: int
    sleep_partial: int
    sleep_excellent: int
    sampling: str

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> BackpressureConfig:
        """Build config from an environment mapping, using defaults for gaps."""
        cfg = cls(
            lazy_max=_int_env(env, "BORING_MCP_TIER_LAZY_MAX"),
            partial_max=_int_env(env, "BORING_MCP_TIER_PARTIAL_MAX"),
            sleep_lazy=_int_env(env, "BORING_MCP_SLEEP_LAZY"),
            sleep_partial=_int_env(env, "BORING_MCP_SLEEP_PARTIAL"),
            sleep_excellent=_int_env(env, "BORING_MCP_SLEEP_EXCELLENT"),
            sampling=_sampling_env(env),
        )
        return cfg
