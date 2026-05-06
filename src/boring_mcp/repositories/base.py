"""Repository protocol defining the data access interface."""

from __future__ import annotations

from typing import Protocol

from boring_mcp.models.results import QueryResult


class BehaviorRepository(Protocol):
    """Interface for behavior storage and retrieval."""

    def add(
        self, document: str, collection: str, metadata: dict[str, str], doc_id: str
    ) -> str:
        """Store a document and return its ID."""
        ...

    def query(self, text: str, collection: str, n_results: int) -> list[QueryResult]:
        """Query for similar documents, returning ranked results."""
        ...

    def delete(self, doc_id: str, collection: str) -> bool:
        """Delete a document by ID. Returns True if deleted."""
        ...

    def list_collections(self) -> list[str]:
        """List all collection names."""
        ...

    def get_all(self, collection: str) -> list[QueryResult]:
        """Get all documents in a collection."""
        ...
