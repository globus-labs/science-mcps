import os
import sys

import pytest
from fastmcp import Client

# Add the compute_facilities directory to the path to import facility_server
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "mcps", "compute_facilities")
)

import facility_server


@pytest.mark.asyncio
async def test_get_nersc_status():
    """Test the get_nersc_status tool returns summary of all systems."""
    async with Client(facility_server.mcp) as client:
        raw = await client.call_tool("get_nersc_status")
        assert "NERSC System Status Summary" in raw.data
        assert "🖥️" in raw.data  # Should contain system icons


@pytest.mark.asyncio
async def test_get_nersc_system_status_valid_system():
    """Test the get_nersc_system_status tool with a valid system name."""
    async with Client(facility_server.mcp) as client:
        # Test with Perlmutter system
        raw = await client.call_tool(
            "get_nersc_system_status", {"system_name": "perlmutter"}
        )
        assert "Status for Perlmutter" in raw.data
        assert "🖥️" in raw.data
        assert "Status:" in raw.data
        assert "System Type:" in raw.data


@pytest.mark.asyncio
async def test_get_nersc_system_status_invalid_system():
    """Test the get_nersc_system_status tool with an invalid system name."""
    async with Client(facility_server.mcp) as client:
        # Test with non-existent system
        raw = await client.call_tool(
            "get_nersc_system_status", {"system_name": "fake_system_123"}
        )
        assert "not found" in raw.data
        assert "Available systems:" in raw.data


@pytest.mark.asyncio
async def test_get_nersc_system_status_filesystem_system():
    """Test the get_nersc_system_status tool with a filesystem system."""
    async with Client(facility_server.mcp) as client:
        # Test with Global Common filesystem
        raw = await client.call_tool(
            "get_nersc_system_status", {"system_name": "global_common"}
        )
        assert "Status for Global Common" in raw.data
        assert "🖥️" in raw.data
        assert "Status:" in raw.data
        assert "System Type:" in raw.data


@pytest.mark.asyncio
async def test_get_nersc_system_status_compute_system():
    """Test the get_nersc_system_status tool with a compute system."""
    async with Client(facility_server.mcp) as client:
        # Test with Perlmutter compute system
        raw = await client.call_tool(
            "get_nersc_system_status", {"system_name": "perlmutter"}
        )
        assert "Status for Perlmutter" in raw.data
        assert "System Type: compute" in raw.data


@pytest.mark.asyncio
async def test_get_nersc_system_status_service_system():
    """Test the get_nersc_system_status tool with a service system."""
    async with Client(facility_server.mcp) as client:
        # Test with Jupyter service
        raw = await client.call_tool(
            "get_nersc_system_status", {"system_name": "jupyter"}
        )
        assert "Status for Jupyter" in raw.data
        assert "🖥️" in raw.data
        assert "Status:" in raw.data


@pytest.mark.asyncio
async def test_get_nersc_system_status_case_insensitive():
    """Test the get_nersc_system_status tool with case-insensitive system names."""
    async with Client(facility_server.mcp) as client:
        # Test with Perlmutter in different cases
        raw = await client.call_tool(
            "get_nersc_system_status", {"system_name": "PERLMUTTER"}
        )
        assert "Status for Perlmutter" in raw.data
        assert "🖥️" in raw.data
        assert "Status:" in raw.data


@pytest.mark.asyncio
async def test_get_alcf_status():
    """Test the get_alcf_status tool returns a dictionary with system status."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool("get_alcf_status")
        # Check that it returns a dictionary-like structure
        assert "is_running" in result.data
        assert "motd_info" in result.data
        assert "maintenance_info" in result.data
        assert "job_counts" in result.data
        assert "last_updated" in result.data


@pytest.mark.asyncio
async def test_get_alcf_running_tasks():
    """Test the get_alcf_running_tasks tool with default parameters."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool("get_alcf_running_tasks")
        # Check that it returns the expected structure
        assert "tasks" in result.data
        assert "total" in result.data
        # Verify total is an integer
        assert isinstance(result.data["total"], int)


@pytest.mark.asyncio
async def test_get_alcf_running_tasks_with_pagination():
    """Test the get_alcf_running_tasks tool with custom pagination."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool("get_alcf_running_tasks", {"n": 5, "skip": 0})
        # Check that it returns the expected structure
        assert "tasks" in result.data
        assert "total" in result.data
        # Verify pagination works
        assert len(result.data["tasks"]) <= 5


@pytest.mark.asyncio
async def test_get_alcf_starting_tasks():
    """Test the get_alcf_starting_tasks tool."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool("get_alcf_starting_tasks")
        # Check that it returns the expected structure
        assert "tasks" in result.data
        assert "total" in result.data
        # Verify total is an integer
        assert isinstance(result.data["total"], int)


@pytest.mark.asyncio
async def test_get_alcf_queued_tasks():
    """Test the get_alcf_queued_tasks tool."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool("get_alcf_queued_tasks")
        # Check that it returns the expected structure
        assert "tasks" in result.data
        assert "total" in result.data
        # Verify total is an integer
        assert isinstance(result.data["total"], int)


@pytest.mark.asyncio
async def test_get_alcf_queued_tasks_with_pagination():
    """Test the get_alcf_queued_tasks tool with custom pagination."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool("get_alcf_queued_tasks", {"n": 3, "skip": 5})
        # Check that it returns the expected structure
        assert "tasks" in result.data
        assert "total" in result.data
        # Verify pagination works
        assert len(result.data["tasks"]) <= 3


@pytest.mark.asyncio
async def test_get_alcf_reservation_tasks():
    """Test the get_alcf_reservation_tasks tool."""
    async with Client(facility_server.mcp) as client:
        result = await client.call_tool("get_alcf_reservation_tasks")
        # Check that it returns the expected structure
        assert "tasks" in result.data
        assert "total" in result.data
        # Verify total is an integer
        assert isinstance(result.data["total"], int)
