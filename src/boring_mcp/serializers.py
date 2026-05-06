"""Shared serialization utilities for Behavior domain objects."""

from __future__ import annotations

from boring_mcp.models.behavior import Behavior


def behavior_to_dict(
    behavior: Behavior, *, include_distance: bool = False
) -> dict[str, object]:
    """Serialize a Behavior to a JSON-safe dict.

    Args:
        behavior: The Behavior to serialize.
        include_distance: Whether to include the distance field.
    """
    data: dict[str, object] = {
        "id": behavior.id,
        "sentence": behavior.sentence,
        "collection": behavior.collection,
        "metadata": behavior.metadata,
    }
    if include_distance:
        data["distance"] = behavior.distance
    return data
