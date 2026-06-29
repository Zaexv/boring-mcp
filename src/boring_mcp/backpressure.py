"""Backpressure enforcement — ensures agents call `boring` before every action.

This module provides a guard that tracks whether the mandatory backpressure
sleep has been completed before allowing other tool calls. The server rejects
tool invocations that skip backpressure.
"""

from __future__ import annotations

import asyncio
import functools
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any, ParamSpec, TypeVar

from boring_mcp.logging import get_logger
from boring_mcp.scoring.scorer import Sampler, StructureScorer

_log = get_logger("backpressure")

BACKPRESSURE_SECONDS: int = 30

P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class BackpressureGuard:
    """Tracks backpressure state and enforces the mandatory sleep rule.

    The guard maintains a timestamp of the last completed `boring` call.
    Other tools must check `is_allowed()` before executing. If backpressure
    has not been applied since the last tool call, the action is denied.
    """

    _last_boring_at: float = 0.0
    _last_tool_at: float = 0.0
    _boring_in_progress: bool = False

    async def apply_backpressure(self) -> str:
        """Execute the mandatory 30-second sleep and record completion."""
        _log.info("Backpressure started (%ds sleep)", BACKPRESSURE_SECONDS)
        self._boring_in_progress = True
        await asyncio.sleep(BACKPRESSURE_SECONDS)
        self._last_boring_at = time.monotonic()
        self._boring_in_progress = False
        _log.info("Backpressure complete — tools unlocked")
        return (
            "You waited 30 seconds. That's the point. "
            "Boring means predictable, reliable, and intentional. "
            "No rushing, no shortcuts."
        )

    async def scored_backpressure(
        self, text: str, scorer: StructureScorer, sampler: Sampler | None
    ) -> str:
        """Score input, sleep by tier, return the tier message.

        Replaces the fixed 30s gate for text-bearing tools: the sleep duration is
        derived from how structured `text` is. Highly structured input sleeps 0s
        and is applied directly. The scored sleep itself is the backpressure, so
        no prior `boring` call is required.

        This path is self-contained: it does NOT touch the admin-gate state
        (`_last_boring_at` / `_last_tool_at`). A scored call therefore neither
        requires nor satisfies the `boring` gate that admin tools still enforce.
        """
        result = await scorer.score(text, sampler)
        seconds = scorer.tiers.duration_for(result.score)
        _log.info(
            "Scored backpressure: score=%d tier=%s source=%s sleep=%ds",
            result.score,
            result.tier,
            result.source,
            seconds,
        )
        await asyncio.sleep(seconds)
        return scorer.tiers.message_for(result.score)

    def is_allowed(self) -> bool:
        """Check if backpressure was applied since last tool."""
        allowed = (
            self._last_boring_at > 0.0 and self._last_boring_at > self._last_tool_at
        )
        return allowed

    def record_tool_call(self) -> None:
        """Record that a non-boring tool was just invoked."""
        self._last_tool_at = time.monotonic()

    def denial_message(self) -> str:
        """Message returned when a tool call is denied for missing backpressure."""
        return (
            "⛔ DENIED: You must call the `boring` tool before every other tool call. "
            "This is mandatory backpressure. Call `boring` first, then retry."
        )

    def guarded(
        self, fn: Callable[P, Coroutine[Any, Any, str]]
    ) -> Callable[P, Coroutine[Any, Any, str]]:
        """Decorator that wraps a tool handler with backpressure enforcement.

        If the guard has not been satisfied, returns a denial message.
        Otherwise, records the tool call and executes the handler.
        """

        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> str:
            result = self.denial_message()
            if self.is_allowed():
                self.record_tool_call()
                _log.info("Tool '%s' authorized — executing", fn.__name__)
                result = await fn(*args, **kwargs)
            else:
                _log.warning("Tool '%s' DENIED — missing backpressure", fn.__name__)
            return result

        return wrapper
