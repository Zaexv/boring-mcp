# Boring MCP — Feature Roadmap

## Vision

Transform Boring MCP from a single-agent behavioral store into a **multi-agent
behavioral orchestration platform** — still boring, still predictable, but
powerful enough to coordinate personality, memory, and constraints across
any number of AI agents.

---

## Phase 1: Foundation Hardening (Current → v0.2)

### ✅ Done
- [x] Core CRUD tools (store, query, delete, list)
- [x] Backpressure enforcement (server-side guard)
- [x] 98%+ test coverage
- [x] SOLID architecture with Protocol-based repository
- [x] Input validation, structured logging, seed utility
- [x] CI/CD pipeline (lint → test → typecheck)

### 🔜 Next
- [ ] **Behavior versioning** — track history of changes per behavior
- [ ] **Batch import/export** — JSON/YAML bulk operations via tool
- [ ] **Collection metadata** — descriptions, schemas, access rules per collection

---

## Phase 2: Intelligence Layer (v0.3)

### Contextual Behavior Routing

Instead of the agent manually calling `query_behaviors`, the server
automatically injects relevant behaviors based on the conversation context.

```
Agent sends message → MCP intercepts → auto-queries relevant behaviors
→ prepends to response context → agent sees behaviors transparently
```

**Implementation:**
- New `auto_context` resource that returns behaviors matched to the last N messages
- Optional "behavior injection" middleware in the transport layer

### Behavior Conflicts Detection

When storing a new behavior, check for semantic contradictions with existing ones:

```
→ store_behavior("Always say yes", "tone")
← ⚠️ CONFLICT: Existing behavior "Refuse harmful requests" (collection: boundaries)
   conflicts with this instruction. Store anyway? (provide override flag)
```

**Implementation:**
- Cross-collection similarity search on store
- Configurable conflict threshold (distance < 0.3 = likely conflict)

### Behavior Importance Scoring

Not all behaviors are equal. Add weight/priority metadata:

```
→ store_behavior("Never lie", "boundaries", metadata={"priority": "critical"})
→ store_behavior("Use emojis sparingly", "formatting", metadata={"priority": "low"})
```

- Query results sorted by priority × relevance
- Critical behaviors always surface regardless of distance

---

## Phase 3: Multi-Agent (v0.4)

### Agent Profiles

Named agent configurations that bundle collections:

```
→ create_profile("support-agent", collections=["tone", "boundaries", "support-workflow"])
→ load_profile("support-agent")
← Returns all behaviors from those collections, merged and ranked
```

### Shared vs. Private Collections

- **Shared**: `tone`, `boundaries` — same across all agents
- **Private**: `agent-1-memory`, `agent-2-persona` — scoped per agent

**Implementation:**
- Collection naming convention: `shared:tone`, `agent:support-1:memory`
- Profile-based access control

### Behavior Inheritance

Profiles can inherit from parent profiles:

```
base-agent → support-agent → premium-support-agent
```

Each level adds/overrides behaviors. Conflicts resolved by specificity.

---

## Phase 4: Observability & Analytics (v0.5)

### Usage Analytics

Track which behaviors are actually retrieved and how often:

```
→ behavior_stats(collection="tone", period="7d")
← {"most_retrieved": [...], "never_retrieved": [...], "avg_relevance": 0.72}
```

Identifies dead behaviors that can be pruned.

### Behavior Effectiveness Scoring

Track correlation between behavior retrieval and agent outcome quality:

- Behaviors retrieved before successful interactions → score up
- Behaviors retrieved before failures/escalations → score down
- Auto-suggest behavior retirement for consistently low-scoring ones

### Audit Log

Immutable log of all behavior changes:

```
→ audit_log(collection="boundaries", limit=20)
← [{"action": "store", "sentence": "...", "timestamp": "...", "agent": "admin"}]
```

---

## Phase 5: Ecosystem (v1.0)

### Behavior Marketplace

Publish and subscribe to behavior packs:

```
→ install_behavior_pack("customer-support-v2")
← Installed 47 behaviors across 5 collections from @boring-mcp/support-pack
```

### Multi-Backend Support

Repository implementations for:
- **Pinecone** — cloud-scale vector search
- **Qdrant** — self-hosted with filtering
- **PostgreSQL + pgvector** — for teams already on Postgres
- **SQLite + embeddings** — zero-dependency local option

### Webhook Notifications

Fire webhooks when behaviors change:

```yaml
webhooks:
  - event: behavior.stored
    url: https://my-app.com/hooks/behavior-changed
  - event: conflict.detected
    url: https://my-app.com/hooks/conflict-alert
```

### MCP Composition

Boring MCP as a building block in larger MCP chains:

```
Agent → Router MCP → Boring MCP (personality)
                   → Memory MCP (conversation history)
                   → Tool MCP (actual capabilities)
```

---

## Phase 6: Enterprise (v2.0)

### Multi-Tenant Isolation

Complete data isolation per tenant with shared infrastructure:

- Tenant-scoped ChromaDB collections
- API key authentication per tenant
- Usage quotas and rate limiting (beyond backpressure)

### Role-Based Access Control

```
admin   → full CRUD on all collections
editor  → store/delete on assigned collections
reader  → query only
agent   → query only (with mandatory backpressure)
```

### Compliance & Governance

- Behavior approval workflows (store → pending → approved)
- Mandatory review for `boundaries` collection changes
- Export for compliance audits (GDPR, SOC2)

---

## Technical Debt & Improvements

| Item | Priority | Effort |
|------|----------|--------|
| Replace `type: ignore` in chroma.py with proper typed wrappers | Medium | Small |
| Add OpenTelemetry tracing | Low | Medium |
| Connection pooling for PersistentClient | Medium | Small |
| Async repository layer (currently sync) | Low | Large |
| Property-based testing (Hypothesis) | Low | Medium |
| Benchmark suite for query latency | Medium | Small |
| Docker image + Helm chart | Medium | Medium |
| SDK client library (Python + TypeScript) | High | Large |

---

## Contributing

See [`ai-docs/skill-extend-mcp.md`](../ai-docs/skill-extend-mcp.md) for the
step-by-step guide to adding new tools, resources, and capabilities while
maintaining all architectural constraints.
