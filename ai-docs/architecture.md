# Boring MCP — Architecture

## Overview

Boring MCP is a **Model Context Protocol** server built with **FastMCP** (Python),
backed by a local **ChromaDB** vector database. It follows **SOLID principles** and
**Clean Architecture** with strict typing (MyPy strict), 99%+ test coverage, and
server-enforced backpressure.

---

## SOLID Principles Applied

| Principle | Implementation |
|-----------|---------------|
| **Single Responsibility** | Each module has one job: `backpressure.py` enforces gates, `validation.py` validates inputs, `serializers.py` handles serialization |
| **Open/Closed** | New repositories (Pinecone, Qdrant) implement `BehaviorRepository` Protocol — no existing code changes needed |
| **Liskov Substitution** | `ChromaRepository` structurally satisfies the `BehaviorRepository` Protocol — all clients work identically |
| **Interface Segregation** | `BehaviorRepository` Protocol defines only 5 essential methods — no bloated interfaces |
| **Dependency Inversion** | Services depend on the `BehaviorRepository` Protocol, never on `ChromaRepository` directly |

---

## High-Level Architecture

```mermaid
graph TB
    subgraph "AI Agent / Client"
        A[MCP Client]
    end

    subgraph "Boring MCP Server"
        BP[BackpressureGuard<br>30s mandatory sleep]
        B[FastMCP Transport Layer]
        C[MCP Tools & Resources]
        V[Input Validation]
        D[Service Layer]
        E[Repository Layer<br>Protocol-based]
    end

    subgraph "Storage"
        F[(ChromaDB - Local/Persistent)]
    end

    A <-->|MCP Protocol<br>stdio / SSE / HTTP| B
    B --> BP
    BP --> C
    C --> V
    V --> D
    D --> E
    E <--> F
```

---

## Layer Responsibilities

```mermaid
graph LR
    subgraph "Layer 1: Transport"
        T1[FastMCP Server]
        T2[stdio / SSE / HTTP<br>streamable-http]
    end

    subgraph "Layer 2: Enforcement"
        BP[BackpressureGuard]
        BP2[guarded decorator]
    end

    subgraph "Layer 3: Interface"
        I1[Tool Handlers]
        I2[Resource Handlers]
        I3[Input Validation<br>validation.py]
    end

    subgraph "Layer 4: Service"
        S1[BehaviorService]
        S2[HealthService]
    end

    subgraph "Layer 5: Repository"
        R1[BehaviorRepository<br>Protocol]
        R2[ChromaRepository]
    end

    subgraph "Layer 6: Domain"
        D1[Behavior]
        D2[QueryResult]
        D3[HealthStatus]
    end

    T1 --> BP
    BP --> I1
    BP --> I2
    I1 --> I3
    I3 --> S1
    I3 --> S2
    S1 --> R1
    S2 --> R1
    R2 -.implements.-> R1
    S1 -.produces.-> D1
    R2 -.produces.-> D2
    S2 -.produces.-> D3
```

---

## Component Diagram

```mermaid
classDiagram
    class BackpressureGuard {
        -_last_boring_at: float
        -_last_tool_at: float
        +apply_backpressure() str
        +is_allowed() bool
        +record_tool_call() void
        +denial_message() str
        +guarded(fn) fn
    }

    class BehaviorService {
        -_repository: BehaviorRepository
        +store(sentence, collection, metadata) str
        +query(query_text, collection, top_k) list~Behavior~
        +delete(doc_id) bool
        +list_collections() list~str~
        +get_collection(collection) list~Behavior~
    }

    class HealthService {
        -_repository: BehaviorRepository
        +check() HealthStatus
    }

    class BehaviorRepository {
        <<Protocol>>
        +add(document, collection, metadata, doc_id) str
        +query(text, collection, n_results) list~QueryResult~
        +delete(doc_id, collection) bool
        +list_collections() list~str~
        +get_all(collection) list~QueryResult~
    }

    class ChromaRepository {
        -_client: ClientAPI
        +add(document, collection, metadata, doc_id) str
        +query(text, collection, n_results) list~QueryResult~
        +delete(doc_id, collection) bool
        +list_collections() list~str~
        +get_all(collection) list~QueryResult~
    }

    class Behavior {
        <<frozen>>
        +id: str
        +sentence: str
        +collection: str
        +metadata: dict
        +distance: float | None
    }

    class QueryResult {
        <<frozen>>
        +id: str
        +document: str
        +metadata: dict
        +distance: float
    }

    class HealthStatus {
        <<frozen>>
        +healthy: bool
        +chromadb_connected: bool
        +collections_count: int
        +message: str
    }

    BackpressureGuard --> BehaviorService : gates access
    BehaviorService --> BehaviorRepository : depends on
    HealthService --> BehaviorRepository : depends on
    ChromaRepository ..|> BehaviorRepository : implements
    BehaviorService ..> Behavior : produces
    ChromaRepository ..> QueryResult : produces
    HealthService ..> HealthStatus : produces
```

