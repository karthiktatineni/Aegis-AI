import asyncio
from pathlib import Path

from app.core.config import get_settings
from app.services.tools.base import ToolResult


class CommandSandboxTool:
    name = "command_sandbox"
    description = "Execute allowlisted local commands inside the workspace root."
    input_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["command"],
    }

    allowed_binaries = {"python", "node", "npm", "pytest", "ruff"}

    async def run(self, payload: dict) -> ToolResult:
        settings = get_settings()
        if not settings.command_sandbox_enabled:
            return ToolResult(ok=False, output="Command sandbox disabled", metadata={})

        command = payload.get("command") or []
        if not isinstance(command, list) or not command:
            return ToolResult(ok=False, output="Command must be a non-empty string array", metadata={})
        if Path(command[0]).name not in self.allowed_binaries:
            return ToolResult(ok=False, output=f"Command not allowlisted: {command[0]}", metadata={})

        workspace = Path(settings.workspace_root).resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=workspace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=settings.command_timeout_seconds
            )
        except TimeoutError:
            process.kill()
            return ToolResult(ok=False, output="Command timed out", metadata={})
        output = (stdout + stderr).decode("utf-8", errors="replace")
        return ToolResult(
            ok=process.returncode == 0,
            output=output[-8000:],
            metadata={"returncode": process.returncode},
        )
