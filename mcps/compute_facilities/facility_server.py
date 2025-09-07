#!/usr/bin/env python3
"""
NERSC and ALCF Status MCP Server
Provides tools to check NERSC and ALCF system status using Pydantic validation and aiohttp.
"""

import logging
from typing import Any, Literal
from urllib.parse import urljoin

import aiohttp
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import ValidationError
from schemas import (
    ALCFApiResponse,
    ALCFJob,
    ALCFJobsResponse,
    ALCFStatusResponse,
    NERSCApiResponse,
    NERSCSystem,
)

logger = logging.getLogger(__name__)
mcp = FastMCP("NERSC Status MCP Server (Async)")

NERSC_API_BASE = "https://api.nersc.gov/api/v1.2/"
NERSC_STATUS_ENDPOINT = "status/"
ALCF_API_BASE = "https://status.alcf.anl.gov/"
ALCF_STATUS_ENDPOINT = "activity.json"


async def _fetch_json(url: str) -> Any:
    """Fetch JSON from a URL; raise ToolError on HTTP failures."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as e:
        raise ToolError(f"Failed to connect to {url}: {e}")


async def _get_nersc_status() -> NERSCApiResponse:
    """Fetch NERSC systems and validate against schema."""
    url = urljoin(NERSC_API_BASE, NERSC_STATUS_ENDPOINT)
    try:
        data = await _fetch_json(url)
        return NERSCApiResponse(systems=data)
    except ValidationError as e:
        raise ToolError(f"NERSC API response has an unexpected format: {e}")


def _alcf_status_url(resource: str) -> str:
    """Build the ALCF status URL for a resource (e.g., 'polaris')."""
    resource = resource.strip().lower()
    # basic guard against path traversal or invalid characters
    if not resource.replace("_", "").replace("-", "").isalnum():
        raise ToolError(f"Invalid ALCF resource name: {resource}")
    return urljoin(ALCF_API_BASE, f"{resource}/{ALCF_STATUS_ENDPOINT}")


async def _get_alcf_status(resource: str = "polaris") -> ALCFApiResponse:
    """Fetch ALCF status for a resource and validate."""
    try:
        data = await _fetch_json(_alcf_status_url(resource))
        return ALCFApiResponse(**data)
    except ValidationError as e:
        raise ToolError(f"ALCF API response has an unexpected format: {e}")


@mcp.resource(uri="nersc://status/systems")
async def get_nersc_status_resource() -> NERSCApiResponse:
    """Resource: NERSC systems status (API response)."""
    return await _get_nersc_status()


@mcp.resource(uri="alcf://{resource}/status")
async def get_alcf_status_resource(resource: str) -> ALCFApiResponse:
    """Resource: ALCF status for the given resource (e.g., 'polaris', 'aurora')."""
    return await _get_alcf_status(resource)


@mcp.tool
async def get_nersc_status() -> NERSCApiResponse:
    """Tool: list all NERSC systems with status."""
    status_response = await _get_nersc_status()
    return status_response


@mcp.tool
async def get_nersc_system_status(system_name: str) -> NERSCSystem:
    """Tool: get one NERSC system by name."""
    status_response = await _get_nersc_status()
    target = system_name.lower()
    system = next(
        (s for s in status_response.systems if s.name.lower() == target), None
    )

    if not system:
        available = sorted([s.name for s in status_response.systems])
        raise ToolError(
            f"System '{system_name}' not found. Available systems: {', '.join(available)}"
        )

    return system


@mcp.tool
async def get_alcf_status(resource: str = "polaris") -> ALCFStatusResponse:
    """Tool: summarized ALCF status for a resource."""
    status_response = await _get_alcf_status(resource)

    # Determine system operational status
    is_operational = True
    if status_response.maint:
        is_operational = False
    elif status_response.motd_info:
        for motd in status_response.motd_info:
            if motd.type == "MAINT":
                is_operational = False
                break

    return ALCFStatusResponse(
        is_operational=is_operational,
        motd_info=status_response.motd_info,
        maintenance_info={
            "start": status_response.start,
            "end": status_response.end,
        },
        job_counts={
            "running": len(status_response.running),
            "starting": len(status_response.starting),
            "queued": len(status_response.queued),
            "reservation": len(status_response.reservation),
        },
        last_updated=status_response.updated,
    )


def _paginate_jobs(tasks: list[ALCFJob] | None, n: int, skip: int) -> ALCFJobsResponse:
    """Paginate ALCF jobs (limit n, offset skip)."""
    total = len(tasks) if tasks else 0
    if not tasks or skip >= total:
        return ALCFJobsResponse(total=total, tasks=[])

    end_idx = min(skip + n, total)
    # tasks are parsed as list[ALCFJob]; slice and return directly
    return ALCFJobsResponse(total=total, tasks=list(tasks[skip:end_idx]))


@mcp.tool
async def get_alcf_jobs(
    kind: Literal["running", "starting", "queued", "reservation"],
    n: int = 10,
    skip: int = 0,
    resource: str = "polaris",
) -> ALCFJobsResponse:
    """Tool: paginated ALCF jobs by kind and resource.

    kind must be one of: 'running', 'starting', 'queued', 'reservation'.
    resource examples: 'polaris', 'aurora'.
    """
    status_response = await _get_alcf_status(resource)
    tasks_map = {
        "running": status_response.running,
        "starting": status_response.starting,
        "queued": status_response.queued,
        "reservation": status_response.reservation,
    }
    return _paginate_jobs(tasks_map[kind], n, skip)


if __name__ == "__main__":
    mcp.run(transport="stdio")
