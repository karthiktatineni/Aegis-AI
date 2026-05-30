from app.services.tools.base import Tool, ToolResult
from app.services.tools.command import CommandSandboxTool
from app.services.tools.filesystem import FileSystemTool
from app.services.tools.iot import IoTTool
from app.services.tools.web_search import WebSearchTool


class ToolRegistry:
    def __init__(self) -> None:
        tools: list[Tool] = [
            FileSystemTool(),
            CommandSandboxTool(),
            WebSearchTool(),
            IoTTool(),
        ]
        self.tools = {tool.name: tool for tool in tools}

    def list_tools(self) -> list[Tool]:
        return list(self.tools.values())

    async def run(self, name: str, payload: dict) -> ToolResult:
        tool = self.tools.get(name)
        if not tool:
            return ToolResult(ok=False, output=f"Unknown tool: {name}", metadata={})
        return await tool.run(payload)
