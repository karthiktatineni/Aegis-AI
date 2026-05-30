from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    content: str
    index: int
    metadata: dict


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 160) -> list[TextChunk]:
    cleaned = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if not cleaned:
        return []

    chunks: list[TextChunk] = []
    start = 0
    index = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        boundary = cleaned.rfind("\n\n", start, end)
        if boundary > start + chunk_size // 2:
            end = boundary
        content = cleaned[start:end].strip()
        if content:
            chunks.append(TextChunk(content=content, index=index, metadata={"start": start, "end": end}))
            index += 1
        if end >= len(cleaned):
            break
        start = max(end - overlap, 0)
    return chunks
