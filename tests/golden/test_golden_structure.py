"""Golden-set regression tests for deterministic structure scoring.

Locks `score_rubric` outputs and tier mapping against a curated dataset so any
unintended change to the heuristics fails CI. Regenerate intentionally by
editing structure_goldenset.json when a scoring change is deliberate.
"""

import json
from pathlib import Path

import pytest

from boring_mcp.config import BackpressureConfig
from boring_mcp.scoring.rubric import score_rubric
from boring_mcp.scoring.tiers import Tiers

_GOLDEN = json.loads(
    (Path(__file__).parent / "structure_goldenset.json").read_text(encoding="utf-8")
)
_CASES = _GOLDEN["cases"]
_TIERS = Tiers.from_config(BackpressureConfig.from_env({}))


def _ids() -> list[str]:
    return [c["note"] for c in _CASES]


def test_goldenset_is_non_trivial():
    tiers = {c["tier"] for c in _CASES}
    assert tiers == {"lazy", "partial", "excellent"}, "golden set must span all tiers"
    assert len(_CASES) >= 12


@pytest.mark.parametrize("case", _CASES, ids=_ids())
def test_rubric_score_matches_golden(case):
    actual = score_rubric(case["text"])
    assert actual == case["score"], (
        f"rubric score drift for {case['note']!r}: "
        f"expected {case['score']}, got {actual}"
    )


@pytest.mark.parametrize("case", _CASES, ids=_ids())
def test_tier_matches_golden(case):
    actual_tier = _TIERS.tier_for(score_rubric(case["text"]))
    assert actual_tier == case["tier"], (
        f"tier drift for {case['note']!r}: expected {case['tier']}, got {actual_tier}"
    )
