from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ET
import httpx

from app.core.config import get_settings
from app.services.tools.base import ToolResult


async def fetch_realtime_news(query: str, limit: int = 4) -> list[str]:
    """Fetch live, up-to-the-minute news articles from Google News RSS."""
    cleaned = query.strip()
    if not cleaned:
        return []
    encoded = urllib.parse.quote(cleaned)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(url, headers={"User-Agent": "AegisAI/1.0"})
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                items = root.findall(".//item")[:limit]
                results = []
                for item in items:
                    title = (item.findtext("title") or "").strip()
                    pub_date = (item.findtext("pubDate") or "").strip()
                    link = (item.findtext("link") or "").strip()
                    if title:
                        results.append(f"{title} ({pub_date}) - {link}")
                return results
    except Exception as exc:
        print(f"[WebSearch] Error fetching real-time news: {exc}")
    return []


class WebSearchTool:
    name = "web_search"
    description = "Fetches real-time web search and live news updates."
    input_schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
        "required": ["query"],
    }

    async def run(self, payload: dict) -> ToolResult:
        query = payload.get("query", "").strip()
        if not query:
            return ToolResult(ok=False, output="Search query cannot be empty", metadata={})

        limit = min(int(payload.get("limit", 4)), 6)
        news_items = await fetch_realtime_news(query, limit=limit)
        if news_items:
            output = "Live News Updates:\n" + "\n".join(f"- {item}" for item in news_items)
            return ToolResult(ok=True, output=output, metadata={"query": query, "count": len(news_items), "source": "google_news_rss"})

        # Clean fallback summary
        return ToolResult(
            ok=True,
            output=f"Searched web for: '{query}'. No breaking headlines found.",
            metadata={"query": query, "limit": limit},
        )
