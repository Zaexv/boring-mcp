"""Tests for the deterministic rubric scorer."""

from boring_mcp.scoring.rubric import score_rubric


def test_empty_is_zero():
    assert score_rubric("") == 0
    assert score_rubric("   ") == 0


def test_lazy_input_scores_low():
    assert score_rubric("be nice") < 40


def test_structured_input_scores_high():
    text = "When the user asks for code, respond with a fenced block, e.g. ```py```"
    assert score_rubric(text) >= 80


def test_filler_is_penalised():
    plain = "respond with a fenced code block when asked for code examples"
    filler = "just respond with really some fenced code block stuff when asked"
    assert score_rubric(filler) < score_rubric(plain)


def test_score_is_clamped_to_100():
    text = (
        "When the user asks for code, if the file exists, always respond "
        "with a fenced block, e.g. ```py```, never add prose: keep it short"
    )
    assert score_rubric(text) <= 100
