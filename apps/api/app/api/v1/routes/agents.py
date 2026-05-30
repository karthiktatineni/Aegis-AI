from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.core.security import CurrentUser, get_current_user
from app.schemas.agents import AgentRunRequest, AgentRunResponse
from app.services.agents.planner import AgentPlanner

router = APIRouter()


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    payload: AgentRunRequest,
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> AgentRunResponse:
    response = await AgentPlanner(session).run(user.id, payload)
    await session.commit()
    return response
