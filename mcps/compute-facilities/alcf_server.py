#!/usr/bin/env python3
"""
ALCF Polaris MCP Server

This MCP server provides tools and resources to monitor ALCF Polaris cluster status and job activity.
"""

import json
import logging
from datetime import datetime

import aiohttp
from fastmcp import Context, FastMCP

logger = logging.getLogger(__name__)
mcp = FastMCP("ALCF Polaris Status Bridge")

ALCF_STATUS_URL = "https://status.alcf.anl.gov/polaris/activity.json"


async def _get_http_session() -> aiohttp.ClientSession:
    if not hasattr(_get_http_session, "session"):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; Globus-Labs-Science-MCP-Agent/1.0;"
                " +https://github.com/globus-labs/science-mcps)"
            )
        }
        _get_http_session.session = aiohttp.ClientSession(headers=headers)
    return _get_http_session.session


async def _fetch_activity_data() -> dict:
    session = await _get_http_session()
    try:
        async with session.get(ALCF_STATUS_URL) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                raise Exception(f"HTTP {resp.status}: {await resp.text()}")
    except Exception as e:
        logger.error(f"Error fetching ALCF activity: {e}")
        raise


async def _get_system_status() -> dict:
    """Summarize system status."""
    data = await _fetch_activity_data()
    running = data.get("running", [])
    starting = data.get("starting", [])
    queued = data.get("queued", [])
    total = len(running) + len(starting) + len(queued)
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system_operational": bool(running),
        "total_jobs": total,
        "running_jobs": len(running),
        "starting_jobs": len(starting),
        "queued_jobs": len(queued),
    }


async def _get_job_activity() -> dict:
    """Return raw job activity data."""
    return await _fetch_activity_data()


async def _check_alcf_status(detailed: bool = False) -> str:
    """Return a formatted status report."""
    try:
        data = await _fetch_activity_data()
        running_jobs = data.get("running", [])
        starting_jobs = data.get("starting", [])
        queued_jobs = data.get("queued", [])

        total_jobs = len(running_jobs) + len(queued_jobs) + len(starting_jobs)

        if total_jobs == 0:
            return "⚠️  ALCF Polaris Status: No job data available"

        # Generate status report
        status_lines = [
            f"🖥️  ALCF Polaris System Status - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "=" * 60,
        ]

        if running_jobs:
            status_lines.append(
                f"✅ System Status: OPERATIONAL ({len(running_jobs)} jobs running)"
            )
        else:
            status_lines.append("❌ System Status: NO RUNNING JOBS")

        status_lines.append(f"📊 Total Jobs: {total_jobs}")

        # Job state breakdown
        status_lines.append("\n📋 Job State Summary:")
        status_lines.append(f"   🟢 RUNNING: {len(running_jobs)}")
        status_lines.append(f"   🔵 QUEUED: {len(queued_jobs)}")
        status_lines.append(f"   ⚪ STARTING: {len(starting_jobs)}")

        if detailed and running_jobs:
            status_lines.append(f"\n🏃 Running Jobs Details:")
            for i, job in enumerate(running_jobs[:10]):  # Limit to first 10
                job_id = job.get("jobid", "unknown")
                project = job.get("project", "unknown")
                nodes = job.get("location", "unknown")
                queue = job.get("queue", "unknown")
                status_lines.append(
                    f"   {i + 1}. Job {job_id} | Project: {project} | Queue: {queue} | Nodes: {nodes}"
                )

            if len(running_jobs) > 10:
                status_lines.append(f"   ... and {len(running_jobs) - 10} more")

        return "\n".join(status_lines)

    except Exception as e:
        return f"❌ Error checking ALCF status: {str(e)}"


async def _get_running_jobs(limit: int = 10) -> str:
    """Return a formatted list of running jobs."""
    try:
        data = await _fetch_activity_data()
        running_jobs = data.get("running", [])

        if not running_jobs:
            return "📋 No running jobs found on ALCF Polaris"

        result_lines = [
            f"🏃 Running Jobs on ALCF Polaris ({len(running_jobs)} total)",
            "=" * 50,
        ]

        for i, job in enumerate(running_jobs[:limit]):
            job_id = job.get("jobid", "N/A")
            project = job.get("project", "N/A")
            nodes = job.get("location", "N/A")
            queue = job.get("queue", "N/A")
            start_time = job.get("starttime", "N/A")

            result_lines.append(f"\n🔹 Job #{i + 1}")
            result_lines.append(f"   Job ID: {job_id}")
            result_lines.append(f"   Project: {project}")
            result_lines.append(f"   Nodes: {nodes}")
            result_lines.append(f"   Queue: {queue}")
            result_lines.append(f"   Start Time: {start_time}")

        if len(running_jobs) > limit:
            result_lines.append(
                f"\n... and {len(running_jobs) - limit} more running jobs"
            )

        return "\n".join(result_lines)

    except Exception as e:
        return f"❌ Error retrieving running jobs: {str(e)}"


