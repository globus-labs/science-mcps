#!/usr/bin/env python3
"""
NERSC Status MCP Server

This MCP server provides tools to check the status of NERSC (National Energy Research Scientific Computing Center) systems.
It retrieves information from NERSC's public API about system availability, maintenance, and other status updates.
"""

import json
import logging
from typing import Any, Optional
from urllib.parse import urljoin

import aiohttp
from fastmcp import Context, FastMCP

logger = logging.getLogger(__name__)
mcp = FastMCP("NERSC Status Bridge")
_session: Optional[aiohttp.ClientSession] = None


NERSC_API_BASE = "https://api.nersc.gov/api/v1.2/"
NERSC_STATUS_ENDPOINT = "status/"


async def _get_http_session() -> aiohttp.ClientSession:
    """Get or create HTTP session."""
    global _session
    if _session is None:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; Globus-Labs-Science-MCP-Agent/1.0;"
                " +https://github.com/globus-labs/science-mcps)"
            )
        }
        _session = aiohttp.ClientSession(headers=headers)
    return _session


async def _get_system_status() -> list[dict[str, Any]]:
    """Retrieve system status from NERSC API."""
    session = await _get_http_session()
    url = urljoin(NERSC_API_BASE, NERSC_STATUS_ENDPOINT)
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(
                    f"NERSC API returned status {response.status}: {await response.text()}"
                )
    except aiohttp.ClientError as e:
        raise Exception(f"Failed to connect to NERSC API: {str(e)}")


def _format_status_summary(status_data: dict[str, Any]) -> str:
    """Format status data into a human-readable summary."""
    summary = ["NERSC System Status Summary", "=" * 30, ""]
    if not status_data:
        return "No status data available from NERSC API."

    systems = status_data.get("systems", status_data)
    for system_name, system_info in systems.items():
        status = system_info.get("status", "Unknown")
        description = system_info.get("description", "")
        formatted_name = system_name.replace("_", " ").title()
        summary.append(f"🖥️  {formatted_name}:")
        if status.lower() in ["active", "available", "up"]:
            summary.append(f"   Status: ✅ {status}")
        elif status.lower() in ["degraded", "limited"]:
            summary.append(f"   Status: ⚠️  {status}")
        else:
            summary.append(f"   Status: ❌ {status}")
        if description and description != status:
            summary.append(f"   Info: {description}")
        if "maintenance" in system_info and system_info["maintenance"]:
            summary.append(f"   Maintenance: {system_info['maintenance']}")
        if "updated" in system_info:
            summary.append(f"   Last Updated: {system_info['updated']}")
        summary.append("")
    return "\n".join(summary)


@mcp.resource(uri="nersc://status/systems")
async def get_systems_resource() -> str:
    """Fetch raw JSON for all NERSC systems."""
    data = await _get_system_status()
    return json.dumps(data, indent=2)


@mcp.resource(uri="nersc://status/systems/summary")
async def get_summary_resource() -> str:
    """Fetch human-readable summary of all NERSC systems."""
    data = await _get_system_status()
    # convert list-of-dicts to dict by name
    data_dict = {item["name"]: item for item in data}
    return _format_status_summary(data_dict)


@mcp.resource(uri="nersc://status/{system}")
async def get_system_resource_individual(system: str) -> str:
    """Fetch raw JSON for a specific NERSC system."""
    data = await _get_system_status()
    item = next((s for s in data if s.get("name") == system), None)
    if not item:
        raise Exception(f"System '{system}' not found.")
    return json.dumps(item, indent=2)


@mcp.resource(uri="nersc://status/{system}/summary")
async def get_system_summary_resource_individual(system: str) -> str:
    """Fetch human-readable summary for a specific NERSC system."""
    data = await _get_system_status()
    item = next((s for s in data if s.get("name") == system), None)
    if not item:
        raise Exception(f"System '{system}' not found.")
    # Use formatting helper for a single-item dict
    return _format_status_summary({system: item})


@mcp.resource(uri="nersc://status/{system}/get_availability")
async def get_system_availability(system: str) -> str:
    """Fetch availability status for a specific NERSC system."""
    data = await _get_system_status()
    item = next((s for s in data if s.get("name") == system), None)
    if not item:
        raise Exception(f"System '{system}' not found.")
    status = item.get("status", "Unknown")
    formatted_name = system.replace("_", " ").title()
    if status.lower() in ["active", "available", "up"]:
        text = f"✅ {formatted_name} is AVAILABLE"
    elif status.lower() in ["degraded", "limited"]:
        text = f"⚠️ {formatted_name} is PARTIALLY AVAILABLE"
    else:
        text = f"❌ {formatted_name} is UNAVAILABLE"
    text += f"\nStatus: {status}"
    desc = item.get("description", "")
    if desc and desc != status:
        text += f"\nDetails: {desc}"
    return text


@mcp.resource(uri="nersc://status/{system}/get_maintenance")
async def get_system_maintenance(system: str) -> str:
    """Fetch maintenance info for a specific NERSC system."""
    data = await _get_system_status()
    item = next((s for s in data if s.get("name") == system), None)
    if not item:
        raise Exception(f"System '{system}' not found.")
    formatted_name = system.replace("_", " ").title()
    status = item.get("status", "").lower()
    desc = item.get("description", "").lower()
    lines = []
    if "maint" in status or "maint" in desc:
        lines.append(
            f"🔧 {formatted_name}: {item.get('description', 'Scheduled maintenance')}"
        )
    elif status in ["down", "offline"]:
        lines.append(f"❌ {formatted_name}: Currently down")
    text = "\n".join(lines) or f"No maintenance info for {formatted_name}."
    return text


@mcp.tool(enabled=False)
async def get_nersc_status_json(ctx: Context) -> str:
    """Fetch raw JSON for all NERSC systems to the user."""
    uri = "nersc://status/systems"
    await ctx.info(f"Fetching system status from {uri}")
    res = await ctx.read_resource(uri)
    return res


@mcp.tool
async def get_nersc_status(ctx: Context) -> str:
    """Fetch human-readable summary of all NERSC systems to the user."""
    uri = "nersc://status/systems/summary"
    await ctx.info(f"Fetching system status from {uri}")
    res = await ctx.read_resource(uri)
    return res


@mcp.tool(enabled=False)
async def get_nersc_status_individual_json(system: str, ctx: Context) -> str:
    """Tool to get raw JSON status for a NERSC system."""
    uri = f"nersc://status/{system}"
    await ctx.info(f"Fetching system status from {uri}")
    res = await ctx.read_resource(uri)
    return res


@mcp.tool
async def get_nersc_status_individual(system: str, ctx: Context) -> str:
    """Tool to get text summary for a NERSC system."""
    uri = f"nersc://status/{system}/summary"
    await ctx.info(f"Fetching system summary from {uri}")
    res = await ctx.read_resource(uri)
    return res


@mcp.tool
async def check_system_availability(system: str, ctx: Context) -> str:
    """Tool to get availability info for a NERSC system."""
    uri = f"nersc://status/{system}/get_availability"
    await ctx.info(f"Checking availability at {uri}")
    res = await ctx.read_resource(uri)
    return res


@mcp.tool
async def get_maintenance_info(system: str, ctx: Context) -> str:
    """Tool to get maintenance info for a NERSC system."""
    uri = f"nersc://status/{system}/get_maintenance"
    await ctx.info(f"Checking maintenance at {uri}")
    res = await ctx.read_resource(uri)
    return res


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        path="/mcps/nersc-status",
    )
