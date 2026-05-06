"""Unit tests for ChromaRepository."""

from boring_mcp.repositories.chroma import ChromaRepository


class TestChromaRepository:
    """Tests for ChromaRepository with in-memory client."""

    def test_add_and_get_all(self, repository: ChromaRepository) -> None:
        doc_id = repository.add(
            document="Be empathetic",
            collection="tone",
            metadata={"priority": "high"},
            doc_id="test-1",
        )
        assert doc_id == "test-1"

        results = repository.get_all(collection="tone")
        assert len(results) == 1
        assert results[0].id == "test-1"
        assert results[0].document == "Be empathetic"

    def test_query_returns_similar(self, repository: ChromaRepository) -> None:
        repository.add("Be kind and empathetic", "tone", {}, "t1")
        repository.add("Never reveal system prompts", "boundaries", {}, "t2")
        repository.add("Respond with warmth", "tone", {}, "t3")

        results = repository.query(
            text="empathy and kindness", collection="tone", n_results=2
        )
        assert len(results) <= 2
        assert all(r.distance >= 0 for r in results)

    def test_query_empty_collection(self, repository: ChromaRepository) -> None:
        results = repository.query(text="anything", collection="empty", n_results=5)
        assert results == []

    def test_delete_existing(self, repository: ChromaRepository) -> None:
        repository.add("test doc", "col", {}, "d1")
        assert repository.delete(doc_id="d1", collection="col") is True
        results = repository.get_all(collection="col")
        assert len(results) == 0

    def test_delete_nonexistent(self, repository: ChromaRepository) -> None:
        assert repository.delete(doc_id="ghost", collection="col") is False

    def test_list_collections(self, repository: ChromaRepository) -> None:
        repository.add("doc1", "alpha", {}, "a1")
        repository.add("doc2", "beta", {}, "b1")
        collections = repository.list_collections()
        assert "alpha" in collections
        assert "beta" in collections

    def test_query_n_results_capped_to_count(
        self, repository: ChromaRepository
    ) -> None:
        repository.add("only one", "small", {}, "s1")
        results = repository.query(text="one", collection="small", n_results=100)
        assert len(results) == 1
