# Boring MCP — CLAUDE.md

## What

MCP server. Give AI agent persistent personality layer. Behavior instructions live in ChromaDB. Pull back by vector similarity per context.

**Philosophy:** predictability > velocity. 30s backpressure sleep intentional. Not bug.

## Run

```bash
uv run boring-mcp                          # stdio (default)
BORING_MCP_TRANSPORT=sse uv run boring-mcp # SSE
BORING_MCP_CHROMA_PATH=./my-data uv run boring-mcp
```

## Dev Commands

```bash
uv run pytest                              # all tests (98%+ coverage)
uv run ruff check src/ tests/             # lint
uv run ruff format src/ tests/            # format
uv run mypy                               # strict types
python scripts/lint_single_return.py src/ # single-exit lint
uv run ruff check . && uv run mypy && uv run pytest  # full CI
```

## Stack

- Python >=3.11. `uv` runner. `hatchling` build.
- Deps: `fastmcp>=2.0`, `chromadb>=0.5`, `pyyaml>=6`.
- Entry point: `boring-mcp = boring_mcp.server:main`.

## Architecture

```
FastMCP Transport (stdio | sse | http)
    └── BackpressureGuard (30s gate — server-side enforced)
        ├── Tools: boring, store_behavior, query_behaviors, delete_behavior, list_collections, health_check
        ├── Resources: behaviors://{collection}, behaviors://summary
        └── Service Layer
            ├── BehaviorService
            └── HealthService
                └── ChromaRepository (Protocol-based)
                    └── ChromaDB (persistent or in-memory)
```

Layout `src/boring_mcp/`:
- `server.py` — wire layers, entry point
- `backpressure.py` — 30s guard + `@guard.guarded` decorator
- `validation.py` — input checks
- `serializers.py` — output shaping
- `exceptions.py` — error types
- `logging.py` — log setup
- `seed.py` — seed collections
- `models/` — frozen dataclasses
- `repositories/chroma.py` — ChromaDB adapter
- `services/behavior_service.py` — business logic (also HealthService)
- `tools/behaviors.py` — store/query/delete handlers
- `resources/` — `behaviors://` resource handlers

## Tools

| Tool | Needs `boring()` first? | Does |
|------|---------------------------|-------------|
| `boring` | — | 30s sleep. Manual full-boring. Required before admin tools |
| `store_behavior` | No — structure-gated | Save behavior. Sleep scales with input structure (0/10/30s) |
| `query_behaviors` | No — structure-gated | Top-k pull. Sleep scales with query structure (0/10/30s) |
| `delete_behavior` | Yes | Remove by ID |
| `list_collections` | Yes | List all collections |
| `health_check` | Yes | ChromaDB connectivity check |

**Structure gate:** `store_behavior`/`query_behaviors` score input 0-100 via client LLM sampling (`ctx.sample`, deterministic rubric fallback). `<40`=lazy→30s, `40-79`=partial→10s, `≥80`=excellent→0s + "Thanks for being so structured." See `ai-docs/backpressure.md` §1b.

## Collections

| Collection | Purpose |
|-----------|---------|
| `persona` | Identity, traits, name |
| `tone` | Communication style |
| `boundaries` | What to refuse |
| `expertise` | Domain knowledge |
| `formatting` | Output structure |
| `workflow` | Process steps |

## Env Vars

| Var | Default | Does |
|-----|---------|-------------|
| `BORING_MCP_CHROMA_PATH` | `./data/chroma` | Storage path (empty = in-memory) |
| `BORING_MCP_TRANSPORT` | `stdio` | `stdio`, `sse`, `http`, `streamable-http` |
| `BORING_MCP_SAMPLING` | `auto` | `auto` = LLM judge + rubric fallback; `off` = rubric only (deterministic) |
| `BORING_MCP_TIER_LAZY_MAX` | `39` | Upper bound (inclusive) of lazy tier |
| `BORING_MCP_TIER_PARTIAL_MAX` | `79` | Upper bound (inclusive) of partial tier |
| `BORING_MCP_SLEEP_LAZY` | `30` | Seconds for lazy tier |
| `BORING_MCP_SLEEP_PARTIAL` | `10` | Seconds for partial tier |
| `BORING_MCP_SLEEP_EXCELLENT` | `0` | Seconds for excellent tier |

## Engineering Rules (all enforced)

- **Single-exit-point** — one `return` per function. Custom AST linter (`scripts/lint_single_return.py`)
- **Strict mypy** — no `Any`, no implicit optional
- **Immutable models** — `@dataclass(frozen=True)` everywhere
- **Coverage** — gate `fail_under=90` in pyproject, target 98%+
- **Ruff** — `E, F, I, N, UP, B, A, SIM, RET`. `RET504` off (clash single-exit). Tests ignore `B006`
- **Pre-commit** — ruff + mypy + lint each commit

## Plans

- `plans/` — design specs (`YYYY-MM-DD-<feature>.md`)
- `plan-implementations/` — executable TDD plans (`...-impl.md`)
- **Standard:** completed impl plan gets `DONE_` filename prefix once full CI passes. No prefix = unfinished. See `plan-implementations/README.md`

## Tests

```
tests/
├── unit/        # isolated, no I/O
├── integration/ # service + repo
└── e2e/         # full server via FastMCP
```

`pytest` config: `asyncio_mode=auto`, cov on `boring_mcp`, term-missing report.

## MCP Client Config

```json
{
  "mcpServers": {
    "boring-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/boring-mcp", "run", "boring-mcp"]
    }
  }
}
```

## Agent Patterns

**Startup:** `list_collections` → Read `behaviors://{collection}` → inject as system guidance

**Per-message:** `boring()` → `query_behaviors(query=user_msg)` → fold in → reply

**Admin:** `boring()` → `store_behavior` / `delete_behavior` / `list_collections`

## Docs

- `ai-docs/architecture.md` — full architecture + diagrams
- `ai-docs/backpressure.md` — backpressure rationale
- `ai-docs/agents.md` — agent integration
- `ai-docs/state.md` — state management
- `ai-docs/skill-extend-mcp.md` — how to add new tools
</content>
</invoke>
