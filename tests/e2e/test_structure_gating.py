"""End-to-end tests for structure-gated backpressure on store/query tools."""

import unittest.mock

import pytest

from boring_mcp.server import create_server


def _text(result) -> str:  # type: ignore[no-untyped-def]
    """Extract text from a FastMCP ToolResult."""
    return result.content[0].text


@pytest.fixture
def server():
    """Server with in-memory ChromaDB and sampling forced off for determinism."""
    env = {"BORING_MCP_CHROMA_PATH": "", "BORING_MCP_SAMPLING": "off"}
    with unittest.mock.patch.dict("os.environ", env):
        srv = create_server()
    return srv


@pytest.mark.asyncio
async def test_structured_store_returns_thanks(server) -> None:
    with unittest.mock.patch(
        "boring_mcp.backpressure.asyncio.sleep", return_value=None
    ):
        result = await server.call_tool(
            "store_behavior",
            {
                "sentence": (
                    "When the user asks for code, respond with a fenced block, "
                    "e.g. ```py```"
                ),
                "collection": "formatting",
            },
        )
    assert "Thanks for being so structured" in _text(result)


@pytest.mark.asyncio
async def test_lazy_store_returns_boring(server) -> None:
    with unittest.mock.patch(
        "boring_mcp.backpressure.asyncio.sleep", return_value=None
    ):
        result = await server.call_tool(
            "store_behavior",
            {"sentence": "be nice", "collection": "tone"},
        )
    assert "30 seconds" in _text(result)


@pytest.mark.asyncio
async def test_store_works_without_prior_boring(server) -> None:
    with unittest.mock.patch(
        "boring_mcp.backpressure.asyncio.sleep", return_value=None
    ):
        result = await server.call_tool(
            "store_behavior",
            {"sentence": "be nice", "collection": "tone"},
        )
    assert "stored" in _text(result)


@pytest.mark.asyncio
async def test_structured_query_returns_thanks(server) -> None:
    with unittest.mock.patch(
        "boring_mcp.backpressure.asyncio.sleep", return_value=None
    ):
        result = await server.call_tool(
            "query_behaviors",
            {
                "query": (
                    "When the user mentions empathy in a message, always return "
                    "the relevant tone guidance entries, e.g. warm and patient "
                    "phrasing"
                ),
                "collection": "tone",
                "top_k": 5,
            },
        )
    assert "Thanks for being so structured" in _text(result)
