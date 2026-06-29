# Boring MCP — Roadmap

## Vision

Transform Boring MCP from single-agent behavioral store into **multi-agent behavioral orchestration platform** — still boring, still predictable, powerful enough to coordinate personality, memory, and constraints across any number of AI agents.

---

## Phase 1: Foundation Hardening (v0.2) — In Progress

**Goal:** Harden the existing core with versioning, bulk ops, and collection metadata.

### Done

- [x] Core CRUD tools (store, query, delete, list)
- [x] Backpressure enforcement (server-side guard)
- [x] 98%+ test coverage
- [x] SOLID architecture with Protocol-based repository
- [x] Input validation, structured logging, seed utility
- [x] CI/CD pipeline (lint → test → typecheck)

### Remaining

**Behavior Versioning** — track history of changes per behavior.

- Every `store_behavior` creates a new version, not an overwrite
- `query_behaviors` returns latest by default; `version` param for historical
- Storage: version field + timestamp in ChromaDB metadata

**Batch Import/Export** — JSON/YAML bulk operations via tool.

```
→ export_behaviors(collection="tone", format="yaml")
← behaviors.yaml with all entries

→ import_behaviors(file_content="...", collection="tone", format="yaml")
← {"imported": 12, "skipped": 2, "errors": 0}
```

**Collection Metadata** — descriptions, schemas, access rules per collection.

```
→ set_collection_meta("tone", description="Communication style rules", schema={"priority": "low|medium|high"})
→ get_collection_meta("tone")
← {"description": "...", "schema": {...}, "count": 7}
```

### Acceptance Criteria

- [ ] Version history survives server restart
- [ ] Batch import idempotent (re-import same file = no duplicates)
- [ ] Collection metadata persisted in ChromaDB
- [ ] All new tools covered at 98%+ test coverage
- [ ] mypy strict + ruff clean

---

## Phase 2: Intelligence Layer (v0.3) — Planned

**Goal:** Make the server smarter: auto-inject behaviors, detect conflicts, support priority weighting.

### Features

**1. Contextual Behavior Routing** — auto-inject relevant behaviors without agent manually calling `query_behaviors`.

```
Agent sends message → MCP intercepts → auto-queries relevant behaviors
→ prepends to response context → agent sees behaviors transparently
```

- New `auto_context` resource — behaviors matched to last N messages
- Optional "behavior injection" middleware in transport layer
- Config flag to enable/disable (default: off — preserves existing behavior)

**2. Behavior Conflict Detection** — on `store_behavior`, cross-check for semantic contradictions with existing behaviors.

```
→ store_behavior("Always say yes", "tone")
← ⚠️ CONFLICT: Existing behavior "Refuse harmful requests" (collection: boundaries)
   conflicts at distance 0.21. Store anyway? Pass override=True to force.
```

- Cross-collection similarity search triggered on every store
- Configurable threshold: `BORING_MCP_CONFLICT_THRESHOLD` (default: `0.3`)
- Returns conflict warning in response; does NOT store unless `override=True`

**3. Behavior Priority/Importance Scoring** — weight metadata for retrieval ordering.

```
→ store_behavior("Never lie", "boundaries", metadata={"priority": "critical"})
→ store_behavior("Use emojis sparingly", "formatting", metadata={"priority": "low"})
```

Priority levels: `critical > high > medium > low`

- Query results sorted by `priority × relevance_score`
- `critical` behaviors always included regardless of distance threshold

### Acceptance Criteria

- [ ] `auto_context` resource returns contextually relevant behaviors
- [ ] Conflict detection fires on every `store_behavior` call
- [ ] `override=True` bypasses conflict check
- [ ] Priority metadata affects result ranking
- [ ] Critical behaviors always surface in query results
- [ ] New env var `BORING_MCP_CONFLICT_THRESHOLD` documented
- [ ] 98%+ coverage on all new paths

---

## Phase 3: Multi-Agent (v0.4) — Planned

**Goal:** Support multiple agents with named profiles, scoped collections, and behavior inheritance.

### Features

**1. Agent Profiles** — named configurations bundling multiple collections.

```
→ create_profile("support-agent", collections=["tone", "boundaries", "support-workflow"])
→ load_profile("support-agent")
← All behaviors from those collections, merged and ranked
```

Tools needed: `create_profile`, `load_profile`, `delete_profile`, `list_profiles`

