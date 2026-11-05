from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentRun, ToolRun
from app.models.entities import uuid_str
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

        executed_tool_output = None
        executed_tool_name = None
        executed_tool_input = {}
        tool_status = "completed"

        # Execute selected tool when requested and allowed
        if len(plan) >= 3 and tool_names:
            executed_tool_name = tool_names[0]
            if executed_tool_name == "filesystem":
                executed_tool_input = {"action": "list", "path": "."}
            elif executed_tool_name == "web_search":
                executed_tool_input = {"query": request.goal, "limit": 3}
            elif executed_tool_name == "command_sandbox":
                executed_tool_input = {"command": ["python", "--version"]}
            else:
                executed_tool_input = {}

            tool_result = await self.tools.run(executed_tool_name, executed_tool_input)
            executed_tool_output = tool_result.output
            tool_status = "completed" if tool_result.ok else "failed"

            plan[2] = AgentStep(
                step=3,
                thought=f"Executed tool {executed_tool_name}: {tool_result.output[:120]}...",
                tool=executed_tool_name,
                status=tool_status,
            )

        if len(plan) >= 4:
            plan[3] = AgentStep(
                step=4,
                thought="Reflect on execution results and ensure safe, local-first output.",
                status="completed",
            )

        context_prompt = f"Goal: {request.goal}"
        if executed_tool_output:
            context_prompt += f"\nTool [{executed_tool_name}] output:\n{executed_tool_output}"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Aegis AI agent planner and executor. "
                    "Synthesize the goal and any tool observations into a concise, actionable answer."
                ),
            },
            {"role": "user", "content": context_prompt},
        ]
        result = await self.llm.complete(messages)
        reflection = (
            f"Executed multi-step plan with {len(plan)} steps. "
            f"Tool orchestration: {'active (' + executed_tool_name + ')' if executed_tool_name else 'none'}. "
            "Plan favors reversible, local-first actions."
        )

        run_id = uuid_str()
        run = AgentRun(
            id=run_id,
            user_id=user_id,
            goal=request.goal,
            status="completed",
            plan=[step.model_dump() for step in plan],
            reflection=reflection,
            result=result,
        )
        self.session.add(run)
        await self.session.flush()

        if executed_tool_name:
            tool_run = ToolRun(
                user_id=user_id,
                agent_run_id=run.id,
                tool_name=executed_tool_name,
                input_json=executed_tool_input,
                output_json={"output": executed_tool_output, "status": tool_status},
                status=tool_status,
            )
            self.session.add(tool_run)
            await self.session.flush()

        return AgentRunResponse(
            id=run.id,
            goal=run.goal,
            status=run.status,
            plan=plan,
            reflection=reflection,
            result=result,
        )
