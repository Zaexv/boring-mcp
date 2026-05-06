"""Tests for the __main__ entry point."""

import unittest.mock


class TestMainModule:
    """Test that python -m boring_mcp calls main()."""

    def test_main_invokes_server_main(self) -> None:
        with unittest.mock.patch("boring_mcp.server.main") as mock_main:
            import runpy

            runpy.run_module("boring_mcp", run_name="__main__", alter_sys=True)
        mock_main.assert_called_once()