async def _get_system_health_summary() -> str:
    """Return a formatted health summary."""
    try:
        data = await _fetch_activity_data()
        running_jobs = data.get("running", [])
        starting_jobs = data.get("starting", [])
        queued_jobs = data.get("queued", [])

        total_jobs = len(running_jobs) + len(queued_jobs) + len(starting_jobs)

        if total_jobs == 0:
            return "⚠️  System Health: Unable to determine - No job data available"

        # Determine health status
        if len(running_jobs) > 0:
            health_status = "HEALTHY"
            emoji = "💚"
        elif len(queued_jobs) > 0:
            health_status = "IDLE"
            emoji = "💛"
        else:
            health_status = "INACTIVE"
            emoji = "❤️"

        summary_lines = [
            f"{emoji} ALCF Polaris System Health Summary",
            "=" * 40,
            f"Overall Status: {health_status}",
            f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "📊 Job Statistics:",
            f"   • Total Jobs: {total_jobs}",
            f"   • Running: {len(running_jobs)}",
            f"   • Queued: {len(queued_jobs)}",
            "",
            f"🎯 Jobs running: {(len(running_jobs) / max(total_jobs, 1)) * 100:.1f}%",
        ]

        # Add recommendations
        if len(running_jobs) == 0 and len(queued_jobs) > 0:
            summary_lines.append(
                "\n💡 Note: Jobs are queued but none are running. System may be in maintenance or experiencing issues."
            )
        elif len(running_jobs) == 0 and len(queued_jobs) == 0:
            summary_lines.append(
                "\n💡 Note: No active job activity detected. System may be offline or in maintenance."
            )

        return "\n".join(summary_lines)

    except Exception as e:
        return f"❌ Error generating health summary: {str(e)}"


@mcp.resource(uri="alcf://polaris/status")
async def get_status_resource() -> str:
    return json.dumps(await _get_system_status(), indent=2)


@mcp.resource(uri="alcf://polaris/status/summary")
async def get_status_summary_resource() -> str:
    return await _check_alcf_status(False)


@mcp.resource(uri="alcf://polaris/jobs")
async def get_jobs_resource() -> str:
    return json.dumps(await _get_job_activity(), indent=2)


@mcp.resource(uri="alcf://polaris/jobs/summary")
async def get_jobs_summary_resource() -> str:
    return await _get_running_jobs(10)


@mcp.resource(uri="alcf://polaris/status/health")
async def get_health_resource() -> str:
    return await _get_system_health_summary()


@mcp.tool(enabled=False)
async def check_alcf_status_json(ctx: Context) -> str:
    uri = "alcf://polaris/status"
    await ctx.info(f"Fetching status JSON from {uri}")
    res = await ctx.read_resource(uri)
    return res


@mcp.tool
async def check_alcf_status(ctx: Context) -> str:
    uri = "alcf://polaris/status/summary"
    await ctx.info(f"Fetching status summary from {uri}")
    res = await ctx.read_resource(uri)
    return res


@mcp.tool(enabled=False)
async def get_running_jobs_json(ctx: Context) -> str:
    uri = "alcf://polaris/jobs"
    await ctx.info(f"Fetching job activity JSON from {uri}")
    res = await ctx.read_resource(uri)
    return res


@mcp.tool
async def get_running_jobs(ctx: Context) -> str:
    uri = "alcf://polaris/jobs/summary"
    await ctx.info(f"Fetching job activity summary from {uri}")
    res = await ctx.read_resource(uri)
    return res


@mcp.tool
async def system_health_summary(ctx: Context) -> str:
    uri = "alcf://polaris/status/health"
    await ctx.info(f"Fetching health summary from {uri}")
    res = await ctx.read_resource(uri)
    return res


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http", host="0.0.0.0", port=8000, path="/mcps/alcf-status"
    )
