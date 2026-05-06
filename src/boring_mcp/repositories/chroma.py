"""ChromaDB implementation of the BehaviorRepository."""

from __future__ import annotations

import chromadb
from chromadb.api import ClientAPI

from boring_mcp.models.results import QueryResult


class ChromaRepository:
    """ChromaDB-backed behavior repository."""

    def __init__(
        self, client: ClientAPI | None = None, persist_path: str | None = None
    ) -> None:
        if client is not None:
            self._client = client
        elif persist_path:
            self._client = chromadb.PersistentClient(path=persist_path)
        else:
            self._client = chromadb.EphemeralClient()

    def add(
        self, document: str, collection: str, metadata: dict[str, str], doc_id: str
    ) -> str:
        """Store a document in the specified collection."""
        col = self._client.get_or_create_collection(name=collection)
        col.add(
            documents=[document],
            ids=[doc_id],
            metadatas=[metadata] if metadata else None,
        )
        return doc_id

    def query(self, text: str, collection: str, n_results: int) -> list[QueryResult]:
        """Query for similar documents using vector similarity."""
        col = self._client.get_or_create_collection(name=collection)
        count = col.count()
        output: list[QueryResult] = []
        if count > 0:
            effective_n = min(n_results, count)
            results = col.query(query_texts=[text], n_results=effective_n)
            output = self._map_results(results)  # type: ignore[arg-type]
        return output

    def delete(self, doc_id: str, collection: str) -> bool:
        """Delete a document by ID from the specified collection."""
        col = self._client.get_or_create_collection(name=collection)
        existing = col.get(ids=[doc_id])
        deleted = bool(existing["ids"])
        if deleted:
            col.delete(ids=[doc_id])
        return deleted

    def list_collections(self) -> list[str]:
        """List all collection names in the database."""
        collections = self._client.list_collections()
        return [c.name for c in collections]

    def get_all(self, collection: str) -> list[QueryResult]:
        """Get all documents in a collection."""
        col = self._client.get_or_create_collection(name=collection)
        output: list[QueryResult] = []
        if col.count() > 0:
            results = col.get(include=["documents", "metadatas"])
            ids = results.get("ids", [])
            documents = results.get("documents") or []
            metadatas = results.get("metadatas") or []
            for i, doc_id in enumerate(ids):
                doc = documents[i] if i < len(documents) else ""
                meta = metadatas[i] if i < len(metadatas) else {}
                output.append(
                    QueryResult(
                        id=doc_id,
                        document=doc or "",
                        metadata={str(k): str(v) for k, v in meta.items()}
                        if meta
                        else {},
                        distance=0.0,
                    )
                )
        return output

    @staticmethod
    def _map_results(results: dict) -> list[QueryResult]:  # type: ignore[type-arg]
        """Map ChromaDB query results to QueryResult objects."""
        output: list[QueryResult] = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        for i, doc_id in enumerate(ids):
            output.append(
                QueryResult(
                    id=doc_id,
                    document=documents[i] if i < len(documents) else "",
                    metadata=dict(metadatas[i])
                    if i < len(metadatas) and metadatas[i]
                    else {},
                    distance=distances[i] if i < len(distances) else 0.0,
                )
            )
        return output
