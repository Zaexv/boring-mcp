# Boring MCP

A boring MCP server for agent behavioral guidance via vector similarity search.

Built with FastMCP, ChromaDB, and strict MyPy typing.

## Setup

```bash
uv sync
```

## Run

```bash
uv run boring-mcp
```

## Test

```bash
uv run pytest
```

## Lint & Type Check

```bash
uv run ruff check src/ tests/
uv run mypy
```
