import pytest
from app.schemas.chat import Citation
from app.services.ai.reranker import rerank
from app.services.rag.chunking import chunk_text
from app.services.rag.embeddings import HashEmbeddingService
from app.services.rag.vector_store import ChromaVectorStore, VectorRecord


def test_chunking_and_overlap():
    sample_text = (
        "Aegis AI is a local-first platform.\n\n"
        "It supports Mistral 7B and Qwen 2.5 7B models.\n\n"
        "Retrieval-Augmented Generation (RAG) is backed by ChromaDB.\n\n"
        "Long-term memory persists across chat sessions."
    )
    chunks = chunk_text(sample_text, chunk_size=80, overlap=20)
    assert len(chunks) >= 2
    assert all(chunk.content for chunk in chunks)
    assert chunks[0].index == 0


def test_embeddings_and_vector_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CHROMA_PATH", str(tmp_path / "chroma"))
    embed_service = HashEmbeddingService()
    store = ChromaVectorStore()

    records = [
        VectorRecord(
            id="doc1:0",
            content="Aegis AI supports Mistral 7B local LLM inference.",
            embedding=embed_service.embed(["Aegis AI supports Mistral 7B local LLM inference."])[0],
            metadata={"document_id": "doc1", "filename": "doc1.txt", "tags": "llm,mistral"},
        ),
        VectorRecord(
            id="doc2:0",
            content="Qwen 2.5 7B provides high-accuracy reasoning on local hardware.",
            embedding=embed_service.embed(["Qwen 2.5 7B provides high-accuracy reasoning on local hardware."])[0],
            metadata={"document_id": "doc2", "filename": "doc2.txt", "tags": "llm,qwen"},
        ),
    ]

    store.upsert("test_coll", records)

    query = "Mistral 7B local"
    query_vec = embed_service.embed([query])[0]
    results = store.query(["test_coll"], query_vec, limit=2)

    assert len(results) > 0
    assert results[0].filename in ["doc1.txt", "doc2.txt"]
    assert results[0].score >= 0.0

    # Test reranker
    reranked = rerank(query, results, limit=1)
    assert len(reranked) == 1
    assert "Mistral" in reranked[0].excerpt
