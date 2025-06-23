import json
import os
from time import sleep, time

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

        raw = await client.call_tool("list_topics")
        assert "diaspora-cicd" in raw[0].text

        raw = await client.call_tool("register_topic", {"topic": "mcps-cicd"})
        assert "success" in raw[0].text or "no-op" in raw[0].text

        # test 1: sync produce without key
        curr_time = str(int(time()))
        raw = await client.call_tool(
            "produce_one", {"topic": "mcps-cicd", "value": curr_time}
        )
        result1 = json.loads(raw[0].text)
        assert result1["status"] == "produced"

        raw = await client.call_tool("consume_latest", {"topic": "mcps-cicd"})
        result2 = json.loads(raw[0].text)
        assert result2["key"] is None and result2["val"] == curr_time

        # test 2: sync produce with key
        curr_time = str(int(time()))
        msg_key = str(int(time()) + int(time()))
        raw = await client.call_tool(
            "produce_one", {"topic": "mcps-cicd", "value": curr_time, "key": msg_key}
        )
        result1 = json.loads(raw[0].text)
        assert result1["status"] == "produced"

        raw = await client.call_tool("consume_latest", {"topic": "mcps-cicd"})
        result2 = json.loads(raw[0].text)
        assert result2["key"] == msg_key and result2["val"] == curr_time

        # test 3: async produce
        curr_time = str(int(time()))
        msg_key = str(int(time()) + int(time()))
        raw = await client.call_tool(
            "produce_one",
            {"topic": "mcps-cicd", "value": curr_time, "key": msg_key, "sync": False},
        )
        result1 = json.loads(raw[0].text)
        assert result1["status"] == "queued"
