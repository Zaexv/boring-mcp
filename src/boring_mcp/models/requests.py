"""Pydantic request models for input validation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StoreBehaviorRequest(BaseModel):
    """Request to store a new behavioral sentence."""

    sentence: str = Field(
        ..., min_length=1, description="The behavioral instruction to store"
    )
    collection: str = Field(
        ..., min_length=1, description="Collection name (e.g., 'tone', 'persona')"
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Optional key-value metadata"
    )


class QueryBehaviorsRequest(BaseModel):
    """Request to query behaviors by semantic similarity."""

    query: str = Field(..., min_length=1, description="The context to match against")
    collection: str | None = Field(
        default=None, description="Filter by collection (all if omitted)"
    )
    top_k: int = Field(
        default=5, ge=1, le=50, description="Number of results to return"
    )


class DeleteBehaviorRequest(BaseModel):
    """Request to delete a behavior by ID."""

    id: str = Field(..., min_length=1, description="The behavior's ID")
