from app.services.tools.base import ToolResult


class WebSearchTool:
    name = "web_search"
    description = "Provider-neutral web search abstraction. Disabled unless configured."
    input_schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
        "required": ["query"],
    }

    async def run(self, payload: dict) -> ToolResult:
        return ToolResult(
            ok=False,
            output="No web search provider configured. Add a provider implementation behind this tool.",
            metadata={"query": payload.get("query")},
        )
