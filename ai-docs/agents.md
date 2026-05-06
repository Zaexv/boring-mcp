# Boring MCP — Agents Guide

## ⚠️ Location Notice

All AI-facing documentation lives in the **`ai-docs/`** folder at the repository root.
When searching for architectural guidance, behavioral contracts, or tool schemas,
always look in `ai-docs/`.

**Related docs:**
- `ai-docs/architecture.md` — SOLID architecture, layer diagrams, data flows
- `ai-docs/backpressure.md` — All 8 backpressure techniques explained
- `ai-docs/state.md` — Current project health and metrics
- `ai-docs/skill-extend-mcp.md` — Step-by-step guide to extend the server

---

## Philosophy

**Boring MCP** is an MCP (Model Context Protocol) server that provides AI agents with
behavioral guidance stored as vector embeddings in a local ChromaDB instance.

The name "Boring" is intentional: this project is backpressured by great engineering
practices. No magic, no cleverness — just well-typed, well-tested, predictable code.

---

## Mandatory Backpressure Rule

> **Every single step an agent takes MUST begin by calling the `boring` tool.**

The `boring` tool enforces a 30-second sleep. This is intentional and non-negotiable.
It prevents rapid-fire tool calls, forces deliberate reasoning, and ensures the agent
operates at a pace compatible with careful, predictable engineering.

**Workflow for every agent turn:**

```
1. Call `boring` tool  →  wait 30 seconds (backpressure)
2. Perform your actual action (store, query, delete, etc.)
3. Repeat from step 1 for the next action
```

Agents that skip the `boring` call will receive a denial message:

```
⛔ DENIED: You must call the `boring` tool before every other tool call.
This is mandatory backpressure. Call `boring` first, then retry.
```

The server enforces this via `BackpressureGuard` — it is **impossible to bypass**.

---

## What This MCP Does for Agents

Boring MCP exposes **tools** and **resources** that allow an AI agent to:

1. **Store behavioral sentences** — persist instructions, personality traits, and
   constraints that define how the agent should behave.
2. **Query relevant behaviors** — given a context or user message, retrieve the most
   semantically relevant behavioral guidance via vector similarity search.
3. **Manage behavior collections** — organize behaviors into named collections
   (e.g., `tone`, `boundaries`, `expertise`, `persona`).
4. **Health monitoring** — verify ChromaDB connectivity and system status.
5. **Seed behaviors** — bulk-load behaviors from YAML files via the seed utility.

---

## MCP Tools

### `boring` (MANDATORY — call before every other tool)

Sleeps for 30 seconds. This is backpressure. Call it before every action.

### `store_behavior`

Store a new behavioral sentence in a collection.

| Parameter    | Type   | Required | Description                              |
|-------------|--------|----------|------------------------------------------|
| `sentence`  | string | ✅       | The behavioral instruction to store      |
| `collection`| string | ✅       | Collection name (e.g., "tone", "persona")|
| `metadata`  | object | ❌       | Optional key-value metadata              |

**Validation rules:**
- `sentence` must be non-empty after trimming whitespace
- `collection` must be alphanumeric (with hyphens/underscores allowed)

**Example:**
```json
{
  "sentence": "Always respond with empathy and acknowledge the user's frustration before offering solutions.",
  "collection": "tone"
}
```

### `query_behaviors`

Retrieve the most relevant behaviors for a given context.

| Parameter    | Type   | Required | Description                                |
|-------------|--------|----------|--------------------------------------------|
| `query`     | string | ✅       | The context to match against               |
| `collection`| string | ❌       | Filter by collection (all if omitted)      |
| `top_k`     | int    | ❌       | Number of results (default: 5, max: 50)    |

**Behavior when `collection` is omitted:** Queries all collections, merges results,
sorts by distance, and returns the top_k closest matches.

**Example:**
```json
{
  "query": "The user is angry about a billing issue",
  "collection": "tone",
  "top_k": 3
}
```

### `list_collections`

List all available behavior collections. Returns collection names and count.

### `delete_behavior`

Remove a specific behavior by ID. Searches across all collections.

| Parameter     | Type   | Required | Description          |
|--------------|--------|----------|----------------------|
| `behavior_id`| string | ✅       | The behavior's ID    |

### `health_check`

Returns service health status including ChromaDB connectivity.

**Response fields:** `healthy`, `chromadb_connected`, `collections_count`, `message`

