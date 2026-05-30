from app.services.rag.embeddings import HashEmbeddingService


def test_hash_embeddings_are_deterministic() -> None:
    service = HashEmbeddingService()
    first = service.embed(["local private ai"])[0]
    second = service.embed(["local private ai"])[0]
    assert first == second
    assert len(first) == service.dimensions
