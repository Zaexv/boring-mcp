"""Input validation for tool boundaries.

Lightweight validation without external dependencies. Raises ValueError
with clear messages when inputs don't meet requirements.
"""

from __future__ import annotations

_TOP_K_MIN = 1
_TOP_K_MAX = 50


def validate_sentence(sentence: str) -> str:
    """Validate a behavioral sentence is non-empty."""
    cleaned = sentence.strip()
    if not cleaned:
        msg = "Sentence must not be empty"
        raise ValueError(msg)
    return cleaned


def validate_collection(collection: str) -> str:
    """Validate a collection name is non-empty and safe."""
    cleaned = collection.strip()
    if not cleaned:
        msg = "Collection name must not be empty"
        raise ValueError(msg)
    if not cleaned.replace("_", "").replace("-", "").isalnum():
        msg = (
            f"Collection name '{cleaned}' contains invalid characters. "
            "Use only alphanumeric, hyphens, and underscores."
        )
        raise ValueError(msg)
    return cleaned


def validate_top_k(top_k: int) -> int:
    """Validate top_k is within acceptable bounds."""
    if top_k < _TOP_K_MIN or top_k > _TOP_K_MAX:
        msg = f"top_k must be between {_TOP_K_MIN} and {_TOP_K_MAX}, got {top_k}"
        raise ValueError(msg)
    return top_k
