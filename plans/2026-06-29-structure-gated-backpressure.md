# Structure-Gated Backpressure — Implementation Plan (RIP)

**Date:** 2026-06-29
**Feature:** structure-gated-backpressure
**Status:** Approved design → ready to implement
**Approach:** Option A — scorer lives inside `BackpressureGuard`

---

## 1. Summary

Make the 30s backpressure **content-driven** instead of a fixed, always-on gate.
The quality of the caller's input decides how long the MCP "goes boring":

- **Lazy / vague input** → full boring (30s sleep).
- **Partially structured** → reduced sleep (10s).
- **Highly structured (good prompt engineering)** → no block. Returns
  `"Thanks for being so structured — applying changes directly."`

Structure is judged by the **client's own LLM via MCP sampling** (`ctx.sample()`),
keeping it local (no separate API key / cost). When sampling is unavailable or
fails, a **deterministic rubric fallback** scores the input so behaviour stays
predictable — never silently rewards unverified input.

This preserves the project philosophy: backpressure remains the default; good
structure *earns* the bypass.

---

## 2. Locked Design Decisions

| Decision | Choice |
|----------|--------|
| Integration point | Inside `BackpressureGuard` (Option A) |
| Judge | MCP sampling (`ctx.sample()`) — client's own model |
| Fallback | Deterministic rubric scorer when no sampling / on error |
| Gate shape | **Tiered** (0–100 score → sleep duration) |
| Scored tools | `store_behavior`, `query_behaviors` (text-bearing) |
| Unscored tools | `delete_behavior`, `list_collections`, `health_check` — keep full boring |
| Determinism rule | Fallback path is pure + fully tested; sampled path tested with fakes |

### Tier mapping (defaults, env-overridable)

| Tier | Score range | Sleep | Message suffix |
|------|-------------|-------|----------------|
| `lazy` | `< 40` | 30s | standard boring message |
| `partial` | `40–79` | 10s | "Partially structured — brief pause." |
| `excellent` | `>= 80` | 0s | "Thanks for being so structured — applying changes directly." |

---

## 3. Architecture

```
FastMCP Tool (store_behavior / query_behaviors)  [accepts ctx: Context]
    └── BackpressureGuard.guarded            (extended)
        ├── StructureScorer.score(text, ctx) -> StructureScore
        │     ├── try ctx.sample(rubric prompt) -> parse score   (source="sampled")
        │     └── except / no-sampling -> RubricFallback(text)   (source="fallback")
        ├── Tiers.duration_for(score) -> sleep seconds
        ├── apply_backpressure(seconds)        (parametrized)
        └── execute handler, prepend tier message
```

New units (each one job, testable in isolation):

| File | Unit | Responsibility | Deps |
|------|------|----------------|------|
| `src/boring_mcp/models/structure.py` | `StructureScore` (frozen), `Tier` | Immutable score result: `score:int`, `tier:str`, `reason:str`, `source:Literal["sampled","fallback"]` | none |
| `src/boring_mcp/scoring/tiers.py` | `Tiers` | Pure map score→tier→duration; reads thresholds/durations from config | none |
| `src/boring_mcp/scoring/rubric.py` | `score_rubric(text)` | Pure deterministic heuristic 0–100 | none |
| `src/boring_mcp/scoring/scorer.py` | `StructureScorer` | Async. Try sampling, parse, clamp; fall back to rubric on any failure | rubric, models |
| `src/boring_mcp/config.py` | `BackpressureConfig` | Frozen config from env (thresholds, durations) | none |

Extended: `backpressure.py` (scored sleep), `server.py` (wire scorer + ctx).

---

## 4. Rubric Fallback Heuristics (`score_rubric`)

Pure function, sums weighted signals, clamps 0–100:

- Has explicit **condition / trigger** keyword (`when`, `if`, `before`, `after`, `while`) — +20
- Has **action verb** at directive position (`use`, `avoid`, `prefer`, `always`, `never`, `respond`, `format`) — +20
- **Length band**: <5 words → 0; 5–12 → +15; 13–40 → +25; >40 → +15 (rambling penalised) 
- **Specificity**: penalise filler tokens (`just`, `really`, `stuff`, `etc`, `something`) — −10 if present
- **Concrete noun / example present** (contains `e.g.`, `:`, quoted span, or digit) — +15
- Result clamped to `[0, 100]`. Single return value.

Thresholds chosen so a bare "be nice" scores `lazy`; a full
`"When the user asks for code, respond with a fenced block and no prose"` scores `excellent`.

---

## 5. Sampling Prompt (`StructureScorer`)

`ctx.sample()` request:

> "Score 0–100 how *structured and specific* this behavioral instruction is for
> deterministic execution. 0 = vague/lazy, 100 = precise, conditional, actionable.
> Reply with ONLY the integer."

