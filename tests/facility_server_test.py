import os
import sys

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

# Add the compute_facilities directory to the path to import facility_server
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "mcps", "compute_facilities")
)

import facility_server


@pytest.mark.asyncio
async def test_get_nersc_status():
    """Test the get_nersc_status tool returns the API model with systems."""
    async with Client(facility_server.mcp) as client:
        res = await client.call_tool("get_nersc_status")
        data = res.data
        assert hasattr(data, "systems")
        assert isinstance(data.systems, list)
        assert len(data.systems) > 0


@pytest.mark.asyncio
async def test_get_nersc_system_status_valid_system():
    """Test the get_nersc_system_status tool with a valid system name."""
    async with Client(facility_server.mcp) as client:
        res = await client.call_tool(
            "get_nersc_system_status", {"system_name": "perlmutter"}
        )
        data = res.data
        assert data.name.lower() == "perlmutter"
        assert hasattr(data, "full_name")
        assert hasattr(data, "status")
        assert hasattr(data, "system_type")
        assert data.system_type.lower() == "compute"


@pytest.mark.asyncio
async def test_get_nersc_system_status_invalid_system():
    """Test the get_nersc_system_status tool with an invalid system name."""
    async with Client(facility_server.mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "get_nersc_system_status", {"system_name": "fake_system_123"}
            )


@pytest.mark.asyncio
async def test_get_nersc_system_status_filesystem_system():
    """Test the get_nersc_system_status tool with a filesystem system."""
    async with Client(facility_server.mcp) as client:
        res = await client.call_tool(
            "get_nersc_system_status", {"system_name": "global_common"}
        )
        data = res.data
        assert hasattr(data, "full_name")
        assert hasattr(data, "status")
        assert data.system_type.lower() == "filesystem"


@pytest.mark.asyncio
@pytest.mark.parametrize("resource", ["polaris", "aurora"])
@pytest.mark.parametrize("kind", ["running", "starting", "queued", "reservation"])
async def test_get_alcf_jobs_all_kinds_all_resources(resource: str, kind: str):
    """Test get_alcf_jobs across all kinds for both polaris and aurora."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool(
            "get_alcf_jobs", {"kind": kind, "resource": resource}
        )
        data = result.data
        assert hasattr(data, "tasks")
        assert hasattr(data, "total")
        assert isinstance(data.total, int)


@pytest.mark.asyncio
async def test_get_nersc_system_status_service_system():
    """Test the get_nersc_system_status tool with a service system."""
    async with Client(facility_server.mcp) as client:
        res = await client.call_tool(
            "get_nersc_system_status", {"system_name": "jupyter"}
        )
        data = res.data
        assert data.system_type.lower() == "service"


@pytest.mark.asyncio
async def test_get_nersc_system_status_case_insensitive():
    """Test the get_nersc_system_status tool with case-insensitive system names."""
    async with Client(facility_server.mcp) as client:
        res = await client.call_tool(
            "get_nersc_system_status", {"system_name": "PERLMUTTER"}
        )
        data = res.data
        assert data.name.lower() == "perlmutter"


@pytest.mark.asyncio
async def test_get_alcf_status():
    """Test the get_alcf_status tool returns a dictionary with system status."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool("get_alcf_status")
        data = result.data
        assert hasattr(data, "is_operational")
        assert hasattr(data, "motd_info")
        assert hasattr(data, "maintenance_info")
        assert hasattr(data, "job_counts")
        assert hasattr(data, "last_updated")


@pytest.mark.asyncio
async def test_get_alcf_running_tasks():
    """Test fetching running tasks via the unified get_alcf_jobs tool."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool("get_alcf_jobs", {"kind": "running"})
        data = result.data
        assert hasattr(data, "tasks")
        assert hasattr(data, "total")
        assert isinstance(data.total, int)


@pytest.mark.asyncio
async def test_get_alcf_running_tasks_with_pagination():
    """Test the get_alcf_jobs tool (running) with custom pagination."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool(
            "get_alcf_jobs", {"kind": "running", "n": 5, "skip": 0}
        )
        data = result.data
        assert hasattr(data, "tasks")
        assert hasattr(data, "total")
        assert len(data.tasks) <= 5


@pytest.mark.asyncio
async def test_get_alcf_starting_tasks():
    """Test fetching starting tasks via the unified get_alcf_jobs tool."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool("get_alcf_jobs", {"kind": "starting"})
        data = result.data
        assert hasattr(data, "tasks")
        assert hasattr(data, "total")
        assert isinstance(data.total, int)


@pytest.mark.asyncio
async def test_get_alcf_queued_tasks():
    """Test fetching queued tasks via the unified get_alcf_jobs tool."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool("get_alcf_jobs", {"kind": "queued"})
        data = result.data
        assert hasattr(data, "tasks")
        assert hasattr(data, "total")
        assert isinstance(data.total, int)


@pytest.mark.asyncio
async def test_get_alcf_queued_tasks_with_pagination():
    """Test the get_alcf_jobs tool (queued) with custom pagination."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool(
            "get_alcf_jobs", {"kind": "queued", "n": 3, "skip": 5}
        )
        data = result.data
        assert hasattr(data, "tasks")
        assert hasattr(data, "total")
        assert len(data.tasks) <= 3


@pytest.mark.asyncio
async def test_get_alcf_reservation_tasks():
    """Test fetching reservation tasks via the unified get_alcf_jobs tool."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool("get_alcf_jobs", {"kind": "reservation"})
        data = result.data
        assert hasattr(data, "tasks")
        assert hasattr(data, "total")
        assert isinstance(data.total, int)


@pytest.mark.asyncio
async def test_resource_nersc_status_systems():
    """Resource read: nersc://status/systems returns systems list."""
    async with Client(facility_server.mcp) as client:
        res = await client.read_resource("nersc://status/systems")
        # Accept various shapes: model with .systems, dict with key, or content list
        if hasattr(res, "content"):
            items = getattr(res, "content") or []
            assert isinstance(items, list)
            assert len(items) > 0
        elif hasattr(res, "data"):
            data = res.data
            has = lambda k: (k in data) if isinstance(data, dict) else hasattr(data, k)
            get = lambda k: (data[k] if isinstance(data, dict) else getattr(data, k))
            assert has("systems")
            systems = get("systems")
            assert isinstance(systems, list) and len(systems) > 0
        else:
            # fallback minimal assertion
            assert res is not None


@pytest.mark.asyncio
async def test_resource_alcf_polaris_status():
    """Resource read: alcf://polaris/status returns ALCF status payload."""
    async with Client(facility_server.mcp) as client:
        res = await client.read_resource("alcf://polaris/status")
        if hasattr(res, "content"):
            items = getattr(res, "content") or []
            assert isinstance(items, list)
            assert len(items) > 0
        elif hasattr(res, "data"):
            data = getattr(res, "data")
            assert data is not None
        else:
            assert res is not None


@pytest.mark.asyncio
async def test_resource_alcf_aurora_status():
    """Resource read: alcf://aurora/status returns ALCF status payload."""
    async with Client(facility_server.mcp) as client:
        res = await client.read_resource("alcf://aurora/status")
        if hasattr(res, "content"):
            items = getattr(res, "content") or []
            assert isinstance(items, list)
            assert len(items) > 0
        elif hasattr(res, "data"):
            data = getattr(res, "data")
            assert data is not None
        else:
            assert res is not None
