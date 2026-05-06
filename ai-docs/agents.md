# Boring MCP — Agents Guide

## ⚠️ Location Notice

All AI-facing documentation lives in the **`ai-docs/`** folder at the repository root.
When searching for architectural guidance, behavioral contracts, or tool schemas,
always look in `ai-docs/`.

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

Agents that skip the `boring` call are violating the protocol. The MCP server may
reject subsequent calls if backpressure is not respected.

---

## What This MCP Does for Agents

Boring MCP exposes **tools** and **resources** that allow an AI agent to:

1. **Store behavioral sentences** — persist instructions, personality traits, and
   constraints that define how the agent should behave.
2. **Query relevant behaviors** — given a context or user message, retrieve the most
   semantically relevant behavioral guidance via vector similarity search.
3. **Manage behavior collections** — organize behaviors into named collections
   (e.g., `tone`, `boundaries`, `expertise`, `persona`).

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
| `top_k`     | int    | ❌       | Number of results (default: 5)             |

**Example:**
```json
{
  "query": "The user is angry about a billing issue",
  "collection": "tone",
  "top_k": 3
}
```

### `list_collections`

List all available behavior collections.

### `delete_behavior`

Remove a specific behavior by ID.

| Parameter | Type   | Required | Description          |
|-----------|--------|----------|----------------------|
| `id`      | string | ✅       | The behavior's ID    |

### `health_check`

Returns service health status including ChromaDB connectivity.

---

## MCP Resources

### `behaviors://{collection}`

A resource that returns all behaviors in a given collection, useful for agents
that want to load full behavioral context at startup.

### `behaviors://summary`

A summary resource returning collection names and counts.

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