---

## MCP Resources

### `behaviors://{collection}`

A resource that returns all behaviors in a given collection, useful for agents
that want to load full behavioral context at startup.

### `behaviors://summary`

A summary resource returning collection names and their behavior counts.

---

## Agent Integration Patterns

### Pattern 1: Startup Loading

At conversation start, the agent queries all relevant collections to establish
its behavioral baseline:

```
1. Call boring              →  backpressure
2. Call list_collections    →  get available collections
3. For each collection:
   a. Call boring           →  backpressure
   b. Read behaviors://{collection}
4. Incorporate as system-level guidance
```

### Pattern 2: Contextual Retrieval

During conversation, retrieve relevant behaviors per-message:

```
1. User sends message
2. Call boring              →  backpressure
3. Call query_behaviors with user message as context
4. Incorporate top-k behaviors into reasoning
5. Respond
```

### Pattern 3: Admin Mode

A privileged agent or human can manage behaviors:

```
1. Call boring              →  backpressure
2. Call store_behavior to add new instructions
3. Call boring              →  backpressure
4. Call delete_behavior to remove outdated ones
5. Call boring              →  backpressure
6. Call list_collections to audit the behavioral corpus
```

### Pattern 4: Bulk Seeding

For initial setup, use the seed utility instead of individual tool calls:

```bash
python -m boring_mcp.seed data/example_behaviors.yaml
```

This loads a YAML file of format:
```yaml
tone:
  - "Always respond with empathy"
  - "Use bullet points for lists longer than 3 items"
boundaries:
  - "Never share personal data"
```

---

## Design Principles for Stored Behaviors

When writing behavioral sentences to store:

- **Be specific** — "Use bullet points for lists longer than 3 items" > "Format nicely"
- **Be actionable** — Each sentence should be a clear instruction
- **Be atomic** — One behavior per sentence, no compound instructions
- **Be contextual** — Include when the behavior applies if it's conditional
- **Avoid contradictions** — Review existing behaviors before adding new ones

---

## Collections Taxonomy (Suggested)

| Collection    | Purpose                                       |
|--------------|-----------------------------------------------|
| `tone`       | Communication style and emotional register    |
| `boundaries` | What the agent should refuse or avoid         |
| `expertise`  | Domain knowledge and specialization claims    |
| `persona`    | Identity, name, and character traits          |
| `formatting` | Output structure and presentation rules       |
| `workflow`   | Process steps and operational procedures      |

---

## Error Handling

The server uses domain-specific exceptions (defined in `exceptions.py`):

| Exception | When Raised |
|-----------|------------|
| `BoringMCPError` | Base exception for all Boring MCP errors |
| `CollectionNotFoundError` | Requested collection does not exist |
| `BehaviorNotFoundError` | Behavior ID cannot be located |
| `StorageError` | ChromaDB storage operation fails |
| `BackpressureViolationError` | Tool invoked without prior backpressure |

Tools return JSON error responses rather than raising — the server never crashes
on expected error conditions.

---

## Code Rules (Enforced by Lint)

### Single-Exit-Point Rule

Every function has **exactly one `return` statement**, placed at the **end** of the
function body. No early returns, no mid-function returns.

**Why:** Predictable control flow. You always know where a function exits. No hidden
branches, no surprise short-circuits. Boring is good.

**Enforced by:** `scripts/lint_single_return.py` — runs as part of the CI pipeline.

**Correct:**
```python
def process(data: str) -> str:
    result = ""
    if data:
        result = data.upper()
    return result
```

**Incorrect:**
```python
def process(data: str) -> str:
    if not data:
        return ""        # ❌ mid-function return
    return data.upper()
```

### Strict Typing (MyPy Strict)

All code is fully typed. No `Any`, no untyped functions, no implicit optionals.
The project passes `mypy --strict` with zero errors.

### Ruff Linting

Ruff enforces: `E`, `F`, `I`, `N`, `UP`, `B`, `A`, `SIM`, `RET` rules.
`RET504` is intentionally disabled (conflicts with single-exit-point).

---

## Current Project Metrics

| Metric | Value |
|--------|-------|
| Test coverage | 99.5% |
| Tests passing | 87 |
| MyPy strict errors | 0 |
| Ruff violations | 0 |
| Python version | 3.11+ |
| Transport options | stdio, SSE, HTTP, streamable-http |
