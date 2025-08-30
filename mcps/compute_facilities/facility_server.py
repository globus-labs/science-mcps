#!/usr/bin/env python3
"""
NERSC Status MCP Server (Async Version)
Provides tools to check NERSC and ALCF system status using Pydantic validation and aiohttp.
"""

import logging
from typing import Any, Optional
from urllib.parse import urljoin

import aiohttp
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)
mcp = FastMCP("NERSC Status MCP Server (Async)")

NERSC_API_BASE = "https://api.nersc.gov/api/v1.2/"
NERSC_STATUS_ENDPOINT = "status/"

ALCF_STATUS_URL = "https://status.alcf.anl.gov/polaris/activity.json"


class NERSCSystem(BaseModel):
    name: str = Field(description="System identifier name")
    full_name: str = Field(description="Full display name of the system")
    description: str = Field(description="Description of the system status")
    system_type: str = Field(
        description="Type of system (compute, filesystem, service, storage)"
    )
    notes: list[str] = Field(description="Additional notes about the system")
    status: str = Field(description="Current status of the system")
    updated_at: str = Field(description="Timestamp of last status update")

    def matches_name(self, search_name: str) -> bool:
        """Case-insensitive system name matching."""
        return self.name.lower() == search_name.lower()


class NERSCStatusResponse(BaseModel):
    systems: list[NERSCSystem] = Field(
        description="List of all NERSC systems and their status"
    )


class ALCFJob(BaseModel):
    jobid: str = Field(description="Job identifier")
    project: str = Field(description="Project name")
    queue: str = Field(description="Queue name")
    starttime: str = Field(description="Job start time")


class ALCFMOTD(BaseModel):
    display_end: str = Field(description="Display end time")
    display_start: str = Field(description="Display start time")
    message: str = Field(description="Message content")
    resource: str = Field(description="Resource name")
    type: str = Field(description="Message type")


class ALCFStatusResponse(BaseModel):
    # Maintenance fields
    maint: Optional[bool] = Field(default=None, description="System in maintenance")
    start: Optional[int] = Field(
        default=None, description="Maintenance start timestamp"
    )
    end: Optional[int] = Field(default=None, description="Maintenance end timestamp")

    # Job queue fields
    running: Optional[list[ALCFJob]] = Field(default=None, description="Running jobs")
    starting: Optional[list[ALCFJob]] = Field(default=None, description="Starting jobs")
    queued: Optional[list[ALCFJob]] = Field(default=None, description="Queued jobs")
    reservation: Optional[list[ALCFJob]] = Field(
        default=None, description="Reservations"
    )
    motd_info: Optional[list[ALCFMOTD]] = Field(
        default=None, description="Messages of the day"
    )
    updated: Optional[int] = Field(default=None, description="Last update timestamp")


async def _get_nersc_status() -> NERSCStatusResponse:
    """Fetch and validate NERSC system status."""
    url = urljoin(NERSC_API_BASE, NERSC_STATUS_ENDPOINT)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return NERSCStatusResponse(systems=data)

    except aiohttp.ClientError as e:
        raise ToolError(f"Failed to connect to NERSC API: {e}")
    except ValidationError as e:
        raise ToolError(f"NERSC API response has an unexpected format: {e}")


