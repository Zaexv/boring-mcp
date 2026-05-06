# Boring MCP

[![CI](https://github.com/Zaexv/boring-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Zaexv/boring-mcp/actions/workflows/ci.yml)

A deliberately **boring** MCP (Model Context Protocol) server that provides AI agents with behavioral guidance via vector similarity search. Built with FastMCP, ChromaDB, and strict typing.

> **Boring is good.** No magic, no cleverness — just well-typed, well-tested, predictable code.

## What It Does

Boring MCP allows you to store behavioral sentences (instructions, personality traits, constraints) in a local ChromaDB vector database, then retrieve the most relevant ones via semantic similarity when an agent needs guidance.

**Key feature:** Every tool call is gated by a **mandatory 30-second backpressure sleep** (`boring` tool). This prevents rapid-fire agent actions and enforces deliberate, predictable behavior.

## Tools

| Tool | Description |
|------|-------------|
| `boring` | **Mandatory** — 30-second sleep before every other tool call |
| `store_behavior` | Store a behavioral instruction in a collection |
| `query_behaviors` | Retrieve relevant behaviors by semantic similarity |
| `delete_behavior` | Remove a behavior by ID |
| `list_collections` | List all behavior collections |
| `health_check` | System health status |

## Resources

| Resource | Description |
|----------|-------------|
| `behaviors://{collection}` | All behaviors in a collection |
| `behaviors://summary` | Collection names and counts |

## Setup

```bash
uv sync
```

## Run

```bash
uv run boring-mcp
```

Or with custom ChromaDB path:

```bash
BORING_MCP_CHROMA_PATH=./my-data uv run boring-mcp
```

## Test

```bash
uv run pytest
```

## Lint & Type Check

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
python scripts/lint_single_return.py src/
uv run mypy
```

## AI Documentation

All agent-facing documentation lives in **`ai-docs/`**:

- [`ai-docs/agents.md`](ai-docs/agents.md) — Agent integration guide, tool schemas, backpressure rules
- [`ai-docs/architecture.md`](ai-docs/architecture.md) — System architecture with Mermaid diagrams
- [`ai-docs/state.md`](ai-docs/state.md) — Session continuity state

## Code Rules

| Rule | Enforcement |
|------|-------------|
| **Single-Exit-Point** | `scripts/lint_single_return.py` — one `return` per function, at the end |
| **Backpressure** | `BackpressureGuard` — server rejects tools if `boring` wasn't called first |
| **Strict typing** | MyPy strict mode, no `Any` escapes |
| **Ruff** | Linting + formatting with `RET` rules (except `RET504` which conflicts with single-exit) |

## Architecture

```
Agent → FastMCP Transport → Tools/Resources → Service Layer → Repository → ChromaDB
```

See [`ai-docs/architecture.md`](ai-docs/architecture.md) for full Mermaid diagrams.

## License

MIT
