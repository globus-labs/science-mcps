import logging
import platform

from pydantic import Field
from typing import Annotated, Any, Dict, Tuple

import globus_sdk
import globus_compute_sdk
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from globus_compute_sdk import Client
from globus_compute_sdk.serialize import (
    ComputeSerializer,
    PureSourceTextInspect,
    JSONData,
)
from globus_compute_sdk.serialize.facade import validate_strategylike

from auth import get_authorizer
from schemas import (
    ComputeFunctionRegisterResponse,
    ComputeSubmitResponse,
    ComputeTask,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("Globus Compute MCP Server")


def get_compute_client():
    scopes = globus_sdk.ComputeClient.scopes.all
    authorizer = get_authorizer(scopes)
    serializer = ComputeSerializer(
        # Ensure no dill deserialization on the server
        allowed_deserializer_types=[JSONData, PureSourceTextInspect],
    )
    return Client(authorizer=authorizer, serializer=serializer, do_version_check=False)


@mcp.tool
def register_function(
    function_code: Annotated[
        str, Field(description="The text of the function source code")
    ],
    function_name: Annotated[str, Field(description="The name of the function")],
    description: Annotated[
        str, Field(default="", description="An optional description of the function")
    ],
    public: Annotated[
        bool,
        Field(
            description="Indicates whether the function can be used by others",
            default=False,
        ),
    ],
) -> ComputeFunctionRegisterResponse:
    """Register a Python function with Globus Compute.

    Use submit_task to run the registered function on an endpoint.
    """
    gcc = get_compute_client()

    # Simulate PureSourceTextInspect strategy
    serde_iden = "st"
    serialized = f"{serde_iden}\n{function_name}:{function_code}"
    packed = ComputeSerializer.pack_buffers([serialized])

    data = {
        "function_name": function_name,
        "function_code": packed,
        "description": description,
        "meta": {
            "python_version": platform.python_version(),
            "sdk_version": globus_compute_sdk.__version__,
            "serde_identifier": serde_iden,
        },
        "public": public,
    }

    try:
        r = gcc._compute_web_client.v3.register_function(data)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Function registration failed: {e}")

    return ComputeFunctionRegisterResponse(function_id=r.data["function_uuid"])


@mcp.tool
def submit_task(
    endpoint_id: Annotated[
        str, Field(description="ID of the endpoint that will execute the function")
    ],
    function_id: Annotated[str, Field(description="ID of the function")],
    function_args: Annotated[
        Tuple[Any, ...], Field(description="Positional arguments for the function")
    ],
    function_kwargs: Annotated[
        Dict[str, Any], Field(description="Keyword arguments for the function")
    ],
) -> ComputeSubmitResponse:
    """Submit a function execution task to a Globus Compute endpoint.

    Use get_task_status to monitor progress and retrieve results.
    """
    gcc = get_compute_client()

    batch = gcc.create_batch(
        result_serializers=[validate_strategylike(JSONData).import_path]
    )
    batch.add(function_id, function_args, function_kwargs)

    try:
        r = gcc.batch_run(endpoint_id, batch)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Execution failed: {e}")

    task_id = r["tasks"][function_id][0]
    return ComputeSubmitResponse(task_id=task_id)


@mcp.tool
def get_task_status(
    task_id: Annotated[str, Field(description="The ID of the task")],
) -> ComputeTask:
    """Retrieve the status and result of a Globus Compute task."""
    gcc = get_compute_client()

    try:
        r = gcc._compute_web_client.v2.get_task(task_id)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to retrieve task result: {e}")

    result = r.get("result")
    if result:
        try:
            result = gcc.fx_serializer.deserialize(result)
        except Exception:
            raise ToolError("Unable to deserialize result")

    return ComputeTask(
        task_id=r.data["task_id"],
        status=r.data["status"],
        result=result,
        exception=r.get("exception"),
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