async def _get_alcf_status() -> ALCFStatusResponse:
    """Fetch and validate ALCF Polaris status."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ALCF_STATUS_URL) as response:
                response.raise_for_status()
                data = await response.json()
                return ALCFStatusResponse(**data)

    except aiohttp.ClientError as e:
        raise ToolError(f"Failed to connect to ALCF API: {e}")
    except ValidationError as e:
        raise ToolError(f"ALCF API response has an unexpected format: {e}")


def _format_nersc_system_status(system: NERSCSystem) -> list[str]:
    """Format single NERSC system status for display."""
    status_emoji_map = {
        "active": "✅",
        "available": "✅",
        "up": "✅",
        "degraded": "⚠️",
        "limited": "⚠️",
    }
    emoji = status_emoji_map.get(system.status.lower(), "❌")
    formatted_name = system.full_name.replace("_", " ")

    result = [
        f"🖥️  {formatted_name} ({system.name}):",
        f"   Status: {emoji} {system.status}",
    ]
    if system.description and system.description != system.status:
        result.append(f"   Info: {system.description}")
    result.append(f"   Last Updated: {system.updated_at}")
    return result


def _format_nersc_status_summary(status_response: NERSCStatusResponse) -> str:
    """Format full NERSC status response for display."""
    if not status_response.systems:
        return "No status data available from NERSC API."

    sorted_systems = sorted(status_response.systems, key=lambda s: s.full_name)
    summary_lines = ["NERSC System Status Summary", "=" * 30, ""]
    for system in sorted_systems:
        summary_lines.extend(_format_nersc_system_status(system))
        summary_lines.append("")
    return "\n".join(summary_lines)


@mcp.resource(uri="nersc://status/systems")
async def get_nersc_resource() -> str:
    """Get raw JSON for all NERSC systems."""
    data = await _get_nersc_status()
    return data.model_dump_json(indent=2)


@mcp.resource(uri="alcf://polaris/status")
async def get_alcf_status_resource() -> str:
    """Get raw JSON for ALCF Polaris status."""
    data = await _get_alcf_status()
    return data.model_dump_json(indent=2)


@mcp.tool
async def get_nersc_status() -> str:
    """Get human-readable summary of all NERSC systems."""
    status_response = await _get_nersc_status()
    return _format_nersc_status_summary(status_response)


@mcp.tool
async def get_nersc_system_status(system_name: str) -> str:
    """Get status of specific NERSC system."""
    status_response = await _get_nersc_status()
    system = next(
        (s for s in status_response.systems if s.matches_name(system_name)), None
    )

    if not system:
        available = sorted([s.name for s in status_response.systems])
        return f"System '{system_name}' not found. Available systems: {', '.join(available)}"

    result = [f"Status for {system.full_name}", "=" * (11 + len(system.full_name)), ""]
    result.extend(_format_nersc_system_status(system))
    result.extend(
        [
            f"   System Type: {system.system_type}",
            f"   Notes: {', '.join(system.notes) if system.notes else 'None'}",
        ]
    )
    return "\n".join(result)


@mcp.tool
async def get_alcf_status() -> dict[str, Any]:
    """Get ALCF Polaris status with system availability information."""
    from datetime import datetime

    status_response = await _get_alcf_status()

    # Determine system operational status
    is_operational = True
    if status_response.maint:
        is_operational = False
    elif status_response.motd_info:
        for motd in status_response.motd_info:
            if motd.type == "MAINT":
                is_operational = False
                break

    result = {
        "is_operational": is_operational,
        "motd_info": status_response.motd_info,
        "maintenance_info": {
            "start": status_response.start,
            "end": status_response.end,
        },
        "job_counts": {
            "running": len(status_response.running) if status_response.running else 0,
            "starting": len(status_response.starting)
            if status_response.starting
            else 0,
            "queued": len(status_response.queued) if status_response.queued else 0,
            "reservation": len(status_response.reservation)
            if status_response.reservation
            else 0,
        },
        "last_updated": status_response.updated,
    }

    return result


@mcp.tool
async def get_alcf_running_tasks(n: int = 10, skip: int = 0) -> dict[str, Any]:
    """Get ALCF Polaris running tasks with pagination."""
    status_response = await _get_alcf_status()

    running_tasks = []
    total_running = 0

    if status_response.running:
        total_running = len(status_response.running)
        start_idx = skip
        end_idx = min(start_idx + n, total_running)

        if start_idx < total_running:
            for i in range(start_idx, end_idx):
                task = status_response.running[i]
                running_tasks.append(
                    {
                        "jobid": task.jobid,
                        "project": task.project,
                        "queue": task.queue,
                        "starttime": task.starttime,
                    }
                )

    return {"total": total_running, "tasks": running_tasks}


@mcp.tool
async def get_alcf_starting_tasks(n: int = 10, skip: int = 0) -> dict[str, Any]:
    """Get ALCF Polaris starting tasks with pagination."""
    status_response = await _get_alcf_status()

    starting_tasks = []
    total_starting = 0

    if status_response.starting:
        total_starting = len(status_response.starting)
        start_idx = skip
        end_idx = min(start_idx + n, total_starting)

        if start_idx < total_starting:
            for i in range(start_idx, end_idx):
                task = status_response.starting[i]
                starting_tasks.append(
                    {
                        "jobid": task.jobid,
                        "project": task.project,
                        "queue": task.queue,
                        "starttime": task.starttime,
                    }
                )

    return {"total": total_starting, "tasks": starting_tasks}


@mcp.tool
async def get_alcf_queued_tasks(n: int = 10, skip: int = 0) -> dict[str, Any]:
    """Get ALCF Polaris queued tasks with pagination."""
    status_response = await _get_alcf_status()

    queued_tasks = []
    total_queued = 0

    if status_response.queued:
        total_queued = len(status_response.queued)
        start_idx = skip
        end_idx = min(start_idx + n, total_queued)

        if start_idx < total_queued:
            for i in range(start_idx, end_idx):
                task = status_response.queued[i]
                queued_tasks.append(
                    {
                        "jobid": task.jobid,
                        "project": task.project,
                        "queue": task.queue,
                        "starttime": task.starttime,
                    }
                )

    return {"total": total_queued, "tasks": queued_tasks}


@mcp.tool
async def get_alcf_reservation_tasks(n: int = 10, skip: int = 0) -> dict[str, Any]:
    """Get ALCF Polaris reservation tasks with pagination."""
    status_response = await _get_alcf_status()

    reservation_tasks = []
    total_reservation = 0

    if status_response.reservation:
        total_reservation = len(status_response.reservation)
        start_idx = skip
        end_idx = min(start_idx + n, total_reservation)

        if start_idx < total_reservation:
            for i in range(start_idx, end_idx):
                task = status_response.reservation[i]
                reservation_tasks.append(
                    {
                        "jobid": task.jobid,
                        "project": task.project,
                        "queue": task.queue,
                        "starttime": task.starttime,
                    }
                )

    return {"total": total_reservation, "tasks": reservation_tasks}


if __name__ == "__main__":
    mcp.run(transport="stdio")
