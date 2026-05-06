"""Unit tests for domain models."""

import pytest

from boring_mcp.models.behavior import Behavior
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
