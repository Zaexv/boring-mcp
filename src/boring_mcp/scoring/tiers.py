"""Maps a structure score to a backpressure tier, duration, and message."""

from __future__ import annotations

from dataclasses import dataclass

from boring_mcp.config import BackpressureConfig

_LAZY_MESSAGE = (
    "You waited 30 seconds. That's the point. "
    "Boring means predictable, reliable, and intentional. No rushing, no shortcuts."
)
_PARTIAL_MESSAGE = "Partially structured — brief pause before applying."
_EXCELLENT_MESSAGE = "Thanks for being so structured — applying changes directly."


@dataclass(frozen=True)
class Tiers:
    """Pure score-to-tier mapping built from configuration."""

    lazy_max: int
    partial_max: int
    sleep_lazy: int
    sleep_partial: int
    sleep_excellent: int

    @classmethod
    def from_config(cls, cfg: BackpressureConfig) -> Tiers:
        """Construct tier mapping from a BackpressureConfig."""
        tiers = cls(
            lazy_max=cfg.lazy_max,
            partial_max=cfg.partial_max,
            sleep_lazy=cfg.sleep_lazy,
            sleep_partial=cfg.sleep_partial,
            sleep_excellent=cfg.sleep_excellent,
        )
        return tiers

    def tier_for(self, score: int) -> str:
        """Return the tier name for a score."""
        tier = "excellent"
        if score <= self.lazy_max:
            tier = "lazy"
        elif score <= self.partial_max:
            tier = "partial"
        return tier

    def duration_for(self, score: int) -> int:
        """Return the sleep seconds for a score."""
        durations = {
            "lazy": self.sleep_lazy,
            "partial": self.sleep_partial,
            "excellent": self.sleep_excellent,
        }
        return durations[self.tier_for(score)]

    def message_for(self, score: int) -> str:
        """Return the user-facing message for a score."""
        messages = {
            "lazy": _LAZY_MESSAGE,
            "partial": _PARTIAL_MESSAGE,
            "excellent": _EXCELLENT_MESSAGE,
        }
        return messages[self.tier_for(score)]
