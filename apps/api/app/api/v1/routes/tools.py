from fastapi import APIRouter

from app.schemas.agents import ToolInfo
from app.services.tools.registry import ToolRegistry

router = APIRouter()


@router.get("", response_model=list[ToolInfo])
async def list_tools() -> list[ToolInfo]:
    return [
        ToolInfo(name=tool.name, description=tool.description, input_schema=tool.input_schema)
        for tool in ToolRegistry().list_tools()
    ]
