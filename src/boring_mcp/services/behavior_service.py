"""Behavior service — business logic for storing and querying behaviors."""

from __future__ import annotations

import uuid

from boring_mcp.models.behavior import Behavior
from boring_mcp.models.results import QueryResult
from boring_mcp.repositories.base import BehaviorRepository


class BehaviorService:
    """Orchestrates behavior storage and retrieval."""

    def __init__(self, repository: BehaviorRepository) -> None:
        self._repository = repository

    def store(
        self, sentence: str, collection: str, metadata: dict[str, str] | None = None
    ) -> str:
        """Store a behavioral sentence. Returns the generated ID."""
        doc_id = str(uuid.uuid4())
        self._repository.add(
            document=sentence,
            collection=collection,
            metadata=metadata or {},
            doc_id=doc_id,
        )
        return doc_id

    def query(
        self, query_text: str, collection: str | None = None, top_k: int = 5
    ) -> list[Behavior]:
        """Query for relevant behaviors by semantic similarity."""
        behaviors: list[Behavior] = []
        if collection:
            results = self._repository.query(
                text=query_text, collection=collection, n_results=top_k
            )
            behaviors = [self._to_behavior(r, collection) for r in results]
        else:
            # Query across all collections
            all_behaviors: list[Behavior] = []
            for col_name in self._repository.list_collections():
                results = self._repository.query(
                    text=query_text, collection=col_name, n_results=top_k
                )
                all_behaviors.extend(self._to_behavior(r, col_name) for r in results)
            all_behaviors.sort(
                key=lambda b: b.distance if b.distance is not None else float("inf")
            )
            behaviors = all_behaviors[:top_k]
        return behaviors

    def delete(self, doc_id: str) -> bool:
        """Delete a behavior by ID. Searches across all collections."""
        deleted = False
        for col_name in self._repository.list_collections():
            if self._repository.delete(doc_id=doc_id, collection=col_name):
                deleted = True
                break
        return deleted

    def list_collections(self) -> list[str]:
        """List all available behavior collections."""
        return self._repository.list_collections()

    def get_collection(self, collection: str) -> list[Behavior]:
        """Get all behaviors in a collection."""
        results = self._repository.get_all(collection=collection)
        return [self._to_behavior(r, collection) for r in results]

    @staticmethod
    def _to_behavior(result: QueryResult, collection: str) -> Behavior:
        """Map a QueryResult to a Behavior domain object."""
        return Behavior(
            id=result.id,
            sentence=result.document,
            collection=collection,
            metadata=result.metadata,
            distance=result.distance,
        )
