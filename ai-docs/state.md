# Boring MCP — Session State

> Last updated: 2026-05-06T15:21 CEST

## What's Done

| Phase | Status |
|-------|--------|
| Domain models (`models/behavior.py`, `results.py`, `requests.py`) | ✅ Done |
| Repository layer (`repositories/base.py`, `chroma.py`) | ✅ Done |
| Service layer (`services/behavior_service.py`, `health_service.py`) | ✅ Done |
| Backpressure guard (`backpressure.py`) | ✅ Done |
| MCP tools (`tools/boring.py`, `behaviors.py`, `collections.py`, `health.py`) | ✅ Done |
| MCP resources (`resources/behaviors.py`) | ✅ Done |
| Server entry point (`server.py`, `__main__.py`) | ✅ Done |
| Custom lint: single-exit-point (`scripts/lint_single_return.py`) | ✅ Done |
| Agent docs moved to `ai-docs/` | ✅ Done |
| `agents.md` updated with backpressure-every-step mandate | ✅ Done |
| Tests written (unit + integration) | ✅ Done |

## What's Remaining

1. **`uv sync` failed** — the install was running for a long time and exited with code 1. Need to re-run and debug the dependency resolution (likely chromadb compilation or network timeout).
2. **Run tests** — once deps install, run `uv run pytest` to validate all tests pass.
3. **Run ruff** — `uv run ruff check src/ tests/` to validate linting.
4. **Run mypy** — `uv run mypy` for type checking (may need adjustments for strict mode with chromadb types).
5. **Git commit** — all changes are unstaged. Commit and push once validated.

## Key Architecture Decisions

- **BackpressureGuard** (`src/boring_mcp/backpressure.py`): Server-side enforcement. Every non-`boring` tool checks `guard.is_allowed()` before executing. If the agent hasn't called `boring` since the last tool, it gets a denial message.
- **Single-Exit-Point Rule**: Enforced by `scripts/lint_single_return.py`. All source code passes. Every function has exactly one `return` at the end.
- **Ruff `RET` rules**: Added to `pyproject.toml` lint selection for additional return-pattern linting.
- **`asyncio_mode = "auto"`** added to pytest config for async tests.

## File Layout

```
ai-docs/
  agents.md          — Agent integration guide (backpressure mandate)
  architecture.md    — Mermaid diagrams, layered design
  state.md           — THIS FILE (session continuity)
src/boring_mcp/
  __init__.py
  __main__.py
  backpressure.py    — BackpressureGuard (30s sleep enforcement)
  server.py          — FastMCP wiring, all tools registered
  models/            — Behavior, QueryResult, Pydantic requests
  repositories/      — Protocol + ChromaDB implementation
  services/          — BehaviorService, HealthService
  tools/             — boring, behaviors, collections, health
  resources/         — behaviors resource handlers
tests/
  conftest.py        — Shared fixtures (in-memory ChromaDB)
  unit/              — test_models, test_chroma_repository, test_behavior_service,
                       test_boring, test_backpressure, test_health_service
  integration/       — test_tools, test_resources
scripts/
  lint_single_return.py  — Custom AST linter for single-exit-point
```

## To Resume

```bash
cd boring-mcp
uv sync                           # Install deps (retry if it failed)
python3 scripts/lint_single_return.py src/   # Should pass ✅
uv run pytest                     # Run all tests
uv run ruff check src/ tests/     # Lint
uv run mypy                       # Type check
git add -A && git commit -m "feat: implement boring MCP with backpressure enforcement"
```
