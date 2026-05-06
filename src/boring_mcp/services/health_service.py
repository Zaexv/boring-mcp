"""Health service — checks system health and connectivity."""

from __future__ import annotations

from dataclasses import dataclass

from boring_mcp.exceptions import StorageError
from boring_mcp.repositories.base import BehaviorRepository


@dataclass(frozen=True, slots=True)
class HealthStatus:
    """Health check result."""

    healthy: bool
    chromadb_connected: bool
    collections_count: int
    message: str


class HealthService:
    """Reports system health status."""

    def __init__(self, repository: BehaviorRepository) -> None:
        self._repository = repository

    def check(self) -> HealthStatus:
        """Run health checks and return status."""
        try:
            collections = self._repository.list_collections()
            status = HealthStatus(
                healthy=True,
                chromadb_connected=True,
                collections_count=len(collections),
                message="All systems operational",
            )
        except (StorageError, OSError, RuntimeError) as e:
            status = HealthStatus(
                healthy=False,
                chromadb_connected=False,
                collections_count=0,
                message=f"ChromaDB connection failed: {e}",
            )
        return status
