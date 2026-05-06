"""Unit tests for the seed utility."""

import unittest.mock
from pathlib import Path

from boring_mcp.seed import _load_yaml, main, seed_from_yaml


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

    def test_skips_empty_strings(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "empty_strings.yaml"
        yaml_file.write_text("tone:\n  - ''\n  - '   '\n  - valid\n")
        with unittest.mock.patch("boring_mcp.seed.ChromaRepository"):
            count = seed_from_yaml(str(yaml_file), chroma_path="./fake")
        assert count == 1


class TestSeedMain:
    """Tests for the CLI entry point."""

    def test_main_prints_usage_on_no_args(self) -> None:
        with (
            unittest.mock.patch("sys.argv", ["boring_mcp.seed"]),
            unittest.mock.patch("builtins.print") as mock_print,
        ):
            import pytest

            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        mock_print.assert_called_once_with(
            "Usage: python -m boring_mcp.seed <path-to-yaml>"
        )

    def test_main_calls_seed_from_yaml(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("tone:\n  - Hello\n")
        with (
            unittest.mock.patch("sys.argv", ["seed", str(yaml_file)]),
            unittest.mock.patch(
                "boring_mcp.seed.seed_from_yaml", return_value=1
            ) as mock_seed,
            unittest.mock.patch("builtins.print"),
        ):
            main()
        mock_seed.assert_called_once_with(str(yaml_file), "./data/chroma")

    def test_main_with_custom_chroma_path(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("tone:\n  - Hello\n")
        with (
            unittest.mock.patch("sys.argv", ["seed", str(yaml_file), "/custom/path"]),
            unittest.mock.patch(
                "boring_mcp.seed.seed_from_yaml", return_value=1
            ) as mock_seed,
            unittest.mock.patch("builtins.print"),
        ):
            main()
        mock_seed.assert_called_once_with(str(yaml_file), "/custom/path")
