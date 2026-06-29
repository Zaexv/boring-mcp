"""Tests for the StructureScore model."""

import dataclasses

import pytest

from boring_mcp.models.structure import StructureScore


def test_structure_score_holds_fields():
    s = StructureScore(
        score=85, tier="excellent", reason="sampled=85", source="sampled"
    )
    assert s.score == 85
    assert s.tier == "excellent"
    assert s.reason == "sampled=85"
    assert s.source == "sampled"


def test_structure_score_is_frozen():
    s = StructureScore(score=10, tier="lazy", reason="r", source="fallback")
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.score = 99  # type: ignore[misc]
