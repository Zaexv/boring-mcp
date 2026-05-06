"""Structured logging configuration for Boring MCP.

Provides a configured logger with consistent formatting. All tool calls,
backpressure events, and errors are logged for observability.
"""

from __future__ import annotations

import logging
import os
import sys


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger for the given module name."""
    logger = logging.getLogger(f"boring_mcp.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        level = os.environ.get("BORING_MCP_LOG_LEVEL", "INFO").upper()
        handler.setLevel(getattr(logging, level, logging.INFO))
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level, logging.INFO))
    return logger
