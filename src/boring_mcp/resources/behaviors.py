"""MCP resources — expose behavior data as readable resources."""

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
    }


async def get_collection_behaviors(collection: str, *, service: BehaviorService) -> str:
    """Get all behaviors in a given collection."""
    behaviors = service.get_collection(collection)
    results = [_behavior_to_dict(b) for b in behaviors]
    return json.dumps(
        {"collection": collection, "behaviors": results, "count": len(results)}
    )


async def get_behaviors_summary(*, service: BehaviorService) -> str:
    """Get a summary of all collections and their counts."""
    collections = service.list_collections()
    summary: list[dict[str, object]] = []
    for col_name in collections:
        behaviors = service.get_collection(col_name)
        summary.append({"collection": col_name, "count": len(behaviors)})
    return json.dumps({"collections": summary, "total_collections": len(summary)})
