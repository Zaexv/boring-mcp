"""MCP tools for Boring MCP."""

from boring_mcp.tools.behaviors import delete_behavior, query_behaviors, store_behavior
from boring_mcp.tools.boring import boring
from boring_mcp.tools.collections import list_collections
from boring_mcp.tools.health import health_check

__all__ = [
    "boring",
    "delete_behavior",
    "health_check",
    "list_collections",
    "query_behaviors",
    "store_behavior",
]
