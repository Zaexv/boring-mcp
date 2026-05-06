"""Behavior tools — store, query, and delete behavioral guidance."""

from __future__ import annotations

import json

from boring_mcp.serializers import behavior_to_dict
from boring_mcp.services.behavior_service import BehaviorService
from boring_mcp.validation import validate_collection, validate_sentence, validate_top_k


async def store_behavior(
    sentence: str,
    collection: str,
    metadata: dict[str, str] | None,
    *,
    service: BehaviorService,
) -> str:
    """Store a new behavioral sentence in a collection."""
    clean_sentence = validate_sentence(sentence)
    clean_collection = validate_collection(collection)
    doc_id = service.store(
        sentence=clean_sentence, collection=clean_collection, metadata=metadata
    )
    return json.dumps({"id": doc_id, "status": "stored"})


async def query_behaviors(
    query: str, collection: str | None, top_k: int, *, service: BehaviorService
) -> str:
    """Retrieve the most relevant behaviors for a given context."""
    clean_query = validate_sentence(query)
    safe_top_k = validate_top_k(top_k)
    clean_collection = validate_collection(collection) if collection else None
    behaviors = service.query(
        query_text=clean_query, collection=clean_collection, top_k=safe_top_k
    )
    results = [behavior_to_dict(b, include_distance=True) for b in behaviors]
    return json.dumps({"results": results, "count": len(results)})


async def delete_behavior(behavior_id: str, *, service: BehaviorService) -> str:
    """Remove a specific behavior by ID."""
    deleted = service.delete(doc_id=behavior_id)
    result = json.dumps({"id": behavior_id, "deleted": deleted})
    return result
