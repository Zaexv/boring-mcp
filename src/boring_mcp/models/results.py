"""Query result model returned from the repository layer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class QueryResult:
    """A single result from a vector similarity query."""

    id: str
    document: str
    metadata: dict[str, str] = field(default_factory=dict)
    distance: float = 0.0
