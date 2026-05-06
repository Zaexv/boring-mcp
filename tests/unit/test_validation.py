"""Unit tests for input validation."""

import pytest

from boring_mcp.validation import validate_collection, validate_sentence, validate_top_k


class TestValidateSentence:
    """Tests for sentence validation."""

    def test_valid_sentence(self) -> None:
        assert validate_sentence("Be kind") == "Be kind"

    def test_strips_whitespace(self) -> None:
        assert validate_sentence("  hello  ") == "hello"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            validate_sentence("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            validate_sentence("   ")


class TestValidateCollection:
    """Tests for collection name validation."""

    def test_valid_name(self) -> None:
        assert validate_collection("tone") == "tone"

    def test_allows_hyphens_underscores(self) -> None:
        assert validate_collection("my-collection_v2") == "my-collection_v2"

    def test_strips_whitespace(self) -> None:
        assert validate_collection("  persona  ") == "persona"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            validate_collection("")

    def test_invalid_chars_raises(self) -> None:
        with pytest.raises(ValueError, match="invalid characters"):
            validate_collection("bad/name!")


class TestValidateTopK:
    """Tests for top_k validation."""

    def test_valid_range(self) -> None:
        assert validate_top_k(5) == 5
        assert validate_top_k(1) == 1
        assert validate_top_k(50) == 50

    def test_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="between"):
            validate_top_k(0)

    def test_over_max_raises(self) -> None:
        with pytest.raises(ValueError, match="between"):
            validate_top_k(51)

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="between"):
            validate_top_k(-1)
