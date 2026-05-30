import re

from app.schemas.chat import Citation


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(text)}


def rerank(query: str, citations: list[Citation], limit: int = 8) -> list[Citation]:
    query_tokens = _tokens(query)
    if not query_tokens:
        return citations[:limit]
    scored: list[Citation] = []
    for citation in citations:
        overlap = len(query_tokens.intersection(_tokens(citation.excerpt)))
        citation.score = round(citation.score + overlap / max(len(query_tokens), 1), 4)
        scored.append(citation)
    return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]
