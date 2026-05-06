"""Unit tests for HealthService."""

from boring_mcp.services.health_service import HealthService


class TestHealthService:
    """Tests for HealthService."""

    def test_healthy_status(self, health_service: HealthService) -> None:
        status = health_service.check()
        assert status.healthy is True
        assert status.chromadb_connected is True
        assert status.message == "All systems operational"

    def test_reports_collection_count(self, health_service: HealthService) -> None:
        # Add something so collection exists
        from boring_mcp.services.behavior_service import BehaviorService

        svc = BehaviorService(repository=health_service._repository)
        svc.store("test", "col1")
        svc.store("test", "col2")

        status = health_service.check()
        assert status.collections_count >= 2
