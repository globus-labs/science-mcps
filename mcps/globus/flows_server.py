import logging
from typing import Annotated, Any, Callable, Dict

import globus_sdk
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from auth import get_globus_app
from schemas import (
    Flow,
    FlowCreateResponse,
    FlowRun,
    FlowRunResponse,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("Globus Flows MCP Server")


def get_flows_client():
    app = get_globus_app()
    flows_scope = globus_sdk.scopes.FlowsScopes.all
    app.add_scope_requirements({'flows.globus.org': flows_scope})
    return globus_sdk.FlowsClient(app=app)


def handle_gare(
    client_method: Callable[..., globus_sdk.GlobusHTTPResponse],
    *args,
    **kwargs,
) -> globus_sdk.GlobusHTTPResponse:
    client: globus_sdk.FlowsClient = client_method.__self__
    try:
        return client_method(*args, **kwargs)
    except globus_sdk.GlobusAPIError as e:
        if e.http_status == 403 and e.code == "ConsentRequired":
            scopes = e.info.consent_required.required_scopes
            for scope in scopes:
                client.add_app_scope(scope)
            return client_method(*args, **kwargs)
        raise


def _format_flow_response(flow_data: Dict[str, Any]) -> Flow:
    return Flow(
        flow_id=flow_data["id"],
        title=flow_data["title"],
        definition=flow_data["definition"],
        input_schema=flow_data.get("input_schema"),
        subtitle=flow_data.get("subtitle"),
        owner_id=flow_data.get("owner_id") or flow_data.get("principal"),
        created_at=flow_data.get("created_at"),
        updated_at=flow_data.get("updated_at"),
    )


def _format_flow_run_response(run_data: Dict[str, Any]) -> FlowRun:
    return FlowRun(
        run_id=run_data["run_id"],
        flow_id=run_data["flow_id"],
        status=run_data["status"],
        start_time=run_data.get("start_time"),
        completion_time=run_data.get("completion_time"),
        details=run_data.get("details"),
    )


@mcp.tool
def create_flow(
    title: Annotated[str, Field(description="Title for the flow")],
    definition: Annotated[
        Dict[str, Any], Field(description="Flow definition in Globus Flows format")
    ],
    subtitle: Annotated[
        str, Field(description="Optional subtitle for the flow", default="")
    ],
    input_schema: Annotated[
        Dict[str, Any] | None,
        Field(description="Optional input schema for the flow. Defaults to {} (accepts any input)", default=None),
    ],
) -> FlowCreateResponse:
    """Create a new Globus Flow."""
    fc = get_flows_client()

    # Use default empty schema if none provided
    schema = input_schema if input_schema is not None else {}
    
    # Build keyword arguments for optional parameters
    kwargs = {}
    if subtitle:
        kwargs["subtitle"] = subtitle

    try:
        r = handle_gare(fc.create_flow, title, definition, schema, **kwargs)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to create flow: {e}")

    return FlowCreateResponse(flow_id=r.data["id"])


@mcp.tool
def list_flows(
    limit: Annotated[int, Field(description="Maximum number of flows to return", default=25)],
) -> list[Flow]:
    """List flows that the user has access to."""
    fc = get_flows_client()

    try:
        r = handle_gare(fc.list_flows)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to list flows: {e}")

    flows = []
    count = 0
    for flow_data in r:
        if count >= limit:
            break
        flows.append(_format_flow_response(flow_data))
        count += 1

    return flows


@mcp.tool
def get_flow(
    flow_id: Annotated[str, Field(description="ID of the flow to retrieve")],
) -> Flow:
    """Get detailed information about a specific flow."""
    fc = get_flows_client()

    try:
        r = handle_gare(fc.get_flow, flow_id)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to get flow: {e}")

    return _format_flow_response(r.data)


@mcp.tool
def update_flow(
    flow_id: Annotated[str, Field(description="ID of the flow to update")],
    title: Annotated[str | None, Field(description="New title for the flow", default=None)],
    subtitle: Annotated[str | None, Field(description="New subtitle for the flow", default=None)],
    definition: Annotated[
        Dict[str, Any] | None, Field(description="New flow definition", default=None)
    ],
    input_schema: Annotated[
        Dict[str, Any] | None, Field(description="New input schema", default=None)
    ],
) -> Flow:
    """Update an existing flow."""
    fc = get_flows_client()

    update_data = {}
    if title is not None:
        update_data["title"] = title
    if subtitle is not None:
        update_data["subtitle"] = subtitle
    if definition is not None:
        update_data["definition"] = definition
    if input_schema is not None:
        update_data["input_schema"] = input_schema

    if not update_data:
        raise ToolError("At least one field must be provided for update")

    try:
        r = handle_gare(fc.update_flow, flow_id, **update_data)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to update flow: {e}")

    return _format_flow_response(r.data)


@mcp.tool
def delete_flow(
    flow_id: Annotated[str, Field(description="ID of the flow to delete")],
) -> Dict[str, str]:
    """Delete a flow. Only the flow owner can delete a flow."""
    fc = get_flows_client()

    try:
        handle_gare(fc.delete_flow, flow_id)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to delete flow: {e}")

    return {"message": f"Flow {flow_id} deleted successfully"}


@mcp.tool
def run_flow(
    flow_id: Annotated[str, Field(description="ID of the flow to run")],
    flow_input: Annotated[
        Dict[str, Any], Field(description="Input data for the flow execution")
    ],
    run_label: Annotated[
        str, Field(description="Optional label for the flow run", default="")
    ],
) -> FlowRunResponse:
    """Start a flow run with the provided input data."""
    app = get_globus_app()
    
    # For running flows, we need flow-specific scopes
    flow_scope = f"https://auth.globus.org/scopes/{flow_id}/flow_{flow_id}_user"
    app.add_scope_requirements({flow_id: flow_scope})
    
    specific_client = globus_sdk.SpecificFlowClient(flow_id, app=app)

    run_data = {"body": flow_input}
    if run_label:
        run_data["label"] = run_label

    try:
        r = handle_gare(specific_client.run_flow, **run_data)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to start flow run: {e}")

    return FlowRunResponse(run_id=r.data["run_id"])


@mcp.tool
def validate_flow(
    definition: Annotated[
        Dict[str, Any], Field(description="Flow definition to validate")
    ],
    input_schema: Annotated[
        Dict[str, Any] | None,
        Field(description="Optional input schema to validate", default=None),
    ],
) -> Dict[str, Any]:
    """Validate a flow definition without creating the flow."""
    fc = get_flows_client()

    validation_data = {"definition": definition}
    if input_schema is not None:
        validation_data["input_schema"] = input_schema

    try:
        # Note: This uses a direct API call as there might not be a specific SDK method
        r = fc.post("/flows/validate", data=validation_data)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Flow validation failed: {e}")

    return r.data


@mcp.tool
def list_flow_runs(
    flow_id: Annotated[str | None, Field(description="Filter by specific flow ID", default=None)],
    limit: Annotated[int, Field(description="Maximum number of runs to return", default=25)],
    status: Annotated[
        str | None, Field(description="Filter by run status (ACTIVE, SUCCEEDED, FAILED, etc.)", default=None)
    ],
) -> list[FlowRun]:
    """List flow runs, optionally filtered by flow ID or status."""
    fc = get_flows_client()

    # Build keyword arguments for the API call
    kwargs = {}
    if flow_id:
        kwargs["filter_flow_id"] = flow_id
    # Note: status filtering might need to be handled differently in the API

    try:
        r = handle_gare(fc.list_runs, **kwargs)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to list flow runs: {e}")

    runs = []
    count = 0
    for run_data in r:
        if count >= limit:
            break
        # Apply status filter locally if provided
        if status and run_data.get("status") != status:
            continue
        runs.append(_format_flow_run_response(run_data))
        count += 1

    return runs


@mcp.tool
def get_flow_run(
    run_id: Annotated[str, Field(description="ID of the flow run to retrieve")],
) -> FlowRun:
    """Get detailed information about a specific flow run."""
    fc = get_flows_client()

    try:
        r = handle_gare(fc.get_run, run_id)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to get flow run: {e}")

    return _format_flow_run_response(r.data)


@mcp.tool
def cancel_flow_run(
    run_id: Annotated[str, Field(description="ID of the flow run to cancel")],
) -> Dict[str, str]:
    """Cancel an active flow run."""
    fc = get_flows_client()

    try:
        handle_gare(fc.cancel_run, run_id)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to cancel flow run: {e}")

    return {"message": f"Flow run {run_id} canceled successfully"}


@mcp.tool
def get_flow_run_logs(
    run_id: Annotated[str, Field(description="ID of the flow run")],
    limit: Annotated[int, Field(description="Maximum number of log entries to return", default=100)],
) -> Dict[str, Any]:
    """Get execution logs for a flow run."""
    fc = get_flows_client()

    try:
        r = handle_gare(fc.get_run_logs, run_id, limit=limit)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to get flow run logs: {e}")

    return r.data


if __name__ == "__main__":
    mcp.run(transport="stdio")