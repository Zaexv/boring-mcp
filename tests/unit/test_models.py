"""Unit tests for domain models."""

import pytest
from pydantic import ValidationError

from boring_mcp.models.behavior import Behavior
from boring_mcp.models.requests import (
    DeleteBehaviorRequest,
    QueryBehaviorsRequest,
    StoreBehaviorRequest,
)
from boring_mcp.models.results import QueryResult


class TestBehavior:
    """Tests for the Behavior dataclass."""

    def test_create_minimal(self) -> None:
        b = Behavior(id="abc", sentence="Be kind", collection="tone")
        assert b.id == "abc"
        assert b.sentence == "Be kind"
        assert b.collection == "tone"
        assert b.metadata == {}
        assert b.distance is None

    def test_create_full(self) -> None:
        b = Behavior(
            id="xyz",
            sentence="Never lie",
            collection="boundaries",
            metadata={"priority": "high"},
            distance=0.123,
        )
        assert b.metadata == {"priority": "high"}
        assert b.distance == 0.123

    def test_frozen(self) -> None:
        b = Behavior(id="1", sentence="x", collection="c")
        with pytest.raises(AttributeError):
            b.id = "2"  # type: ignore[misc]


class TestQueryResult:
    """Tests for the QueryResult dataclass."""

    def test_create(self) -> None:
        r = QueryResult(id="a", document="hello", metadata={"k": "v"}, distance=0.5)
        assert r.id == "a"
        assert r.document == "hello"
        assert r.distance == 0.5


class TestStoreBehaviorRequest:
    """Tests for store request validation."""

    def test_valid(self) -> None:
        req = StoreBehaviorRequest(sentence="Be helpful", collection="tone")
        assert req.sentence == "Be helpful"
        assert req.metadata == {}

    def test_empty_sentence_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StoreBehaviorRequest(sentence="", collection="tone")

    def test_empty_collection_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StoreBehaviorRequest(sentence="Ok", collection="")


class TestQueryBehaviorsRequest:
    """Tests for query request validation."""

    def test_defaults(self) -> None:
        req = QueryBehaviorsRequest(query="angry user")
        assert req.top_k == 5
        assert req.collection is None

    def test_top_k_bounds(self) -> None:
        with pytest.raises(ValidationError):
            QueryBehaviorsRequest(query="x", top_k=0)

        with pytest.raises(ValidationError):
            QueryBehaviorsRequest(query="x", top_k=51)


class TestDeleteBehaviorRequest:
    """Tests for delete request validation."""

    def test_valid(self) -> None:
        req = DeleteBehaviorRequest(id="abc-123")
        assert req.id == "abc-123"
