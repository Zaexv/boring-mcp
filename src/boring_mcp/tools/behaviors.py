"""Behavior tools — store, query, and delete behavioral guidance."""

from __future__ import annotations

import json

from boring_mcp.models.behavior import Behavior
from boring_mcp.services.behavior_service import BehaviorService


def _behavior_to_dict(behavior: Behavior) -> dict[str, object]:
    """Serialize a Behavior to a JSON-safe dict."""
    return {
        "id": behavior.id,
        "sentence": behavior.sentence,
        "collection": behavior.collection,
        "metadata": behavior.metadata,
        "distance": behavior.distance,
    }


async def store_behavior(
    sentence: str,
    collection: str,
    metadata: dict[str, str] | None,
    *,
    service: BehaviorService,
) -> str:
    """Store a new behavioral sentence in a collection."""
    doc_id = service.store(sentence=sentence, collection=collection, metadata=metadata)
    return json.dumps({"id": doc_id, "status": "stored"})


async def query_behaviors(
    query: str, collection: str | None, top_k: int, *, service: BehaviorService
) -> str:
    """Retrieve the most relevant behaviors for a given context."""
    behaviors = service.query(query_text=query, collection=collection, top_k=top_k)
    results = [_behavior_to_dict(b) for b in behaviors]
    return json.dumps({"results": results, "count": len(results)})


async def delete_behavior(behavior_id: str, *, service: BehaviorService) -> str:
    """Remove a specific behavior by ID."""
    deleted = service.delete(doc_id=behavior_id)
    result = json.dumps({"id": behavior_id, "deleted": deleted})
    return result
