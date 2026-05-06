"""Shared test fixtures for Boring MCP."""

from collections.abc import Generator

import chromadb
import pytest

from boring_mcp.repositories.chroma import ChromaRepository
from boring_mcp.services.behavior_service import BehaviorService
from boring_mcp.services.health_service import HealthService


@pytest.fixture
def chroma_client() -> Generator[chromadb.ClientAPI, None, None]:
    """In-memory ChromaDB client for fast, isolated tests."""
    client = chromadb.EphemeralClient()
    yield client
    # Teardown: delete all collections to ensure isolation
    for col in client.list_collections():
        client.delete_collection(col.name)


@pytest.fixture
def repository(chroma_client: chromadb.ClientAPI) -> ChromaRepository:
    """ChromaRepository backed by in-memory ChromaDB."""
    return ChromaRepository(client=chroma_client)


@pytest.fixture
def behavior_service(repository: ChromaRepository) -> BehaviorService:
    """BehaviorService with in-memory repository."""
    return BehaviorService(repository=repository)


@pytest.fixture
def health_service(repository: ChromaRepository) -> HealthService:
    """HealthService with in-memory repository."""
    return HealthService(repository=repository)
