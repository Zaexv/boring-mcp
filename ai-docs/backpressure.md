# Boring MCP — Backpressure Techniques

## What Is Backpressure?

Backpressure is a flow-control mechanism that slows producers when consumers can't
keep up. In Boring MCP, the "producer" is the AI agent making rapid tool calls, and
the "consumer" is the system (and the human) that needs time to absorb, validate,
and act on each change.

Backpressure here is **intentional friction** — it forces deliberate, careful behavior
from agents that would otherwise blast through actions at machine speed.

---

## Techniques Used

### 1. Mandatory Sleep Gate (`boring` tool)

**What:** Every tool call must be preceded by a call to the `boring` tool, which
enforces a 30-second `asyncio.sleep`.

**Implementation:** `src/boring_mcp/backpressure.py` → `BackpressureGuard`

```python
await asyncio.sleep(BACKPRESSURE_SECONDS)  # 30 seconds, non-negotiable
```

**Why:**
- Prevents rapid-fire tool invocations that could corrupt state or overwhelm ChromaDB
- Forces the agent to "think" between actions — no shotgun approaches
- Makes agent behavior observable by humans in real time (you can watch what it does)
- Rate-limits writes to the vector database without needing external infrastructure
- Emulates real-world latency — agents trained against this won't break in production

---

### 1b. Structure-Gated Backpressure (Adaptive Sleep)

**What:** For the text-bearing tools (`store_behavior`, `query_behaviors`), the
backpressure duration is no longer fixed at 30s — it scales inversely with how
**structured** the caller's input is. Lazy, vague input gets the full boring
pause; precise, conditional, well-engineered input is applied directly with no
sleep. These two tools no longer require a prior `boring` call — the scored sleep
*is* their backpressure. Admin tools (`delete_behavior`, `list_collections`,
`health_check`) keep the mandatory `boring` gate from section 1/2.

**Implementation:**
- `src/boring_mcp/scoring/scorer.py` → `StructureScorer.score()`
- `src/boring_mcp/scoring/rubric.py` → deterministic fallback scorer
- `src/boring_mcp/scoring/tiers.py` → score → tier → duration/message
- `src/boring_mcp/backpressure.py` → `BackpressureGuard.scored_backpressure()`

**Scoring:** the input is judged 0–100 by the **client's own LLM** via MCP
sampling (`ctx.sample()`) — local, no separate API key or cost. When sampling is
unavailable, errors, or is disabled, a **pure deterministic rubric** scores the
input instead, keeping behaviour predictable.

**Tiers (defaults, env-overridable):**

| Tier | Score | Sleep | Response |
|------|-------|-------|----------|
| lazy | `< 40` | 30s | standard boring message |
| partial | `40–79` | 10s | "Partially structured — brief pause." |
| excellent | `>= 80` | 0s | "Thanks for being so structured — applying changes directly." |

**Why:**
- Rewards good prompt engineering with speed; taxes lazy input with friction
- Keeps backpressure as the default — the bypass must be *earned* by structure
- Sampling uses the caller's own model, so judgement is local and free
- The deterministic rubric fallback preserves the predictability rule; set
  `BORING_MCP_SAMPLING=off` to force fully deterministic scoring

---

### 2. Server-Side Enforcement (`BackpressureGuard`)

**What:** The server tracks whether `boring` was called before each tool. If not,
the tool returns a denial message instead of executing.

**Implementation:** `src/boring_mcp/backpressure.py` → `is_allowed()` / `record_tool_call()`

```python
result = guard.denial_message()
if guard.is_allowed():
    guard.record_tool_call()
    result = await actual_handler(...)
return result
```

**Why:**
- Documentation alone doesn't enforce behavior — agents can (and will) ignore it
- Server-side gating makes backpressure **impossible to bypass**
- The denial message teaches the agent what it did wrong and how to fix it
- No trust assumptions — the system enforces the protocol, not the agent's goodwill

---

### 3. Single-Exit-Point Rule (Code Structure)

**What:** Every function has exactly one `return` statement, placed at the end.
No early returns, no mid-function exits.

**Implementation:** `scripts/lint_single_return.py` (AST-based linter)

**Why:**
- Predictable control flow is a form of backpressure on complexity
- Developers (and agents reading code) always know where a function exits
- Eliminates hidden branches that create subtle bugs
- Forces explicit handling of all cases via variables, not escape hatches
- Makes code review trivial: "does the final `return` have the right value?"

---

### 4. Strict Type System (MyPy Strict)

**What:** All code is typed with MyPy in strict mode. No `Any`, no untyped functions,
no implicit optionals.

**Implementation:** `pyproject.toml` → `[tool.mypy] strict = true`

**Why:**
- Types are backpressure on ambiguity — you can't be vague about what goes in/out
- Catches entire categories of bugs before runtime (None-safety, type mismatches)
- Forces explicit decisions at boundaries (Protocol interfaces, return types)
- Slows down "quick hack" code — you must think about types first

---

### 5. Layered Architecture (Forced Indirection)

**What:** Code flows through layers: Transport → Tools → Services → Repository → DB.
No skipping layers.

**Implementation:** Directory structure + import discipline

**Why:**
- Each layer is a checkpoint that validates and transforms data
- Prevents "shortcut" code that bypasses validation
- Makes testing possible at each layer in isolation
- Changes propagate predictably (swap ChromaDB → Pinecone by changing one layer)
- The indirection is the point: more steps = more opportunities to catch errors

---

### 6. Immutable Domain Models (`frozen=True`)

**What:** `Behavior` and `QueryResult` dataclasses are frozen — once created, they
cannot be mutated.

**Implementation:** `@dataclass(frozen=True, slots=True)`

**Why:**
- Eliminates an entire class of bugs (unexpected mutation, aliasing issues)
- Forces creation of new objects instead of modifying existing ones
- Makes data flow explicit and traceable
- Thread-safe by construction (no locks needed)

---

### 7. Ruff Linting with RET Rules

**What:** Ruff enforces return-pattern rules (`RET505`, `RET506`, etc.) to prevent
unnecessary else-after-return and similar anti-patterns.

**Implementation:** `pyproject.toml` → `select = [..., "RET"]`

**Why:**
- Automated enforcement — humans and agents can't "forget" the rules
- Catches structural issues that the single-exit-point linter might miss
- Fast feedback loop (sub-second linting)
- `RET504` is intentionally disabled because it conflicts with single-exit-point

---

### 8. Pre-Commit Hooks (Gate Before Commit)

**What:** `.pre-commit-config.yaml` runs ruff, single-exit-point lint, and mypy
before any code can be committed.

**Implementation:** `.pre-commit-config.yaml`

**Why:**
- Backpressure on commits — bad code literally cannot enter the repository
- Shifts error detection left (at commit time, not in CI)
- No "I'll fix it later" — the hook blocks you now
- Works offline, no CI dependency

---

## Philosophy

> "The purpose of backpressure is not to slow things down. It's to ensure that
> every action that happens is deliberate, validated, and reversible."

In conventional systems, speed is a feature. In Boring MCP, **predictability** is
the feature. Every technique above exists to make the system's behavior boring —
no surprises, no race conditions, no "how did that get there?" moments.

The 30-second sleep isn't punishment. It's a statement: *this system values
correctness over velocity.*
