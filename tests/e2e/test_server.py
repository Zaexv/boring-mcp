"""End-to-end tests for the MCP server — exercises the full tool pipeline."""

import json
import unittest.mock

import pytest

from boring_mcp.server import create_server


def _text(result) -> str:  # type: ignore[no-untyped-def]
    """Extract text from a FastMCP ToolResult."""
    return result.content[0].text


def _json(result):  # type: ignore[no-untyped-def]
    """Parse the JSON payload from a tool result.

    Scored tools (store/query) prefix a tier message line before the JSON; the
    JSON is always the last line. Admin tools return bare JSON.
    """
    return json.loads(_text(result).splitlines()[-1])


@pytest.fixture
def server():
    """Create a server instance with in-memory ChromaDB for testing."""
    with unittest.mock.patch.dict("os.environ", {"BORING_MCP_CHROMA_PATH": ""}):
        srv = create_server()
    return srv


class TestBoringToolE2E:
    """Test the boring backpressure tool via the server."""

    @pytest.mark.asyncio
    async def test_boring_tool_returns_message(self, server) -> None:
        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            result = await server.call_tool("boring", {})
        assert "predictable" in _text(result).lower()

    @pytest.mark.asyncio
    async def test_store_scored_without_prior_boring(self, server) -> None:
        # store_behavior is structure-gated: no prior boring() required.
        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            result = await server.call_tool(
                "store_behavior",
                {"sentence": "Be kind", "collection": "tone"},
            )
        data = _json(result)
        assert data["status"] == "stored"

    @pytest.mark.asyncio
    async def test_repeated_stores_without_boring_all_succeed(self, server) -> None:
        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            await server.call_tool(
                "store_behavior",
                {"sentence": "first", "collection": "tone"},
            )
            result = await server.call_tool(
                "store_behavior",
                {"sentence": "second", "collection": "tone"},
            )
        data = _json(result)
        assert data["status"] == "stored"


class TestQueryToolE2E:
    """Test query_behaviors through the server."""

    @pytest.mark.asyncio
    async def test_query_behaviors(self, server) -> None:
        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            await server.call_tool(
                "store_behavior",
                {"sentence": "Be empathetic always", "collection": "tone"},
            )
            result = await server.call_tool(
                "query_behaviors",
                {"query": "empathy", "collection": "tone", "top_k": 5},
            )
        data = _json(result)
        assert data["count"] >= 1


class TestDeleteToolE2E:
    """Test delete_behavior through the server."""

    @pytest.mark.asyncio
    async def test_delete_behavior(self, server) -> None:
        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            await server.call_tool("boring", {})
            store_result = await server.call_tool(
                "store_behavior",
                {"sentence": "Temp", "collection": "temp"},
            )
            doc_id = _json(store_result)["id"]
            await server.call_tool("boring", {})
            result = await server.call_tool("delete_behavior", {"behavior_id": doc_id})
        data = json.loads(_text(result))
        assert data["deleted"] is True


class TestListCollectionsE2E:
    """Test list_collections through the server."""

    @pytest.mark.asyncio
    async def test_list_collections(self, server) -> None:
        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            await server.call_tool("boring", {})
            await server.call_tool(
                "store_behavior",
                {"sentence": "x", "collection": "alpha"},
            )
            await server.call_tool("boring", {})
            result = await server.call_tool("list_collections", {})
        data = json.loads(_text(result))
        assert "alpha" in data["collections"]


class TestHealthCheckE2E:
    """Test health_check through the server."""

    @pytest.mark.asyncio
    async def test_health_check(self, server) -> None:
        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            await server.call_tool("boring", {})
            result = await server.call_tool("health_check", {})
        data = json.loads(_text(result))
        assert data["healthy"] is True
