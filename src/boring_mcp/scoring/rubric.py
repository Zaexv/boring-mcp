"""Deterministic heuristic scorer for structural quality of an input.

Pure fallback used when LLM sampling is unavailable or disabled. Returns an
integer 0-100; higher means more structured and specific.
"""

from __future__ import annotations

_CONDITION_WORDS = ("when", "if", "before", "after", "while", "unless")
_ACTION_WORDS = (
    "use",
    "avoid",
    "prefer",
    "always",
    "never",
    "respond",
    "format",
    "return",
    "keep",
)
_FILLER_WORDS = ("just", "really", "stuff", "etc", "something", "basically")
_CONCRETE_MARKERS = ("e.g.", ":", '"', "`")


def _has_any(low: str, words: tuple[str, ...]) -> bool:
    return any(w in low for w in words)


def _length_points(word_count: int) -> int:
    points = 15
    if word_count < 5:
        points = 0
    elif word_count <= 12:
        points = 15
    elif word_count <= 40:
        points = 25
    return points


def score_rubric(text: str) -> int:
    """Score the structural quality of text as an integer 0-100."""
    cleaned = text.strip()
    low = cleaned.lower()
    words = cleaned.split()
    score = 0
    if cleaned:
        score += _length_points(len(words))
        if _has_any(low, _CONDITION_WORDS):
            score += 20
        if _has_any(low, _ACTION_WORDS):
            score += 20
        if any(m in cleaned for m in _CONCRETE_MARKERS) or any(
            c.isdigit() for c in cleaned
        ):
            score += 15
        if _has_any(low, _FILLER_WORDS):
            score -= 10
    clamped = max(0, min(100, score))
    return clamped
