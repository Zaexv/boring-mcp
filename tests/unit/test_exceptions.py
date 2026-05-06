"""Unit tests for domain exceptions."""

from boring_mcp.exceptions import (
    BackpressureViolationError,
    BehaviorNotFoundError,
    BoringMCPError,
    CollectionNotFoundError,
    StorageError,
)


class TestExceptions:
    """Tests for custom exception hierarchy."""

    def test_base_exception_is_exception(self) -> None:
        assert issubclass(BoringMCPError, Exception)

    def test_collection_not_found(self) -> None:
        exc = CollectionNotFoundError("tone")
        assert exc.collection == "tone"
        assert "tone" in str(exc)
        assert isinstance(exc, BoringMCPError)

    def test_behavior_not_found(self) -> None:
        exc = BehaviorNotFoundError("abc-123")
        assert exc.behavior_id == "abc-123"
        assert "abc-123" in str(exc)
        assert isinstance(exc, BoringMCPError)

    def test_storage_error(self) -> None:
        exc = StorageError("add", "connection refused")
        assert exc.operation == "add"
        assert exc.detail == "connection refused"
        assert "add" in str(exc)
        assert isinstance(exc, BoringMCPError)

    def test_backpressure_violation(self) -> None:
        exc = BackpressureViolationError("Tool called without boring")
        assert isinstance(exc, BoringMCPError)
