import logging
from typing import Annotated

import globus_sdk
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from auth import get_globus_app
from schemas import (
    TransferEndpoint,
    TransferEvent,
    TransferFile,
    TransferSubmitResponse,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("Globus Transfer MCP Server")


def get_transfer_client():
    app = get_globus_app()
    return globus_sdk.TransferClient(app=app)


def _format_endpoint_search_response(
    res: globus_sdk.IterableTransferResponse,
) -> list[TransferEndpoint]:
    endpoints = []
    for e in res["DATA"]:
        e: dict
        endpoint = TransferEndpoint(
            endpoint_id=e["id"],
            display_name=e["display_name"],
            owner_id=e["owner_id"],
            owner_string=e["owner_string"],
            type=e["entity_type"],
            description=e.get("description"),
        )
        endpoints.append(endpoint)
    return endpoints


@mcp.tool
def search_endpoints_and_collections(
    search_filter: Annotated[
        str, Field(description="Required string to match endpoint fields against.")
    ],
    limit: Annotated[int, Field(description="Limit the number of results")],
) -> list[TransferEndpoint]:
    """Use a filter string to search all Globus Transfer endpoints and collections that
    are visible to the user.
    """
    tc = get_transfer_client()

    try:
        r = tc.endpoint_search(filter_fulltext=search_filter, limit=limit)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Search failed: {e}")

    return _format_endpoint_search_response(r)


@mcp.tool
def list_my_endpoints_and_collections(
    limit: Annotated[int, Field(description="Limit the number of results")],
) -> list[TransferEndpoint]:
    """List Globus Transfer endpoints and collections for which the user has the
    'administrator' role
    """
    tc = get_transfer_client()

    try:
        r = tc.endpoint_search(filter_scope="administered-by-me", limit=limit)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Search failed: {e}")

    return _format_endpoint_search_response(r)


@mcp.tool
def list_endpoints_and_collections_shared_with_me(
    limit: Annotated[int, Field(description="Limit the number of results")],
) -> list[TransferEndpoint]:
    """List shared Globus Transfer endpoints with permissions that give the user access."""
    tc = get_transfer_client()

    try:
        r = tc.endpoint_search(filter_scope="shared-with-me", limit=limit)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Search failed: {e}")

    return _format_endpoint_search_response(r)


@mcp.tool
def submit_transfer_task(
    source_collection_id: Annotated[
        str, Field(description="ID of the source collection")
    ],
    destination_collection_id: Annotated[
        str, Field(description="ID of the destination collection")
    ],
    source_path: Annotated[
        str, Field(description="Path to the source directory or file of the transfer")
    ],
    destination_path: Annotated[
        str,
        Field(description="Path to the destination directory or file of the transfer"),
    ],
    label: Annotated[
        str, Field(default="MCP Transfer", description="Label for the transfer task")
    ],
) -> TransferSubmitResponse:
    """Submit a transfer task between two Globus Transfer collections.

    Use get_task_events to monitor the task's progress.
    """
    tc = get_transfer_client()

    data = globus_sdk.TransferData(
        source_endpoint=source_collection_id,
        destination_endpoint=destination_collection_id,
        label=label,
    )
    data.add_item(source_path=source_path, destination_path=destination_path)

    try:
        r = tc.submit_transfer(data)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to submit transfer: {e}")

    return TransferSubmitResponse(task_id=r.data["task_id"])


@mcp.tool
def get_task_events(
    task_id: Annotated[str, Field(description="ID of the task")],
    limit: Annotated[int, Field(description="Limit the number of results")],
) -> list[TransferEvent]:
    """Get a list of task events to monitor the status and progress of a task.
    The events are ordered by time descending (newest first).
    """
    tc = get_transfer_client()

    try:
        r = tc.task_event_list(task_id=task_id, limit=limit)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to get task events: {e}")

    events = []
    for e in r["DATA"]:
        event = TransferEvent(
            code=e["code"],
            is_error=e["is_error"],
            description=e["description"],
            details=e["details"],
            time=e["time"],
        )
        events.append(event)

    return events


@mcp.tool
def list_directory(
    collection_id: Annotated[str, Field(description="ID of the collection")],
    path: Annotated[str, Field(description="Path to a directory")],
    limit: Annotated[int, Field(description="Limit the number of results")],
) -> list[TransferFile]:
    """List contents of a directory on a Globus Transfer collection"""
    tc = get_transfer_client()

    try:
        r = tc.operation_ls(collection_id, path=path, limit=limit)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to list directory contents: {e}")

    files = []
    for f in r["DATA"]:
        f: dict
        file = TransferFile(
            name=f["name"],
            type=f["type"],
            link_target=f.get("link_target"),
            user=f.get("user"),
            group=f.get("group"),
            permissions=f["permissions"],
            size=f["size"],
            last_modified=f["last_modified"],
        )
        files.append(file)

    return files


if __name__ == "__main__":
    mcp.run(transport="stdio")
