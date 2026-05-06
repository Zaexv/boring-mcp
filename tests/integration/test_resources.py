"""Integration tests for MCP resources."""

import json

import pytest

from boring_mcp.resources.behaviors import (
    get_behaviors_summary,
    get_collection_behaviors,
)
from boring_mcp.services.behavior_service import BehaviorService


class TestResources:
    """Integration tests for resource handlers."""

    @pytest.mark.asyncio
    async def test_get_collection_behaviors(
        self, behavior_service: BehaviorService
    ) -> None:
        behavior_service.store("Be kind", "tone")
        behavior_service.store("Be warm", "tone")

        result = await get_collection_behaviors("tone", service=behavior_service)
        data = json.loads(result)
        assert data["collection"] == "tone"
        assert data["count"] == 2
        assert len(data["behaviors"]) == 2

    @pytest.mark.asyncio
    async def test_get_empty_collection(
        self, behavior_service: BehaviorService
    ) -> None:
        result = await get_collection_behaviors("empty", service=behavior_service)
        data = json.loads(result)
        assert data["count"] == 0

    @pytest.mark.asyncio
    async def test_behaviors_summary(self, behavior_service: BehaviorService) -> None:
        behavior_service.store("x", "tone")
        behavior_service.store("y", "boundaries")
        behavior_service.store("z", "boundaries")

        result = await get_behaviors_summary(service=behavior_service)
        data = json.loads(result)
        assert data["total_collections"] == 2
        collections_map = {c["collection"]: c["count"] for c in data["collections"]}
        assert collections_map["tone"] == 1
        assert collections_map["boundaries"] == 2
