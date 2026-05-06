"""Domain models for Boring MCP."""

from boring_mcp.models.behavior import Behavior
from boring_mcp.models.requests import (
    DeleteBehaviorRequest,
    QueryBehaviorsRequest,
    StoreBehaviorRequest,
)
from boring_mcp.models.results import QueryResult

__all__ = [
    "Behavior",
    "DeleteBehaviorRequest",
    "QueryBehaviorsRequest",
    "QueryResult",
    "StoreBehaviorRequest",
]
