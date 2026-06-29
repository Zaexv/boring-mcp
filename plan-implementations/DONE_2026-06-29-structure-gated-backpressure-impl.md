# Structure-Gated Backpressure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make backpressure content-driven — the caller's input is scored 0–100 and the boring sleep shrinks as structure improves, reaching 0s for highly structured input.

**Architecture:** A pure rubric scorer plus an async `StructureScorer` (uses the client's own LLM via an injected sampler, falling back to the rubric) feed a score into `BackpressureGuard`, which maps the score to a sleep tier and message. Scoring logic lives in the guard layer (Option A). Only the two text-bearing tools (`store_behavior`, `query_behaviors`) are scored; admin tools keep the existing full-boring gate.

**Tech Stack:** Python 3.11, FastMCP, ChromaDB, pytest + pytest-asyncio, mypy (strict), ruff.

## Global Constraints

- Python `>=3.11`; no new runtime dependencies (sampler injected as a plain callable, FastMCP `Context.sample` wired only in `server.py`).
- **Single-exit-point**: exactly one `return` per function (enforced by `scripts/lint_single_return.py`). `RET504` is ignored — assign to a result var, then return it.
- **Strict mypy**: no `Any`, no implicit optional. Run `uv run mypy`.
- **Immutable models**: all data models `@dataclass(frozen=True)`.
- **Coverage** gate `fail_under = 90`, project target **≥98%**.
- **Ruff** rules `E, F, I, N, UP, B, A, SIM, RET`. Run `uv run ruff check . && uv run ruff format .`.
- Full CI gate: `uv run ruff check . && uv run mypy && uv run pytest && python scripts/lint_single_return.py src/`.
- Tests live under `tests/unit/`, `tests/integration/`, `tests/e2e/`.

---

### Task 1: Structure score model

**Files:**
- Create: `src/boring_mcp/models/structure.py`
- Test: `tests/unit/test_structure_model.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `StructureScore(score: int, tier: str, reason: str, source: str)` frozen dataclass. `source` is `"sampled"` or `"fallback"`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_structure_model.py
import dataclasses

import pytest

from boring_mcp.models.structure import StructureScore


def test_structure_score_holds_fields():
    s = StructureScore(score=85, tier="excellent", reason="sampled=85", source="sampled")
    assert s.score == 85
    assert s.tier == "excellent"
    assert s.reason == "sampled=85"
    assert s.source == "sampled"


def test_structure_score_is_frozen():
    s = StructureScore(score=10, tier="lazy", reason="r", source="fallback")
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.score = 99  # type: ignore[misc]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_structure_model.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'boring_mcp.models.structure'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/boring_mcp/models/structure.py
"""Immutable result of scoring an input's structural quality."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StructureScore:
    """Score for how structured a behavioral input is.

    Attributes:
        score: Integer 0-100. Higher means more structured.
        tier: One of "lazy", "partial", "excellent".
        reason: Short human-readable explanation (path + signal summary).
        source: "sampled" (client LLM) or "fallback" (deterministic rubric).
    """

    score: int
    tier: str
    reason: str
    source: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_structure_model.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/boring_mcp/models/structure.py tests/unit/test_structure_model.py
git commit -m "feat: add StructureScore model"
```

---

### Task 2: Backpressure config from env

**Files:**
- Create: `src/boring_mcp/config.py`
- Test: `tests/unit/test_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `BackpressureConfig(lazy_max: int, partial_max: int, sleep_lazy: int, sleep_partial: int, sleep_excellent: int, sampling: str)` frozen dataclass, and classmethod `BackpressureConfig.from_env(env: Mapping[str, str]) -> BackpressureConfig`. `sampling` is `"auto"` or `"off"`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_config.py
from boring_mcp.config import BackpressureConfig


def test_defaults_when_env_empty():
    cfg = BackpressureConfig.from_env({})
    assert cfg.lazy_max == 39
    assert cfg.partial_max == 79
    assert cfg.sleep_lazy == 30
    assert cfg.sleep_partial == 10
    assert cfg.sleep_excellent == 0
    assert cfg.sampling == "auto"


def test_env_overrides_applied():
    cfg = BackpressureConfig.from_env(
        {
            "BORING_MCP_TIER_LAZY_MAX": "20",
            "BORING_MCP_SLEEP_PARTIAL": "5",
            "BORING_MCP_SAMPLING": "off",
        }
    )
    assert cfg.lazy_max == 20
    assert cfg.sleep_partial == 5
    assert cfg.sampling == "off"


def test_malformed_int_falls_back_to_default():
    cfg = BackpressureConfig.from_env({"BORING_MCP_SLEEP_LAZY": "not-a-number"})
    assert cfg.sleep_lazy == 30


def test_unknown_sampling_value_falls_back_to_auto():
    cfg = BackpressureConfig.from_env({"BORING_MCP_SAMPLING": "weird"})
    assert cfg.sampling == "auto"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'boring_mcp.config'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/boring_mcp/config.py
"""Backpressure tier configuration, loaded from the environment."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

_DEFAULTS: dict[str, int] = {
    "BORING_MCP_TIER_LAZY_MAX": 39,
    "BORING_MCP_TIER_PARTIAL_MAX": 79,
    "BORING_MCP_SLEEP_LAZY": 30,
    "BORING_MCP_SLEEP_PARTIAL": 10,
    "BORING_MCP_SLEEP_EXCELLENT": 0,
}


def _int_env(env: Mapping[str, str], key: str) -> int:
    raw = env.get(key)
    value = _DEFAULTS[key]
    if raw is not None and raw.lstrip("-").isdigit():
        value = int(raw)
    return value


def _sampling_env(env: Mapping[str, str]) -> str:
    raw = env.get("BORING_MCP_SAMPLING", "auto")
    value = raw if raw in ("auto", "off") else "auto"
    return value


@dataclass(frozen=True)
class BackpressureConfig:
    """Tier thresholds and sleep durations for structure-gated backpressure."""

    lazy_max: int
    partial_max: int
    sleep_lazy: int
    sleep_partial: int
    sleep_excellent: int
    sampling: str

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> BackpressureConfig:
        """Build config from an environment mapping, using defaults for gaps."""
        cfg = cls(
            lazy_max=_int_env(env, "BORING_MCP_TIER_LAZY_MAX"),
            partial_max=_int_env(env, "BORING_MCP_TIER_PARTIAL_MAX"),
            sleep_lazy=_int_env(env, "BORING_MCP_SLEEP_LAZY"),
            sleep_partial=_int_env(env, "BORING_MCP_SLEEP_PARTIAL"),
            sleep_excellent=_int_env(env, "BORING_MCP_SLEEP_EXCELLENT"),
            sampling=_sampling_env(env),
        )
        return cfg
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_config.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/boring_mcp/config.py tests/unit/test_config.py
git commit -m "feat: add BackpressureConfig from env"
```

---

### Task 3: Tier mapping

**Files:**
- Create: `src/boring_mcp/scoring/__init__.py` (empty)
- Create: `src/boring_mcp/scoring/tiers.py`
- Test: `tests/unit/test_tiers.py`

**Interfaces:**
- Consumes: `BackpressureConfig` (Task 2).
- Produces: `Tiers` frozen dataclass with `Tiers.from_config(cfg: BackpressureConfig) -> Tiers`, `tier_for(score: int) -> str`, `duration_for(score: int) -> int`, `message_for(score: int) -> str`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_tiers.py
from boring_mcp.config import BackpressureConfig
from boring_mcp.scoring.tiers import Tiers


def _tiers() -> Tiers:
    return Tiers.from_config(BackpressureConfig.from_env({}))


def test_tier_boundaries():
    t = _tiers()
    assert t.tier_for(39) == "lazy"
    assert t.tier_for(40) == "partial"
    assert t.tier_for(79) == "partial"
    assert t.tier_for(80) == "excellent"


def test_duration_per_tier():
    t = _tiers()
    assert t.duration_for(10) == 30
    assert t.duration_for(50) == 10
    assert t.duration_for(90) == 0


def test_message_excellent_thanks():
    t = _tiers()
    assert "Thanks for being so structured" in t.message_for(90)


def test_message_lazy_is_boring():
    t = _tiers()
    assert "30 seconds" in t.message_for(5)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_tiers.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'boring_mcp.scoring'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/boring_mcp/scoring/__init__.py
```

```python
# src/boring_mcp/scoring/tiers.py
"""Maps a structure score to a backpressure tier, duration, and message."""

from __future__ import annotations

from dataclasses import dataclass

from boring_mcp.config import BackpressureConfig

_LAZY_MESSAGE = (
    "You waited 30 seconds. That's the point. "
    "Boring means predictable, reliable, and intentional. No rushing, no shortcuts."
)
_PARTIAL_MESSAGE = "Partially structured — brief pause before applying."
_EXCELLENT_MESSAGE = "Thanks for being so structured — applying changes directly."


@dataclass(frozen=True)
class Tiers:
    """Pure score-to-tier mapping built from configuration."""

    lazy_max: int
    partial_max: int
    sleep_lazy: int
    sleep_partial: int
    sleep_excellent: int

    @classmethod
    def from_config(cls, cfg: BackpressureConfig) -> Tiers:
        """Construct tier mapping from a BackpressureConfig."""
        tiers = cls(
            lazy_max=cfg.lazy_max,
            partial_max=cfg.partial_max,
            sleep_lazy=cfg.sleep_lazy,
            sleep_partial=cfg.sleep_partial,
            sleep_excellent=cfg.sleep_excellent,
        )
        return tiers

    def tier_for(self, score: int) -> str:
        """Return the tier name for a score."""
        tier = "excellent"
        if score <= self.lazy_max:
            tier = "lazy"
        elif score <= self.partial_max:
            tier = "partial"
        return tier

    def duration_for(self, score: int) -> int:
        """Return the sleep seconds for a score."""
        durations = {
            "lazy": self.sleep_lazy,
            "partial": self.sleep_partial,
            "excellent": self.sleep_excellent,
        }
        return durations[self.tier_for(score)]

    def message_for(self, score: int) -> str:
        """Return the user-facing message for a score."""
        messages = {
            "lazy": _LAZY_MESSAGE,
            "partial": _PARTIAL_MESSAGE,
            "excellent": _EXCELLENT_MESSAGE,
        }
        return messages[self.tier_for(score)]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_tiers.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/boring_mcp/scoring/__init__.py src/boring_mcp/scoring/tiers.py tests/unit/test_tiers.py
git commit -m "feat: add tier mapping for structure scores"
```

---

### Task 4: Deterministic rubric scorer

**Files:**
- Create: `src/boring_mcp/scoring/rubric.py`
- Test: `tests/unit/test_rubric.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `score_rubric(text: str) -> int` — pure, returns clamped `[0, 100]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_rubric.py
from boring_mcp.scoring.rubric import score_rubric


def test_empty_is_zero():
    assert score_rubric("") == 0
    assert score_rubric("   ") == 0


def test_lazy_input_scores_low():
    assert score_rubric("be nice") < 40


def test_structured_input_scores_high():
    text = 'When the user asks for code, respond with a fenced block, e.g. ```py```'
    assert score_rubric(text) >= 80


def test_filler_is_penalised():
    plain = "respond with a fenced code block when asked for code examples"
    filler = "just respond with really some fenced code block stuff when asked"
    assert score_rubric(filler) < score_rubric(plain)


def test_score_is_clamped_to_100():
    text = (
        "When the user asks for code, if the file exists, always respond "
        "with a fenced block, e.g. ```py```, never add prose: keep it short"
    )
    assert score_rubric(text) <= 100
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_rubric.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'boring_mcp.scoring.rubric'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/boring_mcp/scoring/rubric.py
"""Deterministic heuristic scorer for structural quality of an input.

Pure fallback used when LLM sampling is unavailable or disabled. Returns an
integer 0-100; higher means more structured and specific.
"""

from __future__ import annotations

_CONDITION_WORDS = ("when", "if", "before", "after", "while", "unless")
_ACTION_WORDS = (
    "use",
    "avoid",
    "prefer",
    "always",
    "never",
    "respond",
    "format",
    "return",
    "keep",
)
_FILLER_WORDS = ("just", "really", "stuff", "etc", "something", "basically")
_CONCRETE_MARKERS = ("e.g.", ":", '"', "`")


def _has_any(low: str, words: tuple[str, ...]) -> bool:
    return any(w in low for w in words)


def _length_points(word_count: int) -> int:
    points = 15
    if word_count < 5:
        points = 0
    elif word_count <= 12:
        points = 15
    elif word_count <= 40:
        points = 25
    return points


def score_rubric(text: str) -> int:
    """Score the structural quality of text as an integer 0-100."""
    cleaned = text.strip()
    low = cleaned.lower()
    words = cleaned.split()
    score = 0
    if cleaned:
        score += _length_points(len(words))
        if _has_any(low, _CONDITION_WORDS):
            score += 20
        if _has_any(low, _ACTION_WORDS):
            score += 20
        if any(m in cleaned for m in _CONCRETE_MARKERS) or any(c.isdigit() for c in cleaned):
            score += 15
        if _has_any(low, _FILLER_WORDS):
            score -= 10
    clamped = max(0, min(100, score))
    return clamped
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_rubric.py -v`
Expected: PASS (5 passed)

Note: if `test_structured_input_scores_high` falls short, the fixture earns length(25) + condition(20) + action(20) + concrete(15) = 80. Do not lower the threshold; verify the markers instead.

- [ ] **Step 5: Commit**

```bash
git add src/boring_mcp/scoring/rubric.py tests/unit/test_rubric.py
git commit -m "feat: add deterministic rubric scorer"
```

---

### Task 5: StructureScorer (sampling + fallback)

**Files:**
- Create: `src/boring_mcp/scoring/scorer.py`
- Test: `tests/unit/test_scorer.py`

**Interfaces:**
- Consumes: `score_rubric` (Task 4), `StructureScore` (Task 1), `Tiers` (Task 3).
- Produces:
  - Type alias `Sampler = Callable[[str], Awaitable[str]]`.
  - `StructureScorer(tiers: Tiers, sampling: str)` frozen dataclass.
  - `async StructureScorer.score(self, text: str, sampler: Sampler | None) -> StructureScore`.
  - Behaviour: when `sampling == "auto"` and `sampler` is not `None`, call sampler, parse first integer, clamp `[0,100]`, `source="sampled"`. On any exception, missing sampler, unparseable reply, or `sampling == "off"`, use `score_rubric`, `source="fallback"`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_scorer.py
import pytest

from boring_mcp.config import BackpressureConfig
from boring_mcp.scoring.scorer import StructureScorer
from boring_mcp.scoring.tiers import Tiers

pytestmark = pytest.mark.asyncio


def _scorer(sampling: str = "auto") -> StructureScorer:
    return StructureScorer(tiers=Tiers.from_config(BackpressureConfig.from_env({})), sampling=sampling)


async def test_uses_sampler_when_available():
    async def sampler(_prompt: str) -> str:
        return "The score is 85 out of 100"

    result = await _scorer().score("when X do Y", sampler)
    assert result.score == 85
    assert result.source == "sampled"
    assert result.tier == "excellent"


async def test_garbage_reply_falls_back():
    async def sampler(_prompt: str) -> str:
        return "no number here"

    result = await _scorer().score("be nice", sampler)
    assert result.source == "fallback"


async def test_sampler_exception_falls_back():
    async def sampler(_prompt: str) -> str:
        raise RuntimeError("sampling not supported")

    result = await _scorer().score("be nice", sampler)
    assert result.source == "fallback"


async def test_none_sampler_falls_back():
    result = await _scorer().score("be nice", None)
    assert result.source == "fallback"


async def test_sampling_off_ignores_sampler():
    async def sampler(_prompt: str) -> str:
        return "100"

    result = await _scorer(sampling="off").score("be nice", sampler)
    assert result.source == "fallback"


async def test_sampled_score_is_clamped():
    async def sampler(_prompt: str) -> str:
        return "250"

    result = await _scorer().score("when X do Y", sampler)
    assert result.score == 100
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_scorer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'boring_mcp.scoring.scorer'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/boring_mcp/scoring/scorer.py
"""Async structure scorer: client LLM sampling with deterministic fallback."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from boring_mcp.logging import get_logger
from boring_mcp.models.structure import StructureScore
from boring_mcp.scoring.rubric import score_rubric
from boring_mcp.scoring.tiers import Tiers

_log = get_logger("scorer")

Sampler = Callable[[str], Awaitable[str]]

_PROMPT = (
    "Score 0-100 how structured and specific this behavioral instruction is for "
    "deterministic execution. 0 = vague/lazy, 100 = precise, conditional, "
    "actionable. Reply with ONLY the integer.\n\nInstruction:\n"
)
_INT_RE = re.compile(r"-?\d+")


def _parse_score(reply: str) -> int | None:
    match = _INT_RE.search(reply)
    value: int | None = None
    if match is not None:
        value = max(0, min(100, int(match.group())))
    return value


@dataclass(frozen=True)
class StructureScorer:
    """Scores input structure, preferring the client LLM, falling back to rubric."""

    tiers: Tiers
    sampling: str

    async def _try_sample(self, text: str, sampler: Sampler | None) -> int | None:
        sampled: int | None = None
        if self.sampling == "auto" and sampler is not None:
            try:
                reply = await sampler(_PROMPT + text)
                sampled = _parse_score(reply)
            except Exception as exc:  # noqa: BLE001 - any sampling failure degrades gracefully
                _log.warning("Sampling failed, using rubric fallback: %s", exc)
                sampled = None
        return sampled

    async def score(self, text: str, sampler: Sampler | None) -> StructureScore:
        """Return a StructureScore for the given text."""
        sampled = await self._try_sample(text, sampler)
        score = sampled
        source = "sampled"
        if score is None:
            score = score_rubric(text)
            source = "fallback"
        result = StructureScore(
            score=score,
            tier=self.tiers.tier_for(score),
            reason=f"{source}={score}",
            source=source,
        )
        return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_scorer.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add src/boring_mcp/scoring/scorer.py tests/unit/test_scorer.py
git commit -m "feat: add StructureScorer with sampling and rubric fallback"
```

---

### Task 6: Scored backpressure in the guard

**Files:**
- Modify: `src/boring_mcp/backpressure.py`
- Test: `tests/unit/test_scored_backpressure.py`

**Interfaces:**
- Consumes: `StructureScorer` + `Sampler` (Task 5), `Tiers` (Task 3), `StructureScore` (Task 1).
- Produces: new async method on `BackpressureGuard`:
  `async scored_backpressure(self, text: str, scorer: StructureScorer, sampler: Sampler | None) -> str`
  which scores `text`, sleeps `tiers.duration_for(score)` seconds, marks backpressure satisfied, and returns the tier message. Existing `apply_backpressure`, `is_allowed`, `guarded` stay unchanged for admin tools.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_scored_backpressure.py
import boring_mcp.backpressure as bp
from boring_mcp.backpressure import BackpressureGuard
from boring_mcp.config import BackpressureConfig
from boring_mcp.scoring.scorer import StructureScorer
from boring_mcp.scoring.tiers import Tiers

import pytest

pytestmark = pytest.mark.asyncio


def _scorer() -> StructureScorer:
    return StructureScorer(tiers=Tiers.from_config(BackpressureConfig.from_env({})), sampling="auto")


@pytest.fixture
def captured_sleep(monkeypatch):
    calls: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        calls.append(seconds)

    monkeypatch.setattr(bp.asyncio, "sleep", fake_sleep)
    return calls


async def test_excellent_input_no_sleep_and_thanks(captured_sleep):
    guard = BackpressureGuard()

    async def sampler(_p: str) -> str:
        return "95"

    msg = await guard.scored_backpressure("when X do Y", _scorer(), sampler)
    assert captured_sleep == [0]
    assert "Thanks for being so structured" in msg


async def test_lazy_input_full_sleep(captured_sleep):
    guard = BackpressureGuard()

    async def sampler(_p: str) -> str:
        return "5"

    await guard.scored_backpressure("eh", _scorer(), sampler)
    assert captured_sleep == [30]


async def test_partial_input_partial_sleep(captured_sleep):
    guard = BackpressureGuard()

    async def sampler(_p: str) -> str:
        return "60"

    await guard.scored_backpressure("respond with code", _scorer(), sampler)
    assert captured_sleep == [10]


async def test_scored_backpressure_marks_allowed(captured_sleep):
    guard = BackpressureGuard()

    async def sampler(_p: str) -> str:
        return "95"

    await guard.scored_backpressure("when X do Y", _scorer(), sampler)
    assert guard.is_allowed() is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_scored_backpressure.py -v`
Expected: FAIL — `AttributeError: 'BackpressureGuard' object has no attribute 'scored_backpressure'`

- [ ] **Step 3: Write minimal implementation**

Add imports near the top of `src/boring_mcp/backpressure.py` (after the existing `from boring_mcp.logging import get_logger`):

```python
from boring_mcp.scoring.scorer import Sampler, StructureScorer
```

Add this method to the `BackpressureGuard` class (after `apply_backpressure`):

```python
    async def scored_backpressure(
        self, text: str, scorer: StructureScorer, sampler: Sampler | None
    ) -> str:
        """Score input, sleep by tier, mark backpressure satisfied, return message.

        Replaces the fixed 30s gate for text-bearing tools: the sleep duration is
        derived from how structured `text` is. Highly structured input sleeps 0s.
        """
        result = await scorer.score(text, sampler)
        seconds = scorer.tiers.duration_for(result.score)
        _log.info(
            "Scored backpressure: score=%d tier=%s source=%s sleep=%ds",
            result.score,
            result.tier,
            result.source,
            seconds,
        )
        self._boring_in_progress = True
        await asyncio.sleep(seconds)
        self._last_boring_at = time.monotonic()
        self._boring_in_progress = False
        return scorer.tiers.message_for(result.score)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_scored_backpressure.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Run mypy + single-return lint**

Run: `uv run mypy && python scripts/lint_single_return.py src/`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add src/boring_mcp/backpressure.py tests/unit/test_scored_backpressure.py
git commit -m "feat: add scored backpressure to guard"
```

---

### Task 7: Wire scorer into the server and score the text-bearing tools

**Files:**
- Modify: `src/boring_mcp/server.py`
- Test: `tests/e2e/test_structure_gating.py`

**Interfaces:**
- Consumes: `BackpressureConfig` (Task 2), `Tiers` (Task 3), `StructureScorer` (Task 5), `scored_backpressure` (Task 6), FastMCP `Context`.
- Produces: `store_behavior` and `query_behaviors` tools that accept `ctx: Context`, build a `sampler` from `ctx.sample`, call `guard.scored_backpressure(text, scorer, sampler)`, then run the handler. The returned string is `f"{message}\n{handler_result}"`. Admin tools unchanged.

- [ ] **Step 1: Write the failing test**

```python
# tests/e2e/test_structure_gating.py
import boring_mcp.backpressure as bp
import pytest
from fastmcp import Client

from boring_mcp.server import create_server

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def no_real_sleep(monkeypatch):
    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(bp.asyncio, "sleep", fake_sleep)


@pytest.fixture
def env_in_memory(monkeypatch):
    # empty chroma path => in-memory; force rubric so the test is deterministic
    monkeypatch.setenv("BORING_MCP_CHROMA_PATH", "")
    monkeypatch.setenv("BORING_MCP_SAMPLING", "off")


async def test_structured_store_returns_thanks(env_in_memory):
    server = create_server()
    async with Client(server) as client:
        result = await client.call_tool(
            "store_behavior",
            {
                "sentence": "When the user asks for code, respond with a fenced block, e.g. ```py```",
                "collection": "formatting",
            },
        )
        text = result.data if hasattr(result, "data") else str(result)
        assert "Thanks for being so structured" in str(text)


async def test_lazy_store_returns_boring(env_in_memory):
    server = create_server()
    async with Client(server) as client:
        result = await client.call_tool(
            "store_behavior",
            {"sentence": "be nice", "collection": "tone"},
        )
        text = result.data if hasattr(result, "data") else str(result)
        assert "30 seconds" in str(text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/e2e/test_structure_gating.py -v`
Expected: FAIL — store result has no tier message (current server returns only the handler JSON).

- [ ] **Step 3: Write minimal implementation**

In `src/boring_mcp/server.py`, update the imports block:

```python
from boring_mcp.backpressure import BackpressureGuard
from boring_mcp.config import BackpressureConfig
from boring_mcp.repositories.chroma import ChromaRepository
from boring_mcp.scoring.scorer import Sampler, StructureScorer
from boring_mcp.scoring.tiers import Tiers
from boring_mcp.services.behavior_service import BehaviorService
from boring_mcp.services.health_service import HealthService
```

Add a `Context` import from fastmcp at the top:

```python
from fastmcp import Context, FastMCP
```

Inside `create_server`, after `guard = BackpressureGuard()`, build the scorer:

```python
    config = BackpressureConfig.from_env(os.environ)
    scorer = StructureScorer(tiers=Tiers.from_config(config), sampling=config.sampling)

    def _make_sampler(ctx: Context) -> Sampler:
        async def sampler(prompt: str) -> str:
            response = await ctx.sample(prompt)
            return response.text

        return sampler
```

Replace the `store_behavior` tool (drop `@guard.guarded`, add `ctx`, score first):

```python
    @mcp.tool()
    async def store_behavior(
        sentence: str,
        collection: str,
        ctx: Context,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Store a behavioral sentence. Backpressure scales with input structure.

        Highly structured input applies directly; vague input triggers a boring pause.

        Args:
            sentence: The behavioral instruction to store.
            collection: Collection name (e.g., 'tone', 'persona').
            metadata: Optional key-value metadata.
        """
        from boring_mcp.tools.behaviors import store_behavior as _handler

        message = await guard.scored_backpressure(sentence, scorer, _make_sampler(ctx))
        handled = await _handler(sentence, collection, metadata, service=behavior_service)
        return f"{message}\n{handled}"
```

Replace the `query_behaviors` tool the same way:

```python
    @mcp.tool()
    async def query_behaviors(
        query: str,
        ctx: Context,
        collection: str | None = None,
        top_k: int = 5,
    ) -> str:
        """Retrieve relevant behaviors. Backpressure scales with query structure.

        Args:
            query: The context to match against.
            collection: Filter by collection (queries all if omitted).
            top_k: Number of results (default: 5).
        """
        from boring_mcp.tools.behaviors import query_behaviors as _handler

        message = await guard.scored_backpressure(query, scorer, _make_sampler(ctx))
        handled = await _handler(query, collection, top_k, service=behavior_service)
        return f"{message}\n{handled}"
```

Leave `delete_behavior`, `list_collections`, `health_check`, and the `boring` tool exactly as they are (they keep `@guard.guarded` and the manual full-boring gate).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/e2e/test_structure_gating.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Run full CI**

Run: `uv run ruff check . && uv run mypy && uv run pytest && python scripts/lint_single_return.py src/`
Expected: all green, coverage ≥ 98%. If existing e2e tests asserted that `store_behavior` requires a prior `boring()` call, update them — scored tools no longer require it (this is the intended contract change; admin-tool gating tests stay).

- [ ] **Step 6: Commit**

```bash
git add src/boring_mcp/server.py tests/e2e/test_structure_gating.py
git commit -m "feat: gate store/query backpressure on input structure"
```

---

### Task 8: Documentation

**Files:**
- Modify: `ai-docs/backpressure.md`
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: behaviour from Tasks 1–7.
- Produces: docs only. No code.

- [ ] **Step 1: Update `ai-docs/backpressure.md`**

Add a section "Structure-gated backpressure" describing: scoring via client sampling with rubric fallback, the three tiers (`<40`=30s, `40-79`=10s, `≥80`=0s), the new env vars, the `BORING_MCP_SAMPLING=off` determinism switch, and that `store_behavior`/`query_behaviors` no longer require a prior `boring()` call.

- [ ] **Step 2: Update `CLAUDE.md`**

In the env-vars table add the six new vars from the spec section 7. In the tools table, note that `store_behavior` / `query_behaviors` are now structure-gated (no mandatory `boring()` first). Keep admin tools' "Requires boring() first = Yes".

- [ ] **Step 3: Run single-return lint to be safe (no-op for docs) and full test suite**

Run: `uv run pytest`
Expected: PASS, coverage ≥ 98%.

- [ ] **Step 4: Commit**

```bash
git add ai-docs/backpressure.md CLAUDE.md
git commit -m "docs: document structure-gated backpressure"
```

---

## Self-Review

**Spec coverage:**
- Tiered scoring → Tasks 3, 6. ✓
- LLM sampling judge (client's own model) → Tasks 5, 7 (`ctx.sample`). ✓
- Deterministic fallback → Tasks 4, 5. ✓
- Scope to `store_behavior`/`query_behaviors` only → Task 7; admin tools untouched. ✓
- Env-configurable thresholds/durations + sampling switch → Tasks 2, 8. ✓
- "Thanks for being so structured" excellent message → Task 3 (`_EXCELLENT_MESSAGE`), asserted Task 7. ✓
- Predictability/determinism risk → `BORING_MCP_SAMPLING=off` + pure rubric, tested Tasks 4–5. ✓
- Engineering rules (single-exit, frozen, strict mypy, 98% cov) → Global Constraints + per-task lint/CI steps. ✓
- Contract change (scored tools skip `is_allowed`) → flagged Tasks 6, 7, 8. ✓

**Placeholder scan:** No TBD/TODO; every code step shows full code; commands have expected output. ✓

**Type consistency:** `StructureScore(score,tier,reason,source)`, `Tiers.from_config/tier_for/duration_for/message_for`, `BackpressureConfig.from_env`, `score_rubric(text)->int`, `StructureScorer(tiers,sampling).score(text,sampler)`, `Sampler=Callable[[str],Awaitable[str]]`, `guard.scored_backpressure(text,scorer,sampler)` — names/types identical across producing and consuming tasks. ✓

---

## Notes for the implementer

- `ctx.sample(prompt)` returns a content object exposing `.text`; the `_make_sampler` wrapper isolates that so the scorer stays FastMCP-agnostic and unit-testable with plain async callables.
- Verify the exact `ctx.sample` return shape against the installed FastMCP version (`uv run python -c "import fastmcp; print(fastmcp.__version__)"`); if `.text` differs, adjust only `_make_sampler` in `server.py` — no other file depends on it.
- Keep one `return` per function. Where you'd early-return, assign to a result var and return at the end.