---

## Data Flow: Store Behavior

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant MCP as FastMCP Transport
    participant Guard as BackpressureGuard
    participant Tool as store_behavior
    participant Val as Validation
    participant Svc as BehaviorService
    participant Repo as ChromaRepository
    participant DB as ChromaDB

    Agent->>MCP: call "boring"
    MCP->>Guard: apply_backpressure()
    Guard-->>Agent: "waited 30s"

    Agent->>MCP: call "store_behavior"
    MCP->>Guard: guarded(store_behavior)
    Guard->>Guard: is_allowed() ✓
    Guard->>Tool: execute
    Tool->>Val: validate_sentence + validate_collection
    Val-->>Tool: cleaned inputs
    Tool->>Svc: store(sentence, collection, metadata)
    Svc->>Svc: generate UUID
    Svc->>Repo: add(document, collection, metadata, doc_id)
    Repo->>DB: collection.add(documents, ids, metadatas)
    DB-->>Repo: success
    Repo-->>Svc: doc_id
    Svc-->>Tool: doc_id
    Tool-->>MCP: JSON {"id": ..., "status": "stored"}
    MCP-->>Agent: result
```

---

## Data Flow: Query Behaviors

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant MCP as FastMCP Transport
    participant Guard as BackpressureGuard
    participant Tool as query_behaviors
    participant Val as Validation
    participant Svc as BehaviorService
    participant Repo as ChromaRepository
    participant DB as ChromaDB

    Agent->>MCP: call "boring"
    MCP->>Guard: apply_backpressure()
    Guard-->>Agent: "waited 30s"

    Agent->>MCP: call "query_behaviors"
    MCP->>Guard: guarded(query_behaviors)
    Guard->>Guard: is_allowed() ✓
    Guard->>Tool: execute
    Tool->>Val: validate_sentence + validate_top_k
    Val-->>Tool: cleaned inputs
    Tool->>Svc: query(query_text, collection, top_k)
    Svc->>Repo: query(text, collection, n_results)
    Repo->>DB: collection.query(query_texts, n_results)
    DB-->>Repo: results (ids, documents, distances)
    Repo->>Repo: map → list[QueryResult]
    Repo-->>Svc: list[QueryResult]
    Svc->>Svc: map → list[Behavior]
    Svc-->>Tool: list[Behavior]
    Tool-->>MCP: JSON {"results": [...], "count": N}
    MCP-->>Agent: result
```

---

## Project Structure

```
boring-mcp/
├── pyproject.toml              # Project config, deps, mypy, pytest, ruff
├── README.md                   # Market-facing documentation
├── ai-docs/                    # Agent-facing documentation
│   ├── agents.md               # Integration guide & backpressure rules
│   ├── architecture.md         # This file
│   ├── backpressure.md         # All 8 backpressure techniques explained
│   ├── state.md                # Current project health & metrics
│   └── skill-extend-mcp.md    # Step-by-step extension guide
│
├── .agents/skills/             # AI agent skills (Copilot CLI format)
│   └── extend-boring-mcp/     # Skill for extending the MCP server
│       └── SKILL.md
│
├── plans/
│   └── roadmap.md              # Feature roadmap (6 phases)
│
├── src/boring_mcp/
│   ├── __init__.py
│   ├── __main__.py             # python -m boring_mcp entry
│   ├── server.py               # FastMCP wiring, tool registration
│   ├── backpressure.py         # BackpressureGuard + @guarded decorator
│   ├── validation.py           # Input validation (no external deps)
│   ├── serializers.py          # Shared Behavior → dict serialization
│   ├── exceptions.py           # Domain-specific exceptions
│   ├── logging.py              # Structured logging configuration
│   ├── seed.py                 # YAML-based behavior seeding utility
│   ├── models/
│   │   ├── behavior.py         # Behavior (frozen dataclass)
│   │   └── results.py          # QueryResult (frozen dataclass)
│   ├── services/
│   │   ├── behavior_service.py # Business logic orchestration
│   │   └── health_service.py   # Health & connectivity checks
│   ├── repositories/
│   │   ├── base.py             # BehaviorRepository (Protocol)
│   │   └── chroma.py           # ChromaDB implementation
│   ├── tools/
│   │   ├── behaviors.py        # store/query/delete handlers
│   │   ├── collections.py      # list_collections handler
│   │   ├── boring.py           # Standalone backpressure coroutine
│   │   └── health.py           # health_check handler
│   └── resources/
│       └── behaviors.py        # behaviors://{collection}, behaviors://summary
│
├── tests/
│   ├── conftest.py             # Shared fixtures (EphemeralClient)
│   ├── unit/                   # Pure logic tests (no I/O)
│   ├── integration/            # Tools + Services + ChromaDB (in-memory)
│   └── e2e/                    # Full server pipeline via call_tool
│
├── scripts/
│   └── lint_single_return.py   # Custom AST linter (single-exit-point)
│
├── data/
│   └── example_behaviors.yaml  # Sample seed file
│
└── .github/workflows/ci.yml    # CI: lint → test → typecheck
```

