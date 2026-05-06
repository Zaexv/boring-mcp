"""Unit tests for the seed utility."""

import unittest.mock
from pathlib import Path

from boring_mcp.seed import _load_yaml, seed_from_yaml


class TestLoadYaml:
    """Tests for YAML loading and validation."""

    def test_valid_yaml(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("tone:\n  - Be kind\n  - Be clear\n")
        result = _load_yaml(str(yaml_file))
        assert result == {"tone": ["Be kind", "Be clear"]}

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        result = _load_yaml(str(tmp_path / "missing.yaml"))
        assert result is None

    def test_non_dict_yaml_returns_none(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text("- just a list\n")
        result = _load_yaml(str(yaml_file))
        assert result is None


class TestSeedFromYaml:
    """Tests for the full seed pipeline."""

    def test_seeds_behaviors(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "behaviors.yaml"
        yaml_file.write_text(
            "tone:\n  - Be empathetic\n  - Be clear\nboundaries:\n  - Never lie\n"
        )
        with unittest.mock.patch("boring_mcp.seed.ChromaRepository") as mock_repo_cls:
            mock_repo = unittest.mock.MagicMock()
            mock_repo_cls.return_value = mock_repo
            count = seed_from_yaml(str(yaml_file), chroma_path="./fake")
        assert count == 3

    def test_skips_non_list_values(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text("tone: not-a-list\n")
        with unittest.mock.patch("boring_mcp.seed.ChromaRepository"):
            count = seed_from_yaml(str(yaml_file), chroma_path="./fake")
        assert count == 0

    def test_missing_file_returns_zero(self) -> None:
        count = seed_from_yaml("/does/not/exist.yaml")
        assert count == 0
