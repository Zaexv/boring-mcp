<p align="center">
  <h1 align="center">😐 Boring MCP</h1>
  <p align="center"><strong>Behavioral guidance for AI agents — via vector similarity search.</strong></p>
  <p align="center">
    <a href="https://github.com/Zaexv/boring-mcp/actions/workflows/ci.yml"><img src="https://github.com/Zaexv/boring-mcp/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
    <img src="https://img.shields.io/badge/coverage-98%25-brightgreen" alt="Coverage">
    <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+">
    <img src="https://img.shields.io/badge/mypy-strict-blueviolet" alt="MyPy Strict">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  </p>
</p>

---

## What is Boring MCP?

**Boring MCP** is an [MCP](https://modelcontextprotocol.io) (Model Context Protocol) server that gives AI agents a **persistent personality layer**. Store behavioral instructions — tone, boundaries, expertise, persona — in a local vector database, and let agents retrieve the most relevant guidance in real time via semantic similarity.

> **"Boring" is the point.** No magic, no cleverness, no surprises. Just well-typed, well-tested, predictable infrastructure that does exactly what it says.

### Why does this exist?

LLM agents need consistent behavior across sessions. Prompt engineering is fragile — it changes with every conversation. Boring MCP solves this by externalizing behavioral rules into a queryable, versionable, persistent store:

- 🧠 **Semantic retrieval** — agents get only the guidance relevant to the current context
- 🔒 **Server-enforced backpressure** — prevents rapid-fire actions; forces deliberate behavior
- 🏗️ **Clean architecture** — Protocol-based repository, service layer, tool layer
- 🧪 **98%+ test coverage** — strict typing, immutable models, layered testing

---

## Quick Start

### Install

```bash
# Clone and install
git clone https://github.com/Zaexv/boring-mcp.git
cd boring-mcp
uv sync
```

### Run

```bash
# Default: stdio transport (for MCP clients like Claude Desktop)
uv run boring-mcp

# SSE transport (for web-based MCP clients)
BORING_MCP_TRANSPORT=sse uv run boring-mcp

# Custom data directory
BORING_MCP_CHROMA_PATH=./my-data uv run boring-mcp
```

### Connect

Add to your MCP client configuration:

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

---

## How It Works

```
Agent → boring (30s sleep) → store/query/delete → Service → ChromaDB
```

Every tool call is gated by a **mandatory 30-second backpressure sleep**. The server enforces this — skip it and your call is denied. This isn't a bug. It's the core design philosophy: *predictability over velocity.*

### Tools

| Tool | Description |
|------|-------------|
| `boring` | **Mandatory** 30s sleep before every other tool call |
| `store_behavior` | Persist a behavioral instruction to a named collection |
| `query_behaviors` | Retrieve top-k relevant behaviors by semantic similarity |
| `delete_behavior` | Remove a behavior by ID |
| `list_collections` | List all available behavior collections |
| `health_check` | System health and ChromaDB connectivity |

### Resources

| Resource URI | Description |
|--------------|-------------|
| `behaviors://{collection}` | All behaviors in a collection |
| `behaviors://summary` | Overview of all collections with counts |

---

## Usage Examples

### Store behavioral guidance

```
→ boring()
← "You waited 30 seconds. Boring means predictable."

→ store_behavior(sentence="Always respond with empathy before offering solutions", collection="tone")
← {"id": "abc-123", "status": "stored"}
```

### Query relevant behaviors

```
→ boring()
→ query_behaviors(query="The user is angry about billing", collection="tone", top_k=3)
← {"results": [...], "count": 3}
```

### Organize into collections

| Collection | Purpose |
|-----------|---------|
| `tone` | Communication style and emotional register |
| `boundaries` | What the agent should refuse or avoid |
| `expertise` | Domain knowledge and specialization |
| `persona` | Identity, character traits, name |
| `formatting` | Output structure and presentation rules |
| `workflow` | Process steps and operational procedures |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FastMCP Transport                  │
│                (stdio · sse · http)                   │
├─────────────────────────────────────────────────────┤
│              BackpressureGuard (30s gate)             │
├────────────────────┬────────────────────────────────┤
│       Tools        │          Resources              │
│  boring            │  behaviors://{collection}       │
│  store_behavior    │  behaviors://summary            │
│  query_behaviors   │                                 │
│  delete_behavior   │                                 │
│  list_collections  │                                 │
│  health_check      │                                 │
├────────────────────┴────────────────────────────────┤
│                   Service Layer                       │
│         BehaviorService · HealthService               │
├─────────────────────────────────────────────────────┤
│            Repository (Protocol-based)                │
│               ChromaRepository                        │
├─────────────────────────────────────────────────────┤
│                ChromaDB (Vector Store)                │
│           Local persistent or in-memory               │
└─────────────────────────────────────────────────────┘
```

---

## Engineering Standards

This project is backpressured by great engineering. Every rule is enforced automatically:

| Rule | Enforcement | Why |
|------|-------------|-----|
| **Single-Exit-Point** | Custom AST linter | Predictable control flow, no hidden branches |
| **Backpressure** | Server-side guard | Agents can't bypass the 30s requirement |
| **Strict typing** | MyPy strict mode | No `Any`, no implicit optionals |
| **Immutable models** | `@dataclass(frozen=True)` | No mutation bugs, thread-safe |
| **Layered architecture** | Import discipline | Testable, swappable, predictable |
| **98%+ coverage** | pytest + CI gate | Changes must be tested |
| **Auto-formatting** | Ruff | Consistent style, zero debates |
| **Pre-commit hooks** | ruff + mypy + lint | Bad code can't enter the repo |

---

## Development

```bash
# Run tests
uv run pytest

# Lint and format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type check
uv run mypy

# Single-exit-point lint
python scripts/lint_single_return.py src/

# All checks at once (same as CI)
uv run ruff check . && uv run mypy && uv run pytest
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BORING_MCP_CHROMA_PATH` | `./data/chroma` | ChromaDB storage path (empty = in-memory) |
| `BORING_MCP_TRANSPORT` | `stdio` | Transport: `stdio`, `sse`, `http`, `streamable-http` |

---

## Agent Integration Patterns

### Pattern 1: Startup Loading

```
1. list_collections → discover available collections
2. Read behaviors://{collection} for each
3. Incorporate as system-level guidance
```

### Pattern 2: Contextual Retrieval (per-message)

```
1. User sends message
2. boring() → wait 30s
3. query_behaviors(query=user_message) → get relevant guidance
4. Incorporate into reasoning, then respond
```

### Pattern 3: Admin Mode

```
1. boring() → store_behavior(...) → add new instructions
2. boring() → delete_behavior(...) → remove outdated ones
3. boring() → list_collections() → audit the behavioral corpus
```

---

## Philosophy

> "The purpose of backpressure is not to slow things down. It's to ensure that every action is deliberate, validated, and reversible."

In conventional systems, speed is a feature. In Boring MCP, **predictability** is the feature. The 30-second sleep isn't punishment — it's a statement: *this system values correctness over velocity.*

Read more: [`ai-docs/backpressure.md`](ai-docs/backpressure.md)

---

## License

MIT
