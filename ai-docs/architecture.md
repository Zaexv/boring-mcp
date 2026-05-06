# Boring MCP — Architecture

## Overview

Boring MCP is a **Model Context Protocol** server built with **FastMCP** (Python),
backed by a local **ChromaDB** vector database. It follows a strict layered architecture
with full type safety (MyPy strict mode) and comprehensive test coverage.

---

## High-Level Architecture

```mermaid
graph TB
    subgraph "AI Agent / Client"
        A[MCP Client]
    end

    subgraph "Boring MCP Server"
        B[FastMCP Transport Layer]
        C[MCP Tools & Resources]
        D[Service Layer]
        E[Repository Layer]
    end

    subgraph "Storage"
        F[(ChromaDB - Local)]
    end

    A <-->|MCP Protocol<br>stdio / SSE| B
    B --> C
    C --> D
    D --> E
    E <--> F
```

---

## Layer Responsibilities

```mermaid
graph LR
    subgraph "Layer 1: Transport"
        T1[FastMCP Server]
        T2[stdio transport]
        T3[SSE transport]
    end

    subgraph "Layer 2: Interface"
        I1[Tool Handlers]
        I2[Resource Handlers]
        I3[Input Validation<br>Pydantic Models]
    end

    subgraph "Layer 3: Service"
        S1[BehaviorService]
        S2[CollectionService]
        S3[HealthService]
    end

    subgraph "Layer 4: Repository"
        R1[ChromaRepository]
        R2[Collection Abstraction]
    end

    T1 --> I1
    T1 --> I2
    I1 --> I3
    I2 --> I3
    I3 --> S1
    I3 --> S2
    I3 --> S3
    S1 --> R1
    S2 --> R2
    S3 --> R1
```

---

## Component Diagram

```mermaid
classDiagram
    class MCPServer {
        +FastMCP app
        +register_tools()
        +register_resources()
        +run()
    }

    class BehaviorService {
        -repository: BehaviorRepository
        +store(sentence, collection, metadata) str
        +query(query, collection, top_k) list[Behavior]
        +delete(id) bool
        +list_collections() list[str]
        +get_collection(name) list[Behavior]
    }

    class BehaviorRepository {
        <<interface>>
        +add(document, collection, metadata) str
        +query(text, collection, n_results) list[QueryResult]
        +delete(id) bool
        +list_collections() list[str]
        +get_all(collection) list[Document]
    }

    class ChromaRepository {
        -client: chromadb.Client
        +add(document, collection, metadata) str
        +query(text, collection, n_results) list[QueryResult]
        +delete(id) bool
        +list_collections() list[str]
        +get_all(collection) list[Document]
    }

    class Behavior {
        +id: str
        +sentence: str
        +collection: str
        +metadata: dict
        +distance: float | None
    }

    class QueryResult {
        +id: str
        +document: str
        +metadata: dict
        +distance: float
    }

    MCPServer --> BehaviorService
    BehaviorService --> BehaviorRepository
    ChromaRepository ..|> BehaviorRepository
    BehaviorService ..> Behavior
    ChromaRepository ..> QueryResult
```

---

## Data Flow: Store Behavior

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant MCP as FastMCP Server
    participant Tool as store_behavior Tool
    participant Svc as BehaviorService
    participant Repo as ChromaRepository
    participant DB as ChromaDB

    Agent->>MCP: tools/call "store_behavior"
    MCP->>Tool: dispatch(params)
    Tool->>Tool: validate input (Pydantic)
    Tool->>Svc: store(sentence, collection, metadata)
    Svc->>Svc: generate UUID
    Svc->>Repo: add(document, collection, metadata)
    Repo->>DB: collection.add(documents, ids, metadatas)
    DB-->>Repo: success
    Repo-->>Svc: id
    Svc-->>Tool: id
    Tool-->>MCP: TextContent(id)
    MCP-->>Agent: result
```

---

## Data Flow: Query Behaviors

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant MCP as FastMCP Server
    participant Tool as query_behaviors Tool
    participant Svc as BehaviorService
    participant Repo as ChromaRepository
    participant DB as ChromaDB

    Agent->>MCP: tools/call "query_behaviors"
    MCP->>Tool: dispatch(params)
    Tool->>Tool: validate input (Pydantic)
    Tool->>Svc: query(query_text, collection, top_k)
    Svc->>Repo: query(text, collection, n_results)
    Repo->>DB: collection.query(query_texts, n_results)
    DB-->>Repo: results (ids, documents, distances)
    Repo->>Repo: map to QueryResult[]
    Repo-->>Svc: list[QueryResult]
    Svc->>Svc: map to list[Behavior]
    Svc-->>Tool: list[Behavior]
    Tool-->>MCP: TextContent(JSON)
    MCP-->>Agent: result
```

