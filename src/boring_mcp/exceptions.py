"""Domain exceptions for Boring MCP.

Provides specific, named exceptions instead of generic RuntimeError/Exception.
Each exception maps to a clear failure mode in the system.
"""

from __future__ import annotations


class BoringMCPError(Exception):
    """Base exception for all Boring MCP errors."""


class CollectionNotFoundError(BoringMCPError):
    """Raised when a requested collection does not exist."""

    def __init__(self, collection: str) -> None:
        self.collection = collection
        super().__init__(f"Collection '{collection}' not found")


class BehaviorNotFoundError(BoringMCPError):
    """Raised when a behavior ID cannot be located."""

    def __init__(self, behavior_id: str) -> None:
        self.behavior_id = behavior_id
        super().__init__(f"Behavior '{behavior_id}' not found")


class StorageError(BoringMCPError):
    """Raised when ChromaDB storage operations fail."""

    def __init__(self, operation: str, detail: str) -> None:
        self.operation = operation
        self.detail = detail
        super().__init__(f"Storage error during {operation}: {detail}")


class BackpressureViolationError(BoringMCPError):
    """Raised when a tool is invoked without prior backpressure."""
