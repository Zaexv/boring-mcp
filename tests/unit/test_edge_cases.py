"""Tests for edge cases and branch coverage."""

import unittest.mock

from boring_mcp.repositories.chroma import ChromaRepository
from boring_mcp.services.health_service import HealthService


class TestChromaRepositoryPersistentClient:
    """Test the PersistentClient branch of ChromaRepository."""

    def test_persistent_client_path(self, tmp_path) -> None:
        path = str(tmp_path / "chromadb")
        repo = ChromaRepository(persist_path=path)
        assert repo._client is not None

    def test_default_ephemeral_client(self) -> None:
        repo = ChromaRepository()
        assert repo._client is not None


class TestHealthServiceErrorBranch:
    """Test health_service when ChromaDB is unavailable."""

    def test_health_check_returns_unhealthy_on_error(self) -> None:
        mock_repo = unittest.mock.MagicMock()
        mock_repo.list_collections.side_effect = RuntimeError("ChromaDB down")
        health_service = HealthService(repository=mock_repo)
        status = health_service.check()
        assert status.healthy is False
        assert status.chromadb_connected is False
        assert "ChromaDB down" in status.message