**2. Shared vs. Private Collections** — collection naming convention enforces scope.

| Prefix | Example | Scope |
|--------|---------|-------|
| `shared:` | `shared:tone` | All agents read |
| `agent:{id}:` | `agent:support-1:memory` | Scoped to one agent |
| (none) | `tone` | Legacy / unscoped |

- Profiles declare which shared + private collections to load
- Private collections invisible to other agents

**3. Behavior Inheritance** — profiles inherit from parent profiles, conflicts resolved by specificity (child wins).

```
base-agent → support-agent → premium-support-agent
```

- `create_profile("premium-support-agent", parent="support-agent", collections=[...])`
- On `load_profile`: flatten inheritance chain, child behaviors override parent on conflict

### Data Model

```python
@dataclass(frozen=True)
class Profile:
    name: str
    collections: list[str]
    parent: str | None = None
    description: str | None = None
```

### Acceptance Criteria

- [ ] `create_profile` / `load_profile` / `delete_profile` / `list_profiles` tools work
- [ ] Shared/private collection scoping enforced
- [ ] Inheritance chain resolves correctly (child overrides parent)
- [ ] Circular inheritance raises clear error
- [ ] 98%+ coverage on all new paths

---

## Phase 4: Observability & Analytics (v0.5) — Planned

**Goal:** Understand which behaviors are used, effective, and safe to prune.

### Features

**1. Usage Analytics** — track retrieval frequency per behavior.

```
→ behavior_stats(collection="tone", period="7d")
← {
    "most_retrieved": [{"id": "...", "sentence": "...", "count": 42}],
    "never_retrieved": [{"id": "...", "sentence": "..."}],
    "avg_relevance": 0.72
  }
```

- Increment counter on every `query_behaviors` result inclusion
- Store counters in ChromaDB metadata or lightweight SQLite sidecar
- `behavior_stats` tool aggregates over time window

**2. Behavior Effectiveness Scoring** — correlate retrieval with agent outcome quality.

- Agent reports outcome after interaction: `record_outcome(behavior_ids=[...], success=True)`
- Behaviors retrieved before success → score up; before failure/escalation → score down
- New tool: `suggest_retirement(collection, threshold=0.3)` — surfaces low-scoring behaviors

**3. Audit Log** — immutable append-only log of all behavior mutations.

```
→ audit_log(collection="boundaries", limit=20)
← [
    {"action": "store", "id": "...", "sentence": "...", "timestamp": "2026-06-09T10:00:00Z", "agent": "admin"},
    {"action": "delete", "id": "...", "timestamp": "2026-06-09T10:05:00Z", "agent": "admin"}
  ]
```

- Append-only log file or SQLite table (never mutated)
- `audit_log` tool with filters: collection, action, time range, limit
- Analytics data at `BORING_MCP_ANALYTICS_PATH` (default: `./data/analytics.db`)

### Acceptance Criteria

- [ ] `behavior_stats` returns retrieval counts and never-retrieved list
- [ ] `record_outcome` updates effectiveness scores
- [ ] `suggest_retirement` surfaces behaviors below threshold
- [ ] Audit log is append-only (no delete/update)
- [ ] Analytics survive server restart
- [ ] 98%+ coverage on all new paths

---

## Phase 5: Ecosystem (v1.0) — Planned

**Goal:** Make Boring MCP composable, portable, and community-extensible.

### Features

**1. Behavior Marketplace** — publish and subscribe to behavior packs.

```
→ install_behavior_pack("customer-support-v2")
← {"installed": 47, "collections": ["tone", "boundaries", "workflow"], "source": "@boring-mcp/support-pack"}
```

Pack format: YAML file with behaviors + collection assignments + metadata. Registry: Git repo or HTTP endpoint — packs are URLs, no central authority required.

**2. Multi-Backend Support** — swap ChromaDB for other vector stores via repository protocol.

| Backend | Use case |
|---------|----------|
| `ChromaRepository` | Default — local persistent (current) |
| `PineconeRepository` | Cloud-scale, managed |
| `QdrantRepository` | Self-hosted with rich filtering |
| `PgvectorRepository` | Teams already on Postgres |
| `SqliteRepository` | Zero-dependency local option |

New env var: `BORING_MCP_BACKEND=chroma|pinecone|qdrant|pgvector|sqlite`. Optional extras: `pip install boring-mcp[pinecone]`, `boring-mcp[qdrant]`.

