from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentRun
from app.schemas.agents import AgentRunRequest, AgentRunResponse, AgentStep
from app.services.ai.llm import get_llm_provider
from app.services.tools.registry import ToolRegistry


class AgentPlanner:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tools = ToolRegistry()
        self.llm = get_llm_provider()

    async def run(self, user_id: str, request: AgentRunRequest) -> AgentRunResponse:
        allowed = set(request.allow_tools or self.tools.tools.keys())
        tool_names = [name for name in self.tools.tools if name in allowed]
        plan = [
            AgentStep(step=1, thought="Clarify objective and constraints.", status="completed"),
            AgentStep(step=2, thought="Select relevant memory, knowledge, and tools.", status="completed"),
            AgentStep(
                step=3,
                thought="Execute the smallest useful action.",
                tool=tool_names[0] if tool_names else None,
                status="planned",
            ),
            AgentStep(step=4, thought="Reflect on result quality and gaps.", status="planned"),
        ][: request.max_steps]

        messages = [
            {
                "role": "system",
                "content": "You are an agent planner. Produce a concise execution result.",
            },
            {"role": "user", "content": request.goal},
        ]
        result = await self.llm.complete(messages)
        reflection = "Plan favors reversible, local-first actions and keeps tool use explicit."
        run = AgentRun(
            user_id=user_id,
            goal=request.goal,
            status="completed",
            plan=[step.model_dump() for step in plan],
            reflection=reflection,
            result=result,
        )
        self.session.add(run)
        await self.session.flush()
        return AgentRunResponse(
            id=run.id,
            goal=run.goal,
            status=run.status,
            plan=plan,
            reflection=reflection,
            result=result,
        )
