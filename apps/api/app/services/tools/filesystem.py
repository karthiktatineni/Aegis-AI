from pathlib import Path

from app.core.config import get_settings
from app.services.tools.base import ToolResult


class FileSystemTool:
    name = "filesystem"
    description = "Read and search files inside the configured workspace root."
    input_schema = {
        "type": "object",
        "properties": {
            "action": {"enum": ["read", "list"]},
            "path": {"type": "string"},
        },
        "required": ["action", "path"],
    }

    def __init__(self) -> None:
        self.root = Path(get_settings().workspace_root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative_path: str) -> Path:
        path = (self.root / relative_path).resolve()
        if self.root not in path.parents and path != self.root:
            raise ValueError("Path escapes workspace root")
        return path

    async def run(self, payload: dict) -> ToolResult:
        path = self._resolve(payload.get("path", "."))
        action = payload.get("action")
        if action == "list":
            items = sorted(item.name for item in path.iterdir()) if path.exists() else []
            return ToolResult(ok=True, output="\n".join(items), metadata={"path": str(path)})
        if action == "read":
            return ToolResult(ok=True, output=path.read_text(encoding="utf-8"), metadata={"path": str(path)})
        return ToolResult(ok=False, output="Unsupported filesystem action", metadata={})