**3. Webhook Notifications** — fire webhooks on behavior events.

```yaml
webhooks:
  - event: behavior.stored
    url: https://my-app.com/hooks/behavior-changed
  - event: conflict.detected
    url: https://my-app.com/hooks/conflict-alert
```

Events: `behavior.stored`, `behavior.deleted`, `conflict.detected`, `behavior.retired`

**4. MCP Composition** — Boring MCP as behavioral layer in larger MCP chains.

```
Agent → Router MCP → Boring MCP (personality)
                   → Memory MCP (conversation history)
                   → Tool MCP (capabilities)
```

### Acceptance Criteria

- [ ] `install_behavior_pack` / `uninstall_behavior_pack` / `list_behavior_packs` work
- [ ] At least 2 non-Chroma backends implemented and tested
- [ ] Webhooks fire reliably (with retry on failure)
- [ ] Composition guide in `ai-docs/`
- [ ] 98%+ coverage on all new paths

---

## Phase 6: Enterprise (v2.0) — Planned

**Goal:** Multi-tenant isolation, role-based access, compliance workflows.

### Features

**1. Multi-Tenant Isolation** — complete data isolation per tenant, shared infrastructure.

- Tenant-scoped collections: `tenant:{id}:{collection}`
- API key authentication per tenant (header: `X-Boring-API-Key`)
- Usage quotas: max behaviors per collection, max queries per hour

**2. Role-Based Access Control**

| Role | Permissions |
|------|-------------|
| `admin` | Full CRUD on all collections |
| `editor` | store/delete on assigned collections only |
| `reader` | query only |
| `agent` | query only + mandatory backpressure |

- Roles assigned per API key; collection-level overrides supported
- Unauthorized attempts return structured error (not silent fail)

**3. Compliance & Governance** — approval workflows for sensitive collections.

```
→ store_behavior("...", "boundaries")
← {"id": "...", "status": "pending_review"}  # Not active until approved

→ approve_behavior("abc-123", reviewer="admin@acme.com")
← {"id": "...", "status": "approved", "active": true}
```

- Auth middleware wraps all tools before `BackpressureGuard`
- Approval state stored in SQLite sidecar
- All enterprise features behind `BORING_MCP_ENTERPRISE=true` flag
- GDPR export + SOC2 audit trails

### Acceptance Criteria

- [ ] Tenant isolation: tenant A cannot read/write tenant B data
- [ ] API key auth enforced on all tool calls
- [ ] RBAC: unauthorized operations return `403`-equivalent structured error
- [ ] Approval workflow: `pending` behaviors not returned in `query_behaviors`
- [ ] GDPR export: all behaviors for a tenant exportable as JSON
- [ ] Audit log includes reviewer identity
- [ ] 98%+ coverage on all new paths

---

## Technical Debt

| Item | Priority | Effort | Notes |
|------|----------|--------|-------|
| Replace `type: ignore` in `chroma.py` with proper typed wrappers | Medium | Small | ChromaDB SDK has loose types; wrap at boundary |
| Add OpenTelemetry tracing | Low | Medium | Spans for every tool call + ChromaDB query |
| Connection pooling for `PersistentClient` | Medium | Small | Reuse client across requests |
| Async repository layer (currently sync) | Low | Large | ChromaDB sync calls block event loop |
| Property-based testing (Hypothesis) | Low | Medium | Fuzz input validation + serialization |
| Benchmark suite for query latency | Medium | Small | p50/p95/p99 for `query_behaviors` at various collection sizes |
| Docker image + Helm chart | Medium | Medium | `ghcr.io/boring-mcp/boring-mcp:latest` |
| SDK client library (Python + TypeScript) | High | Large | Typed wrappers for all tools; auto-generated from tool schemas |

### Notes

**Typed Chroma Wrappers:** `src/boring_mcp/repositories/chroma.py` uses `# type: ignore` due to ChromaDB SDK returning `Any`. Fix: typed wrapper classes at import boundary. Zero behavior change.

**Async Repository:** Current sync `ChromaRepository` calls via `asyncio.to_thread`. Target: native async protocol + async ChromaDB client (available in chromadb >= 0.5). Risk: large refactor — do after Phase 2 stabilizes.

**SDK Client Library:** Most impactful for adoption. Auto-generate from FastMCP tool schemas — `boring_mcp_sdk.py` (Python) + `boring-mcp-sdk` npm package (TypeScript).
