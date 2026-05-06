"""The /boring tool — backpressure demonstration.

When invoked, this tool sleeps for 30 seconds before responding.
This demonstrates intentional backpressure: the agent must wait,
preventing rapid-fire tool calls and encouraging deliberate usage.

NOTE: In the server, backpressure is enforced via BackpressureGuard.
This module provides the standalone coroutine for use in tests.
"""

from __future__ import annotations

import asyncio

from boring_mcp.backpressure import BACKPRESSURE_SECONDS


async def boring() -> str:
    """Sleep for 30 seconds. This is intentional backpressure.

    The agent must wait patiently. Boring is good. Boring is predictable.
    """
    await asyncio.sleep(BACKPRESSURE_SECONDS)
    return (
        "You waited 30 seconds. That's the point. "
        "Boring means predictable, reliable, and intentional. "
        "No rushing, no shortcuts."
    )
