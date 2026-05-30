from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    output: str
    metadata: dict


class Tool(Protocol):
    name: str
    description: str
    input_schema: dict

    async def run(self, payload: dict) -> ToolResult:
        ...
