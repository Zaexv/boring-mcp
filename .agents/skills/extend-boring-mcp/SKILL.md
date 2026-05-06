---
name: extend-boring-mcp
description: Extend Boring MCP with new tools, resources, and capabilities. Use when adding new MCP tools, behavior collections, resource endpoints, repository methods, or service layer features to the Boring MCP server. Ensures all extensions follow SOLID principles, backpressure enforcement, strict typing, and single-exit-point rules.
---

# Extend Boring MCP

Skill for adding new tools, resources, and capabilities to Boring MCP while
maintaining all architectural constraints and code quality standards.

## Architecture Overview

Boring MCP follows a strict layered architecture:

```
Transport (FastMCP) → Backpressure (guard) → Tools/Resources → Validation → Services → Repository → ChromaDB
```

**No layer skipping is allowed.** Tools must go through services; services through repositories.

## Non-Negotiable Constraints

Every extension MUST follow these rules:

1. **Single-Exit-Point** — one `return` per function, placed at the end of the body
2. **Backpressure** — new tools MUST be wrapped with `@guard.guarded` in `server.py`
3. **Strict typing** — full type annotations, passes `mypy --strict`, no `Any`
4. **Layered architecture** — Tool → Validation → Service → Repository (no skipping)
5. **Frozen models** — new domain objects use `@dataclass(frozen=True, slots=True)`
6. **Validation** — all inputs validated in `validation.py` before reaching services
7. **Tests at every level** — unit + integration + e2e tests for every new feature
8. **Domain exceptions** — use exceptions from `exceptions.py`, never bare `Exception`

## Adding a New Tool — Step by Step

### Step 1: Add validation (if needed) in `src/boring_mcp/validation.py`

```python
def validate_my_param(value: str) -> str:
    """Validate that my_param meets requirements."""
    cleaned = value.strip()
    if not cleaned:
        msg = "my_param must not be empty"
        raise ValueError(msg)
    return cleaned
```

Rules:
- Single return at end
- Raise `ValueError` with a descriptive `msg` variable
- Return the cleaned/validated value

### Step 2: Add service method (if needed) in `src/boring_mcp/services/`

```python
def my_method(self, param: str) -> SomeResult:
    """Describe what this does."""
    result = self._repository.some_method(param)
    return result
```

Rules:
- Services depend on `BehaviorRepository` Protocol, never `ChromaRepository` directly
- No direct ChromaDB calls — always go through the repository
- Single return at end

### Step 3: Create tool handler in `src/boring_mcp/tools/my_tool.py`

```python
"""My tool — description of what it does."""

from __future__ import annotations

import json

from boring_mcp.services.behavior_service import BehaviorService
from boring_mcp.validation import validate_my_param


async def my_tool(param: str, *, service: BehaviorService) -> str:
    """One-line description matching the tool docstring."""
    clean_param = validate_my_param(param)
    data = service.my_method(clean_param)
    return json.dumps({"result": data})
```

Rules:
- `service` is always a keyword-only argument
- Validate inputs first, then call service
- Return JSON string (all MCP tools return strings)
- Single return at end
- Use `from __future__ import annotations` for forward references

### Step 4: Register in `src/boring_mcp/server.py`

```python
# --- Tool: my_tool ---
@mcp.tool()
@guard.guarded
async def my_tool(param: str) -> str:
    """Tool description visible to the AI agent.

    Args:
        param: Description of param.
    """
    from boring_mcp.tools.my_module import my_tool as _handler

    return await _handler(param, service=behavior_service)
```

Rules:
- Always apply `@guard.guarded` decorator (after `@mcp.tool()`)
- Lazy import the handler inside the function (avoids circular imports)
- Alias the import as `_handler` to avoid name collision
- Docstring includes `Args:` section for all parameters

### Step 5: Write unit tests in `tests/unit/test_my_tool.py`

```python
"""Unit tests for my_tool."""

import unittest.mock

import pytest


class TestMyTool:
    """Tests for my_tool handler."""

    @pytest.mark.asyncio
    async def test_valid_input(self) -> None:
        mock_service = unittest.mock.MagicMock()
        mock_service.my_method.return_value = "result"
        from boring_mcp.tools.my_module import my_tool
        result = await my_tool("valid", service=mock_service)
        assert '"result"' in result

    @pytest.mark.asyncio
    async def test_invalid_input_raises(self) -> None:
        mock_service = unittest.mock.MagicMock()
        from boring_mcp.tools.my_module import my_tool
        with pytest.raises(ValueError, match="must not be empty"):
            await my_tool("", service=mock_service)
```

