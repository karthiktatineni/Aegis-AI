from app.services.rag.chunking import chunk_text


def test_chunk_text_keeps_order_and_overlap() -> None:
    text = "alpha " * 300 + "\n\n" + "beta " * 300
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) > 1
    assert chunks[0].index == 0
    assert chunks[1].index == 1
    assert chunks[0].content
