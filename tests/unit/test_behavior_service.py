"""Unit tests for BehaviorService."""

from boring_mcp.services.behavior_service import BehaviorService


class TestBehaviorService:
    """Tests for BehaviorService business logic."""

    def test_store_returns_uuid(self, behavior_service: BehaviorService) -> None:
        doc_id = behavior_service.store("Be helpful", "tone")
        assert doc_id
        assert len(doc_id) == 36  # UUID format

    def test_store_and_query(self, behavior_service: BehaviorService) -> None:
        behavior_service.store("Always be empathetic", "tone")
        behavior_service.store("Use bullet points", "formatting")

        results = behavior_service.query("empathy", collection="tone", top_k=5)
        assert len(results) >= 1
        assert results[0].collection == "tone"
        assert "empathetic" in results[0].sentence

    def test_query_across_collections(self, behavior_service: BehaviorService) -> None:
        behavior_service.store("Be warm", "tone")
        behavior_service.store("Be cold", "boundaries")

        results = behavior_service.query("temperature", collection=None, top_k=10)
        assert len(results) >= 1

    def test_delete_existing(self, behavior_service: BehaviorService) -> None:
        doc_id = behavior_service.store("Temporary", "temp")
        assert behavior_service.delete(doc_id) is True
        results = behavior_service.get_collection("temp")
        assert len(results) == 0

    def test_delete_nonexistent(self, behavior_service: BehaviorService) -> None:
        assert behavior_service.delete("nonexistent-uuid") is False

    def test_list_collections(self, behavior_service: BehaviorService) -> None:
        behavior_service.store("x", "alpha")
        behavior_service.store("y", "beta")
        collections = behavior_service.list_collections()
        assert "alpha" in collections
        assert "beta" in collections

    def test_get_collection(self, behavior_service: BehaviorService) -> None:
        behavior_service.store("First", "persona")
        behavior_service.store("Second", "persona")
        behaviors = behavior_service.get_collection("persona")
        assert len(behaviors) == 2
        assert all(b.collection == "persona" for b in behaviors)

    def test_store_with_metadata(self, behavior_service: BehaviorService) -> None:
        behavior_service.store(
            "Be professional",
            "tone",
            metadata={"context": "work"},
        )
        behaviors = behavior_service.get_collection("tone")
        assert len(behaviors) == 1
