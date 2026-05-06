"""Unit tests for the /boring tool — backpressure mechanism."""

import asyncio
import unittest.mock

import pytest

from boring_mcp.tools.boring import boring


class TestBoringTool:
    """Tests for the boring backpressure tool."""

    @pytest.mark.asyncio
    async def test_boring_returns_message(self) -> None:
        """Verify boring tool returns the expected message."""
        result = await _boring_fast()
        assert "predictable" in result.lower()

    @pytest.mark.asyncio
    async def test_boring_is_async(self) -> None:
        """Verify the tool is a coroutine."""
        assert asyncio.iscoroutinefunction(boring)


async def _boring_fast() -> str:
    """Fast version of boring for testing — patches the sleep."""
    with unittest.mock.patch(
        "boring_mcp.tools.boring.asyncio.sleep", return_value=None
    ):
        from boring_mcp.tools.boring import boring as boring_fn

        result = await boring_fn()
    return result
