import os

import pytest
from fastmcp import Client

# Remote NERSC MCP endpoint (can override via environment variable)
REMOTE_URL = os.getenv(
    "NERSC_MCP_URL",
    "https://science-mcps-nersc.qpp943wkvr7b2.us-east-1.cs.amazonlightsail.com/mcps/nersc-status/",
)


@pytest.mark.asyncio
async def test_remote_nersc_status():
    async with Client(REMOTE_URL) as client:
        raw = await client.call_tool("get_nersc_status")
        assert "NERSC System Status Summary" in raw[0].text


@pytest.mark.asyncio
async def test_get_nersc_status_individual():
    async with Client(REMOTE_URL) as client:
        raw = await client.call_tool(
            "get_nersc_status_individual", {"system": "globus"}
        )
        assert "Globus" in raw[0].text


@pytest.mark.asyncio
async def test_check_system_availability():
    async with Client(REMOTE_URL) as client:
        raw = await client.call_tool("check_system_availability", {"system": "globus"})
        assert "Globus" in raw[0].text


@pytest.mark.asyncio
async def test_get_maintenance_info():
    async with Client(REMOTE_URL) as client:
        raw = await client.call_tool("get_maintenance_info", {"system": "globus"})
        assert "Globus" in raw[0].text