---

## Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| MCP Framework | FastMCP ≥ 2.0 | Official Python MCP SDK, decorator-based |
| Vector DB | ChromaDB (local) | Zero-config, embeds internally, persistent |
| Type Checking | MyPy (strict) | No `Any`, no implicit optionals |
| Validation | Custom `validation.py` | Zero dependencies, single-exit-point compliant |
| Serialization | `serializers.py` | DRY: one serializer, shared across layers |
| Logging | Python `logging` | Structured, configurable via env var |
| Testing | pytest + pytest-cov | 99%+ coverage, 3-tier test structure |
| Linting | Ruff + custom AST | Fast, comprehensive, single-exit-point |
| Package Manager | uv | Fast, lockfile-based, reproducible |
| CI/CD | GitHub Actions | lint → test → typecheck pipeline |
| Python | 3.11+ | Modern typing (ParamSpec, `X | Y` syntax) |

---

## Test Strategy

```mermaid
graph LR
    subgraph "CI Pipeline"
        A[Ruff Lint + Format] --> B[Single-Exit Lint]
        B --> C[MyPy Strict]
        C --> D[Unit Tests]
        D --> E[Integration Tests]
        E --> F[E2E Tests]
        F --> G[Coverage ≥ 80%]
    end
```

| Level | What's Tested | Dependencies | Speed |
|-------|--------------|-------------|-------|
| Unit | Models, services, guard, validation | Mocked repos | < 1s |
| Integration | Tools + services + real ChromaDB | EphemeralClient | < 2s |
| E2E | Full tool pipeline via `server.call_tool` | Full server instance | < 6s |

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BORING_MCP_CHROMA_PATH` | `./data/chroma` | ChromaDB storage (empty = in-memory) |
| `BORING_MCP_TRANSPORT` | `stdio` | Transport: stdio, sse, http, streamable-http |
| `BORING_MCP_LOG_LEVEL` | `INFO` | Logging: DEBUG, INFO, WARNING, ERROR |

---

## Design Decisions

### Why Backpressure is Server-Enforced

Documentation-only backpressure is unenforceable — agents will skip it. The
`BackpressureGuard` makes compliance a server-side invariant: no `boring` call → no
tool execution. The `@guard.guarded` decorator keeps this DRY across all tools.

### Why Protocol (Not ABC)

Python's `Protocol` enables structural subtyping — any class with the right methods
satisfies the interface without explicit inheritance. This keeps the repository layer
decoupled and makes testing with mocks trivial.

### Why Frozen Dataclasses

Immutable domain objects (`Behavior`, `QueryResult`, `HealthStatus`) eliminate
mutation bugs, make data flow traceable, and are thread-safe by construction.

### Why No Pydantic at Runtime

After evaluating trade-offs, we removed Pydantic as a runtime dependency. Input
validation is handled by a lightweight `validation.py` module that follows the same
single-exit-point rule as the rest of the codebase. This reduces the dependency
footprint and keeps validation logic explicit and testable.

### Why Single-Exit-Point

Every function has exactly one `return` at the end. This makes control flow
predictable, eliminates hidden exit paths, and makes code review trivial. The custom
AST linter in `scripts/lint_single_return.py` enforces this at commit time and in CI.