### Step 6: Write e2e test in `tests/e2e/test_server.py`

Add a new test class that exercises the full pipeline through `server.call_tool`:

```python
class TestMyToolE2E:
    """Test my_tool through the server."""

    @pytest.mark.asyncio
    async def test_my_tool_full_pipeline(self, server) -> None:
        with unittest.mock.patch(
            "boring_mcp.backpressure.asyncio.sleep", return_value=None
        ):
            await server.call_tool("boring", {})
            result = await server.call_tool("my_tool", {"param": "value"})
        data = json.loads(_text(result))
        assert data["result"] == "expected"
```

### Step 7: Validate everything passes

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
python scripts/lint_single_return.py src/
uv run mypy src/
uv run pytest tests/ --cov=boring_mcp --cov-report=term-missing
```

All of these must pass with zero errors before committing.

## Adding a New Resource

Resources are read-only and are NOT gated by backpressure.

### Step 1: Create handler in `src/boring_mcp/resources/`

```python
async def get_my_resource(param: str, *, service: BehaviorService) -> str:
    """Description of what data this resource exposes."""
    data = service.some_method(param)
    return json.dumps(data)
```

### Step 2: Register in `server.py`

```python
@mcp.resource("myresource://{param}")
async def my_resource(param: str) -> str:
    """Resource description visible to the agent."""
    from boring_mcp.resources.my_module import get_my_resource

    return await get_my_resource(param, service=behavior_service)
```

Note: No `@guard.guarded` on resources — they're read-only.

## Adding a New Repository Method

### Step 1: Define in Protocol (`src/boring_mcp/repositories/base.py`)

```python
def new_method(self, param: str) -> ReturnType:
    """Description."""
    ...
```

### Step 2: Implement in `src/boring_mcp/repositories/chroma.py`

### Step 3: Expose through the service layer (never call repo from tools directly)

## Adding a New Domain Model

```python
@dataclass(frozen=True, slots=True)
class MyModel:
    """Description of this domain object."""

    field_one: str
    field_two: int
    optional_field: str | None = None
```

Rules:
- Always `frozen=True, slots=True`
- Use `field(default_factory=dict)` for mutable defaults
- Place in `src/boring_mcp/models/`
- Export from `src/boring_mcp/models/__init__.py`

## File Location Quick Reference

| Type | Location |
|------|----------|
| Tool handler | `src/boring_mcp/tools/` |
| Resource handler | `src/boring_mcp/resources/` |
| Service logic | `src/boring_mcp/services/` |
| Repository protocol | `src/boring_mcp/repositories/base.py` |
| Repository impl | `src/boring_mcp/repositories/chroma.py` |
| Domain model | `src/boring_mcp/models/` |
| Validation | `src/boring_mcp/validation.py` |
| Serialization | `src/boring_mcp/serializers.py` |
| Exceptions | `src/boring_mcp/exceptions.py` |
| Server wiring | `src/boring_mcp/server.py` |
| Unit tests | `tests/unit/` |
| Integration tests | `tests/integration/` |
| E2E tests | `tests/e2e/` |
| CI config | `.github/workflows/ci.yml` |

## Common Patterns

### JSON Response Pattern

All tools return JSON strings:

```python
return json.dumps({"key": value, "count": len(items)})
```

### Validation + Service Pattern

```python
async def my_tool(param: str, *, service: BehaviorService) -> str:
    clean = validate_param(param)
    result = service.do_thing(clean)
    return json.dumps({"result": result})
```

### Error Handling in Tools

Don't catch exceptions in tool handlers — let them propagate to FastMCP which
returns error responses to the client. For expected failures, return error JSON:

```python
async def delete_behavior(behavior_id: str, *, service: BehaviorService) -> str:
    deleted = service.delete(doc_id=behavior_id)
    result = json.dumps({"id": behavior_id, "deleted": deleted})
    return result
```

## Commit Message Convention

```
feat: add <tool-name> tool for <purpose>

- Add tool handler in src/boring_mcp/tools/
- Register with @guard.guarded in server.py
- Add validation in validation.py
- Add unit + e2e tests
- 100% coverage maintained

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```
