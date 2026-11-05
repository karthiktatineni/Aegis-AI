import pytest
from unittest.mock import AsyncMock

from app.schemas.agents import AgentRunRequest
from app.services.agents.planner import AgentPlanner
from app.services.tools.command import CommandSandboxTool
from app.services.tools.filesystem import FileSystemTool
from app.services.tools.web_search import WebSearchTool


@pytest.mark.asyncio
async def test_filesystem_tool(tmp_path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("Aegis AI Agent Data", encoding="utf-8")

    fs = FileSystemTool(root=tmp_path)
    res = await fs.run({"action": "list", "path": "."})
    assert res.ok is True
    assert "sample.txt" in res.output

    res_read = await fs.run({"action": "read", "path": "sample.txt"})
    assert res_read.ok is True
    assert "Aegis AI Agent Data" in res_read.output


@pytest.mark.asyncio
async def test_command_sandbox_safety():
    cmd_tool = CommandSandboxTool()

    # Blocked command (e.g. rm or curl not allowlisted)
    res_blocked = await cmd_tool.run({"command": ["curl", "https://example.com"]})
    assert res_blocked.ok is False
    assert "not allowlisted" in res_blocked.output

    # Allowlisted binary (python)
    res_allowed = await cmd_tool.run({"command": ["python", "--version"]})
    assert res_allowed.ok is True
    assert "Python" in res_allowed.output


@pytest.mark.asyncio
async def test_web_search_tool():
    search_tool = WebSearchTool()
    res = await search_tool.run({"query": "Mistral 7B Instruct"})
    assert res.ok is True
    assert "Mistral 7B" in res.output or "search" in res.output.lower()


@pytest.mark.asyncio
async def test_agent_planner_execution():
    mock_session = AsyncMock()
    planner = AgentPlanner(mock_session)
    request = AgentRunRequest(goal="Inspect workspace files", max_steps=4, allow_tools=["filesystem"])

    response = await planner.run("user_test", request)
    assert response.status == "completed"
    assert len(response.plan) == 4
    assert any(step.status == "completed" for step in response.plan)
    assert response.result is not None
