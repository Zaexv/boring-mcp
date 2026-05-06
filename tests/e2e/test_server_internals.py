"""Tests for server module internals: get_server, main, resources."""

import unittest.mock

import pytest

from boring_mcp.server import create_server, get_server


@pytest.fixture(autouse=True)
def reset_server_singleton():
    """Reset the module-level _server singleton between tests."""
    import boring_mcp.server

    boring_mcp.server._server = None
    yield
    boring_mcp.server._server = None


class TestGetServer:
    """Test the server singleton pattern."""

    def test_creates_server_on_first_call(self) -> None:
        with unittest.mock.patch.dict("os.environ", {"BORING_MCP_CHROMA_PATH": ""}):
            server = get_server()
        assert server is not None
        assert server.name == "Boring MCP"

    def test_returns_same_instance_on_second_call(self) -> None:
        with unittest.mock.patch.dict("os.environ", {"BORING_MCP_CHROMA_PATH": ""}):
            first = get_server()
            second = get_server()
        assert first is second


class TestMainTransport:
    """Test the main() function transport selection."""

    def test_default_transport_is_stdio(self) -> None:
        with (
            unittest.mock.patch.dict(
                "os.environ",
                {"BORING_MCP_CHROMA_PATH": "", "BORING_MCP_TRANSPORT": "stdio"},
            ),
            unittest.mock.patch("boring_mcp.server.FastMCP.run") as mock_run,
        ):
            from boring_mcp.server import main

            main()
        mock_run.assert_called_once_with(transport="stdio")

    def test_sse_transport(self) -> None:
        with (
            unittest.mock.patch.dict(
                "os.environ",
                {"BORING_MCP_CHROMA_PATH": "", "BORING_MCP_TRANSPORT": "sse"},
            ),
            unittest.mock.patch("boring_mcp.server.FastMCP.run") as mock_run,
        ):
            from boring_mcp.server import main

            main()
        mock_run.assert_called_once_with(transport="sse")

    def test_invalid_transport_falls_back_to_stdio(self) -> None:
        with (
            unittest.mock.patch.dict(
                "os.environ",
                {"BORING_MCP_CHROMA_PATH": "", "BORING_MCP_TRANSPORT": "invalid"},
            ),
            unittest.mock.patch("boring_mcp.server.FastMCP.run") as mock_run,
        ):
            from boring_mcp.server import main

            main()
        mock_run.assert_called_once_with(transport="stdio")


class TestResourcesE2E:
    """Test MCP resources through the server."""

    @pytest.fixture
    def server(self):
        with unittest.mock.patch.dict("os.environ", {"BORING_MCP_CHROMA_PATH": ""}):
            srv = create_server()
        return srv

    @pytest.mark.asyncio
    async def test_collection_resource(self, server) -> None:
        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            await server.call_tool("boring", {})
            await server.call_tool(
                "store_behavior",
                {"sentence": "Be polite", "collection": "tone"},
            )
        result = await server.read_resource("behaviors://tone")
        assert "Be polite" in str(result)

    @pytest.mark.asyncio
    async def test_summary_resource(self, server) -> None:
        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            await server.call_tool("boring", {})
            await server.call_tool(
                "store_behavior",
                {"sentence": "x", "collection": "metrics"},
            )
        result = await server.read_resource("behaviors://summary")
        assert "metrics" in str(result)
