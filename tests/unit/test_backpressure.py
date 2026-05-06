"""Unit tests for the BackpressureGuard — enforcement of mandatory sleep."""

import unittest.mock

import pytest

from boring_mcp.backpressure import BACKPRESSURE_SECONDS, BackpressureGuard


class TestBackpressureGuard:
    """Tests that the guard correctly enforces backpressure rules."""

    def test_initial_state_denies_tools(self) -> None:
        guard = BackpressureGuard()
        assert guard.is_allowed() is False

    @pytest.mark.asyncio
    async def test_after_boring_allows_one_tool(self) -> None:
        guard = BackpressureGuard()
        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            await guard.apply_backpressure()
        assert guard.is_allowed() is True

    @pytest.mark.asyncio
    async def test_after_tool_call_denies_next(self) -> None:
        guard = BackpressureGuard()
        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            await guard.apply_backpressure()
        guard.record_tool_call()
        assert guard.is_allowed() is False

    @pytest.mark.asyncio
    async def test_boring_then_tool_then_boring_then_tool(self) -> None:
        guard = BackpressureGuard()
        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            # First cycle
            await guard.apply_backpressure()
            assert guard.is_allowed() is True
            guard.record_tool_call()
            assert guard.is_allowed() is False

            # Second cycle
            await guard.apply_backpressure()
            assert guard.is_allowed() is True
            guard.record_tool_call()
            assert guard.is_allowed() is False

    @pytest.mark.asyncio
    async def test_apply_backpressure_returns_message(self) -> None:
        guard = BackpressureGuard()
        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            message = await guard.apply_backpressure()
        assert "predictable" in message.lower()

    def test_denial_message_is_clear(self) -> None:
        guard = BackpressureGuard()
        msg = guard.denial_message()
        assert "boring" in msg.lower()
        assert "DENIED" in msg

    def test_backpressure_seconds_is_30(self) -> None:
        assert BACKPRESSURE_SECONDS == 30

    @pytest.mark.asyncio
    async def test_guarded_decorator_denies_without_boring(self) -> None:
        guard = BackpressureGuard()

        @guard.guarded
        async def my_tool() -> str:
            return "success"

        result = await my_tool()
        assert "DENIED" in result

    @pytest.mark.asyncio
    async def test_guarded_decorator_allows_after_boring(self) -> None:
        guard = BackpressureGuard()

        @guard.guarded
        async def my_tool() -> str:
            return "success"

        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            await guard.apply_backpressure()
        result = await my_tool()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_guarded_decorator_denies_second_call(self) -> None:
        guard = BackpressureGuard()

        @guard.guarded
        async def my_tool() -> str:
            return "success"

        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            await guard.apply_backpressure()
        await my_tool()
        result = await my_tool()
        assert "DENIED" in result
