"""Health check tool — reports system health."""

from __future__ import annotations

import json

from boring_mcp.services.health_service import HealthService


async def health_check(*, service: HealthService) -> str:
    """Returns service health status including ChromaDB connectivity."""
    status = service.check()
    return json.dumps(
        {
            "healthy": status.healthy,
            "chromadb_connected": status.chromadb_connected,
            "collections_count": status.collections_count,
            "message": status.message,
        }
    )
