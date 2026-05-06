# Boring MCP — Project State

> Last updated: 2026-05-06

---

## Health Summary

| Metric | Status |
|--------|--------|
| **Tests** | ✅ 87 passing |
| **Coverage** | ✅ 99.5% (threshold: 90%) |
| **MyPy strict** | ✅ 0 errors in 25 source files |
| **Ruff lint** | ✅ Clean |
| **Ruff format** | ✅ 45 files formatted |
| **Single-exit-point** | ✅ All functions compliant |
| **CI pipeline** | ✅ lint → test → typecheck |

---

## Architecture Status

| Layer | Module(s) | Status |
|-------|-----------|--------|
| Transport | `server.py` | ✅ FastMCP with stdio/SSE/HTTP/streamable-http |
| Enforcement | `backpressure.py` | ✅ Server-side guard, `@guarded` decorator |
| Interface | `tools/`, `resources/` | ✅ 5 tools + 2 resources |
| Validation | `validation.py` | ✅ Sentence, collection, top_k validators |
| Service | `services/` | ✅ BehaviorService + HealthService |
| Repository | `repositories/` | ✅ Protocol + ChromaDB implementation |
| Domain | `models/` | ✅ Frozen dataclasses (Behavior, QueryResult) |
| Cross-cutting | `exceptions.py`, `logging.py`, `serializers.py` | ✅ |

---

## File Inventory

```
src/boring_mcp/
├── __init__.py              (3 stmts, 100% coverage)
├── __main__.py              (3 stmts, 100% coverage)
├── backpressure.py          (43 stmts, 100% coverage)
├── exceptions.py            (16 stmts, 100% coverage)
├── logging.py               (15 stmts, 100% coverage)
├── seed.py                  (46 stmts, 98% coverage)
├── serializers.py           (7 stmts, 100% coverage)
├── server.py                (66 stmts, 98% coverage)
├── validation.py            (23 stmts, 100% coverage)
├── models/
│   ├── __init__.py          (3 stmts, 100% coverage)
│   ├── behavior.py          (9 stmts, 100% coverage)
│   └── results.py           (8 stmts, 100% coverage)
├── repositories/
│   ├── base.py              (9 stmts, 100% coverage)
│   └── chroma.py            (57 stmts, 100% coverage)
├── resources/
│   └── behaviors.py         (15 stmts, 100% coverage)
├── services/
│   ├── behavior_service.py  (39 stmts, 100% coverage)
│   └── health_service.py    (20 stmts, 100% coverage)
└── tools/
    ├── behaviors.py         (21 stmts, 100% coverage)
    ├── boring.py            (6 stmts, 100% coverage)
    ├── collections.py       (6 stmts, 100% coverage)
    └── health.py            (6 stmts, 100% coverage)

Total: 419 statements, 99.5% coverage
```

---

## Test Structure

```
tests/
├── conftest.py                    — Shared fixtures (EphemeralClient)
├── unit/                          — 7 test modules
│   ├── test_backpressure.py       — BackpressureGuard logic
│   ├── test_behavior_service.py   — Service layer orchestration
│   ├── test_boring.py             — Standalone backpressure coroutine
│   ├── test_chroma_repository.py  — Repository CRUD operations
│   ├── test_edge_cases.py         — Client init branches, health errors
│   ├── test_exceptions.py         — Domain exception construction
│   ├── test_health_service.py     — Health check paths
│   ├── test_main.py               — __main__.py entry point
│   ├── test_models.py             — Frozen dataclass behavior
│   ├── test_seed.py               — YAML loading & seed pipeline + CLI
│   └── test_validation.py         — Input validation rules
├── integration/                   — 2 test modules
│   ├── test_resources.py          — Resource handlers + ChromaDB
│   └── test_tools.py              — Tool handlers + service + ChromaDB
└── e2e/                           — 2 test modules
    ├── test_server.py             — Full tool pipeline via call_tool
    └── test_server_internals.py   — Singleton, transport, resources
```

---

## Dependencies

### Runtime
| Package | Version | Purpose |
|---------|---------|---------|
| fastmcp | ≥ 2.0.0 | MCP server framework |
| chromadb | ≥ 0.5.0 | Vector similarity search |
| pyyaml | ≥ 6.0 | YAML seed file parsing |

### Development
| Package | Version | Purpose |
|---------|---------|---------|
| pytest | ≥ 8.0.0 | Test framework |
| pytest-cov | ≥ 5.0.0 | Coverage reporting |
| pytest-asyncio | ≥ 0.23.0 | Async test support |
| mypy | ≥ 1.10.0 | Static type checking |
| ruff | ≥ 0.4.0 | Linting & formatting |
| types-PyYAML | ≥ 6.0 | Type stubs |

---

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `BORING_MCP_CHROMA_PATH` | `./data/chroma` | ChromaDB storage path (empty = in-memory) |
| `BORING_MCP_TRANSPORT` | `stdio` | Transport: stdio, sse, http, streamable-http |
| `BORING_MCP_LOG_LEVEL` | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR |

---

## CI/CD Pipeline

**GitHub Actions** (`.github/workflows/ci.yml`):

```
lint (Ruff + Format + Single-Exit) → test (pytest + coverage ≥ 80%) → typecheck (MyPy strict)
```

Triggers on: push to `main`, pull requests to `main`.

---

## Known Uncovered Lines

| File | Line | Reason |
|------|------|--------|
| `seed.py` | 91 | `if __name__ == "__main__"` guard |
| `server.py` | 162 | `if __name__ == "__main__"` guard |

These are standard Python idioms and are intentionally not tested.

---

## What's Next

See [`plans/roadmap.md`](../plans/roadmap.md) for the full feature roadmap.

**Immediate opportunities:**
- Behavior versioning (track history of changes)
- Batch import/export tool
- Collection metadata (descriptions, schemas)
- Async repository layer
- Docker image for deployment
