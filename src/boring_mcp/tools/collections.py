"""Collection tools — list available behavior collections."""

from __future__ import annotations

import json

from boring_mcp.services.behavior_service import BehaviorService


async def list_collections(*, service: BehaviorService) -> str:
    """List all available behavior collections."""
    collections = service.list_collections()
    return json.dumps({"collections": collections, "count": len(collections)})
