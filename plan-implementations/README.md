# Plan Implementations

Executable, bite-sized TDD implementation plans (output of the
`superpowers:writing-plans` flow). Design specs live in `../plans/`.

## Naming convention (standard)

```
<YYYY-MM-DD>-<feature-name>-impl.md        # in progress / not started
DONE_<YYYY-MM-DD>-<feature-name>-impl.md   # fully implemented + CI green
```

**Rule:** when a plan is fully implemented and the full CI gate passes
(`ruff check . && mypy && pytest && lint_single_return`), rename it with a
`DONE_` prefix. The prefix is the single source of truth for completion status —
a plan without `DONE_` is unfinished.

## Status

| Plan | Status |
|------|--------|
| `DONE_2026-06-29-structure-gated-backpressure-impl.md` | ✅ Implemented, 116 tests pass, 99% coverage |