---

## Project Structure

```
boring-mcp/
├── pyproject.toml              # Project config, dependencies, mypy, pytest
├── README.md                   # User-facing documentation
├── agents.md                   # Agent integration guide
├── architecture.md             # This file
│
├── src/
│   └── boring_mcp/
│       ├── __init__.py
│       ├── server.py           # FastMCP server setup & entry point
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── behaviors.py    # store_behavior, query_behaviors, delete_behavior
│       │   ├── collections.py  # list_collections
│       │   └── health.py       # health_check
│       ├── resources/
│       │   ├── __init__.py
│       │   └── behaviors.py    # behaviors://{collection}, behaviors://summary
│       ├── services/
│       │   ├── __init__.py
│       │   ├── behavior_service.py
│       │   └── health_service.py
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── base.py         # BehaviorRepository (Protocol/ABC)
│       │   └── chroma.py       # ChromaRepository implementation
│       └── models/
│           ├── __init__.py
│           ├── behavior.py     # Behavior dataclass
│           ├── requests.py     # Pydantic input models
│           └── results.py      # QueryResult dataclass
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures (in-memory ChromaDB client)
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_behavior_service.py
│   │   ├── test_chroma_repository.py
│   │   └── test_models.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_tools.py
│   │   └── test_resources.py
│   └── e2e/
│       ├── __init__.py
│       └── test_mcp_protocol.py
│
└── scripts/
    └── seed_behaviors.py       # Script to seed initial behaviors
```

---

## Technology Stack

| Component        | Technology         | Rationale                                     |
|------------------|--------------------|-----------------------------------------------|
| MCP Framework    | FastMCP ≥ 2.0      | Official Python MCP SDK, batteries-included   |
| Vector DB        | ChromaDB (local)   | Zero-config local vector store, Python native |
| Type Checking    | MyPy (strict)      | Catch bugs before runtime                     |
| Validation       | Pydantic v2        | Runtime input validation with great DX        |
| Testing          | pytest + pytest-cov| Industry standard, plugin ecosystem           |
| Linting          | Ruff               | Fast, replaces flake8 + isort + black         |
| Package Manager  | uv                 | Fast, modern Python package management        |
| Python Version   | 3.11+              | Required for modern typing features           |

---

## Test Pipeline

```mermaid
graph LR
    subgraph "CI Pipeline"
        A[Lint<br>ruff check + ruff format --check] --> B[Type Check<br>mypy --strict]
        B --> C[Unit Tests<br>pytest tests/unit]
        C --> D[Integration Tests<br>pytest tests/integration]
        D --> E[E2E Tests<br>pytest tests/e2e]
        E --> F[Coverage Report<br>pytest --cov ≥ 90%]
    end
```

### Test Levels

| Level       | Scope                           | Dependencies          | Speed   |
|-------------|----------------------------------|-----------------------|---------|
| Unit        | Service logic, models, mapping   | None (mocked repos)   | < 1s    |
| Integration | Tools + Services + ChromaDB      | In-memory ChromaDB    | < 5s    |
| E2E         | Full MCP protocol round-trip     | Full server instance  | < 10s   |

---

## Configuration

Configuration is managed via environment variables with sensible defaults:

| Variable                 | Default              | Description                      |
|--------------------------|----------------------|----------------------------------|
| `BORING_MCP_CHROMA_PATH` | `./data/chroma`     | ChromaDB persistence directory   |
| `BORING_MCP_TRANSPORT`   | `stdio`             | Transport: `stdio` or `sse`      |
| `BORING_MCP_LOG_LEVEL`   | `INFO`              | Logging verbosity                |

---

## Design Decisions

### Why ChromaDB (Local)?

- Zero infrastructure overhead — runs in-process
- Handles embedding generation internally (default model)
- Simple Python API
- Persistent storage with a single path config
- Perfect for single-user / single-agent deployments

### Why FastMCP?

- Official MCP Python SDK from Anthropic
- Decorator-based tool/resource registration
- Built-in input validation
- Handles protocol serialization
- Supports both stdio and SSE transports

### Why Strict MyPy?

- The project name is "Boring" — we embrace predictability
- Catches None-safety issues, missing returns, type mismatches
- Forces explicit typing at boundaries (especially important for the service layer)
- Repository interface uses Protocol for structural subtyping

### Why Layered Architecture?

- **Testability** — each layer can be tested in isolation
- **Replaceability** — swap ChromaDB for Pinecone by implementing a new repository
- **Clarity** — new contributors know exactly where code belongs
- **Boring** — no surprises, no circular dependencies, just layers
