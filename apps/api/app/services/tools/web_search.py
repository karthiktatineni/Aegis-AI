import httpx

from app.core.config import get_settings
from app.services.tools.base import ToolResult


class WebSearchTool:
    name = "web_search"
    description = "Provider-neutral web search abstraction with privacy-preserving DuckDuckGo / local fallback."
    input_schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
        "required": ["query"],
    }

    async def run(self, payload: dict) -> ToolResult:
        query = payload.get("query", "").strip()
        if not query:
            return ToolResult(ok=False, output="Search query cannot be empty", metadata={})

        settings = get_settings()
        limit = min(int(payload.get("limit", 3)), 5)

        # Attempt DuckDuckGo instant answer / abstract query if enabled
        if settings.web_search_provider.lower() != "disabled":
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(
                        "https://api.duckduckgo.com/",
                        params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        abstract = data.get("AbstractText", "")
                        heading = data.get("Heading", "")
                        source_url = data.get("AbstractURL", "")
                        if abstract:
                            return ToolResult(
                                ok=True,
                                output=f"[{heading}] {abstract} (Source: {source_url})",
                                metadata={"source": "duckduckgo", "url": source_url},
                            )
            except Exception:
                pass  # Fall back cleanly

        # Clean fallback summary for offline or local dev
        return ToolResult(
            ok=True,
            output=f"Simulated local web search for: '{query}'. In production, set WEB_SEARCH_PROVIDER=duckduckgo.",
            metadata={"query": query, "limit": limit, "mode": "local_mock"},
        )
