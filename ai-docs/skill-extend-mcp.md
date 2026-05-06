# Boring MCP Extension Skill

## Purpose

This skill helps AI agents add new tools, resources, and collections to the
Boring MCP server while maintaining all architectural constraints.

## When to Use

Use this skill when the user asks to:
- Add a new MCP tool to Boring MCP
- Create a new behavior collection type
- Add a new resource endpoint
- Extend the repository with new query capabilities
- Add a new service layer capability

## Constraints (Non-Negotiable)

Every extension MUST follow these rules:

1. **Single-Exit-Point** — one `return` per function, at the end
2. **Backpressure** — new tools must be wrapped with `@guard.guarded`
3. **Strict typing** — full type annotations, no `Any`
4. **Layered architecture** — Tool → Service → Repository (no layer skipping)
5. **Frozen models** — new domain objects use `@dataclass(frozen=True, slots=True)`
6. **Validation** — inputs validated in `validation.py` before reaching services
7. **Tests** — unit + integration tests for every new feature

## Steps to Add a New Tool

### 1. Define the handler (in `src/boring_mcp/tools/`)

```python
"""my_tool — description of what it does."""

from __future__ import annotations

import json

from boring_mcp.services.behavior_service import BehaviorService


async def my_tool(param: str, *, service: BehaviorService) -> str:
    """One-line description."""
    result_data = service.some_method(param)
    return json.dumps({"result": result_data})
```

### 2. Register in `server.py`

```python
@mcp.tool()
@guard.guarded
async def my_tool(param: str) -> str:
    """Tool description for the agent."""
    from boring_mcp.tools.my_module import my_tool as _handler
    return await _handler(param, service=behavior_service)
```

### 3. Add validation (if needed)

Add validators in `src/boring_mcp/validation.py`:

```python
def validate_param(param: str) -> str:
    """Validate param meets requirements."""
    cleaned = param.strip()
    if not cleaned:
        msg = "param must not be empty"
        raise ValueError(msg)
    return cleaned
```

### 4. Write tests

- Unit test in `tests/unit/test_my_tool.py`
- E2E test in `tests/e2e/test_server.py` (add to existing file)

### 5. Validate

```bash
uv run ruff check . && uv run ruff format --check .
python scripts/lint_single_return.py src/
uv run mypy src/
uv run pytest tests/ --cov=boring_mcp --cov-fail-under=80
```

## Steps to Add a New Resource

### 1. Create handler in `src/boring_mcp/resources/`

```python
async def get_my_resource(*, service: BehaviorService) -> str:
    """Description."""
    data = service.some_method()
    return json.dumps(data)
```

### 2. Register in `server.py`

```python
@mcp.resource("myresource://path")
async def my_resource() -> str:
    """Resource description."""
    from boring_mcp.resources.my_module import get_my_resource
    return await get_my_resource(service=behavior_service)
```

Note: Resources are NOT gated by backpressure (they're read-only).

## Steps to Add a New Repository Method

### 1. Add to Protocol (`repositories/base.py`)

```python
def new_method(self, param: str) -> SomeType:
    """Description."""
    ...
```

### 2. Implement in `repositories/chroma.py`

### 3. Expose via service layer

Never call repository methods directly from tools.

## File Location Guide

| Type | Location |
|------|----------|
| Tool handler | `src/boring_mcp/tools/` |
| Resource handler | `src/boring_mcp/resources/` |
| Service logic | `src/boring_mcp/services/` |
| Repository | `src/boring_mcp/repositories/` |
| Domain model | `src/boring_mcp/models/` |
| Validation | `src/boring_mcp/validation.py` |
| Serialization | `src/boring_mcp/serializers.py` |
| Exceptions | `src/boring_mcp/exceptions.py` |
| Tests | `tests/{unit,integration,e2e}/` |
