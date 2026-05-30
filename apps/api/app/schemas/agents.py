from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    goal: str = Field(min_length=1)
    collection_ids: list[str] = []
    max_steps: int = Field(default=5, ge=1, le=12)
    allow_tools: list[str] = []


class AgentStep(BaseModel):
    step: int
    thought: str
    tool: str | None = None
    status: str
    observation: str | None = None


class AgentRunResponse(BaseModel):
    id: str
    goal: str
    status: str
    plan: list[AgentStep]
    reflection: str | None
    result: str


class ToolInfo(BaseModel):
    name: str
    description: str
    input_schema: dict
