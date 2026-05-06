# Boring MCP — Agents Guide

## Philosophy

**Boring MCP** is an MCP (Model Context Protocol) server that provides AI agents with
behavioral guidance stored as vector embeddings in a local ChromaDB instance.

The name "Boring" is intentional: this project is backpressured by great engineering
practices. No magic, no cleverness — just well-typed, well-tested, predictable code.

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
1. Call list_collections → get available collections
2. For each collection, read behaviors://{collection}
3. Incorporate as system-level guidance
```

### Pattern 2: Contextual Retrieval

During conversation, retrieve relevant behaviors per-message:

```
1. User sends message
2. Agent calls query_behaviors with user message as context
3. Agent incorporates top-k behaviors into its reasoning
4. Agent responds
```

### Pattern 3: Admin Mode

A privileged agent or human can manage behaviors:

```
1. Call store_behavior to add new instructions
2. Call delete_behavior to remove outdated ones
3. Call list_collections to audit the behavioral corpus
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
