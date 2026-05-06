"""Domain model for behavioral guidance sentences."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Behavior:
    """A single behavioral instruction stored in the vector database."""

    id: str
    sentence: str
    collection: str
    metadata: dict[str, str] = field(default_factory=dict)
    distance: float | None = None
