import os

import pytest
from fastmcp import Client

# Remote NERSC MCP endpoint (can override via environment variable)
REMOTE_URL = os.getenv(
    "ALCF_MCP_URL",
    "https://science-mcps-alcf.qpp943wkvr7b2.us-east-1.cs.amazonlightsail.com/mcps/alcf-status/",
)


@pytest.mark.asyncio
async def test_check_alcf_status():
    async with Client(REMOTE_URL) as client:
        raw = await client.call_tool("check_alcf_status")
        assert "Job State Summary" in raw.content[0].text


@pytest.mark.asyncio
async def test_get_running_jobs():
    async with Client(REMOTE_URL) as client:
        raw = await client.call_tool("get_running_jobs")
        assert "Running Jobs on ALCF Polaris" in raw.content[0].text


@pytest.mark.asyncio
async def test_system_health_summary():
    async with Client(REMOTE_URL) as client:
        raw = await client.call_tool("system_health_summary")
        assert "System Health Summary" in raw.content[0].text