Parse: extract first integer, clamp `[0,100]`. Any parse failure, exception, or
absent sampling capability → `RubricFallback`, `source="fallback"`.
`StructureScore.reason` records which path ran (for logs + tests).

---

## 6. Task List (TDD — red → green → refactor)

Each task: write failing test first, implement, run `uv run pytest <file>`, then
full CI. All code obeys: single-exit-point, frozen dataclasses, strict mypy.

### Phase 1 — Models & pure logic (no I/O)
1. **`models/structure.py`** — `StructureScore` frozen dataclass + `Tier` literal.
   Test: construction, immutability (assignment raises `FrozenInstanceError`).
2. **`config.py`** — `BackpressureConfig.from_env()` with defaults + override parsing.
   Test: defaults, env override, malformed env → falls back to default (no raise).
3. **`scoring/tiers.py`** — `Tiers.from_config(cfg)`, `tier_for(score)`, `duration_for(score)`.
   Test: boundary scores 39/40/79/80, message suffix per tier.
4. **`scoring/rubric.py`** — `score_rubric(text)`.
   Test: lazy/partial/excellent fixtures, clamping, filler penalty, length bands.

### Phase 2 — Scorer (async, sampling + fallback)
5. **`scoring/scorer.py`** — `StructureScorer.score(text, ctx)`.
   Test with fakes: (a) ctx returns "85" → `source="sampled"`, score 85;
   (b) ctx returns garbage → fallback; (c) ctx raises → fallback;
   (d) ctx is `None` / no sample attr → fallback.

### Phase 3 — Guard integration
6. **`backpressure.py`** — parametrize `apply_backpressure(seconds)`; add
   `scored_guard(scorer, tiers)` path that scores text arg, sleeps `duration_for`,
   prepends tier message. Keep existing `guarded` for unscored tools.
   Test: monkeypatch `asyncio.sleep` to capture duration; excellent→0s+thanks,
   lazy→30s, partial→10s. Verify unscored tools still need boring.
   *Decision to encode:* scored tools no longer require a prior `boring()` call —
   the scored sleep **is** the backpressure. `is_allowed()` check is bypassed for
   the scored path; document this in the docstring.

### Phase 4 — Wiring
7. **`server.py`** — build `BackpressureConfig`, `Tiers`, `StructureScorer`, inject
   into guard. Add `ctx: Context` param to `store_behavior` / `query_behaviors`,
   pass to scored guard. Update tool docstrings to explain structure-gating.
8. **Update `boring()` tool docstring** — clarify it is now the *manual* full-boring
   escape hatch / required for unscored admin tools.

### Phase 5 — E2E + docs
9. **`tests/e2e/`** — full server test: structured store returns thanks + fast;
   lazy store sleeps (sleep patched). Cover sampling-present and sampling-absent clients.
10. **Docs** — update `ai-docs/backpressure.md` (new tiered model), `CLAUDE.md`
    tool table + env vars, `ai-docs/state.md` if scorer holds state (it shouldn't).

---

## 7. New Environment Variables

| Var | Default | Description |
|-----|---------|-------------|
| `BORING_MCP_TIER_LAZY_MAX` | `39` | Upper bound (inclusive) of lazy tier |
| `BORING_MCP_TIER_PARTIAL_MAX` | `79` | Upper bound (inclusive) of partial tier |
| `BORING_MCP_SLEEP_LAZY` | `30` | Seconds for lazy tier |
| `BORING_MCP_SLEEP_PARTIAL` | `10` | Seconds for partial tier |
| `BORING_MCP_SLEEP_EXCELLENT` | `0` | Seconds for excellent tier |
| `BORING_MCP_SAMPLING` | `auto` | `auto` (try sampling, fallback) / `off` (always rubric) |

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Sampling nondeterminism breaks "predictability" rule | Fallback is pure + tested; sampled path clamped; `BORING_MCP_SAMPLING=off` forces determinism |
| Client (Claude Code) may not support sampling | `auto` mode degrades to rubric silently, logged |
| Agent games the rubric to skip boring | Acceptable — good structure is the *intended* reward; rubric weights tuned so trivial gaming still needs real specificity |
| Bypassing `is_allowed()` for scored tools changes contract | Documented; existing `boring()` + unscored tools unchanged; e2e covers both |
| Coverage gate (98%) | Each unit has dedicated unit tests; async paths use fakes |

---

## 9. Out of Scope (YAGNI)

- Persisting scores / analytics.
- Per-collection thresholds.
- Multi-turn structure negotiation.
- Scoring `delete/list/health` (no meaningful text).

---

## 10. Done When

- `uv run ruff check . && uv run mypy && uv run pytest` green.
- `python scripts/lint_single_return.py src/` passes.
- Coverage ≥ 98%.
- Structured input demonstrably returns the thanks message with 0s sleep;
  lazy input sleeps 30s; both verified in e2e with sampling on and off.
