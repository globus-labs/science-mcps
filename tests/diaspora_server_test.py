import os
from time import time

import pytest
from fastmcp import Client

CLIENT_ID = os.getenv("DIASPORA_CLIENT_ID")
CLIENT_SECRET = os.getenv("DIASPORA_CLIENT_SECRET")

# Remote NERSC MCP endpoint (can override via environment variable)
REMOTE_URL = os.getenv(
    "DIASPORA_MCP_URL",
    "https://science-mcps-diaspora.qpp943wkvr7b2.us-east-1.cs.amazonlightsail.com/mcps/diaspora/",
)


@pytest.mark.asyncio
async def test_diaspora_confidential_auth():
    async with Client(REMOTE_URL) as client:
        raw = await client.call_tool(
            "diaspora_confidential_auth",
            {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
        )
        assert "Confidential client authentication successful" in raw[0].text

        raw = await client.call_tool("create_key")
        assert "access_key" in raw[0].text
        assert "secret_key" in raw[0].text
        assert "endpoint" in raw[0].text

        raw = await client.call_tool("list_topics")
        assert "diaspora-cicd" in raw[0].text

        raw = await client.call_tool("register_topic", {"topic": "mcps-cicd"})
        assert "success" in raw[0].text or "no-op" in raw[0].text

        curr_time = str(int(time()))
        raw = await client.call_tool(
            "produce_event", {"topic": "mcps-cicd", "value": curr_time}
        )
        assert "partition=0" in raw[0].text

        # raw = await client.call_tool("consume_latest_event", {"topic": "mcps-cicd"})
        # assert curr_time in raw[0].text
