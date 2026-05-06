"""Backpressure enforcement — ensures agents call `boring` before every action.

This module provides a guard that tracks whether the mandatory backpressure
sleep has been completed before allowing other tool calls. The server rejects
tool invocations that skip backpressure.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

BACKPRESSURE_SECONDS: int = 30


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
        self._boring_in_progress = True
        await asyncio.sleep(BACKPRESSURE_SECONDS)
        self._last_boring_at = time.monotonic()
        self._boring_in_progress = False
        return (
            "You waited 30 seconds. That's the point. "
            "Boring means predictable, reliable, and intentional. "
            "No rushing, no shortcuts."
        )

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
