"""Integration tests for MCP tools with real ChromaDB."""

import json

import pytest

from boring_mcp.services.behavior_service import BehaviorService
from boring_mcp.services.health_service import HealthService
from boring_mcp.tools.behaviors import delete_behavior, query_behaviors, store_behavior
from boring_mcp.tools.collections import list_collections
from boring_mcp.tools.health import health_check


class TestStoreAndQuery:
    """Integration tests for store + query flow."""

    @pytest.mark.asyncio
    async def test_store_then_query(self, behavior_service: BehaviorService) -> None:
        result = await store_behavior(
            "Be empathetic always", "tone", None, service=behavior_service
        )
        data = json.loads(result)
        assert data["status"] == "stored"
        assert "id" in data

        query_result = await query_behaviors(
            "empathy", "tone", 5, service=behavior_service
        )
        query_data = json.loads(query_result)
        assert query_data["count"] >= 1
        assert any("empathetic" in b["sentence"] for b in query_data["results"])

    @pytest.mark.asyncio
    async def test_store_then_delete(self, behavior_service: BehaviorService) -> None:
        result = await store_behavior(
            "Temporary behavior", "temp", None, service=behavior_service
        )
        doc_id = json.loads(result)["id"]

        delete_result = await delete_behavior(doc_id, service=behavior_service)
        delete_data = json.loads(delete_result)
        assert delete_data["deleted"] is True

    @pytest.mark.asyncio
    async def test_list_collections(self, behavior_service: BehaviorService) -> None:
        await store_behavior("x", "alpha", None, service=behavior_service)
        await store_behavior("y", "beta", None, service=behavior_service)

        result = await list_collections(service=behavior_service)
        data = json.loads(result)
        assert "alpha" in data["collections"]
        assert "beta" in data["collections"]

    @pytest.mark.asyncio
    async def test_health_check(self, health_service: HealthService) -> None:
        result = await health_check(service=health_service)
        data = json.loads(result)
        assert data["healthy"] is True
        assert data["chromadb_connected"] is True
