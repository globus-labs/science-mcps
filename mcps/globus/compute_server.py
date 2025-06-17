"""FastMCP server exposing Globus Compute functionality via Globus Compute SDK."""

import logging
import os
from typing import Any, Dict, Optional, Tuple

import globus_compute_sdk
import globus_sdk
from fastmcp import FastMCP
from globus_compute_sdk.sdk.login_manager import AuthorizerLoginManager
from globus_compute_sdk.sdk.login_manager.manager import ComputeScopeBuilder
from globus_sdk.scopes import AuthScopes

logger = logging.getLogger(__name__)
CLIENT_ID = os.getenv("GLOBUS_CLIENT_ID", "ee05bbfa-2a1a-4659-95df-ed8946e3aae6")

mcp = FastMCP("Globus Transfer Bridge")

# Global variables
compute_client: Optional[globus_compute_sdk.Client] = None
auth_client: Optional[globus_sdk.NativeAppAuthClient] = None
registered_functions: Dict[str, str] = {}


@mcp.tool
async def compute_authenticate() -> str:
    """Authenticate with Globus Compute"""
    global auth_client

    if CLIENT_ID == "YOUR_GLOBUS_CLIENT_ID":
        return "Please set GLOBUS_CLIENT_ID environment variable"

    try:
        auth_client = globus_sdk.NativeAppAuthClient(CLIENT_ID)
        auth_client.oauth2_start_flow(
            requested_scopes=[
                "https://auth.globus.org/scopes/facd7ccc-c5f4-42aa-916b-a0e270e2c2a9/all",
                "openid",
                "email",
                "profile",
            ]
        )

        authorize_url = auth_client.oauth2_get_authorize_url()

        return f"""Please visit this URL to authorize:

{authorize_url}

After authorization, use complete_compute_auth with the code."""

    except Exception as e:
        return f"Authentication failed: {str(e)}"


@mcp.tool
async def complete_compute_auth(auth_code: str) -> str:
    """Complete authentication"""
    global auth_client, compute_client

    if not auth_client:
        return "Please call compute_authenticate first"

    try:
        token_response = auth_client.oauth2_exchange_code_for_tokens(auth_code)

        ComputeScopes = ComputeScopeBuilder()

        compute_auth = globus_sdk.AccessTokenAuthorizer(
            token_response.by_resource_server["funcx_service"]["access_token"]
        )
        openid_auth = globus_sdk.AccessTokenAuthorizer(
            token_response.by_resource_server["auth.globus.org"]["access_token"]
        )

        compute_login_manager = AuthorizerLoginManager(
            authorizers={
                ComputeScopes.resource_server: compute_auth,
                AuthScopes.resource_server: openid_auth,
                "openid": openid_auth,
            }
        )
        compute_login_manager.ensure_logged_in()
        compute_client = globus_compute_sdk.Client(login_manager=compute_login_manager)

        return "Authentication completed successfully!"

    except Exception as e:
        return f"Authentication failed: {str(e)}"


@mcp.tool
async def register_function(
    function_code: str, function_name: str, description: str = ""
) -> str:
    """Register a function"""
    global registered_functions

    if not compute_client:
        return "Not authenticated. Please authenticate first."

    try:
        exec_globals: Dict[str, Any] = {}
        exec(function_code, exec_globals)

        functions = {
            k: v
            for k, v in exec_globals.items()
            if callable(v) and not k.startswith("_")
        }

        if not functions:
            return "No functions found in code"

        if len(functions) > 1:
            return f"Multiple functions found: {list(functions.keys())}. Use only one function."

        func_obj = list(functions.values())[0]
        func_uuid = compute_client.register_function(func_obj)
        registered_functions[function_name] = func_uuid

        return f"""Function registered successfully!

Name: {function_name}
UUID: {func_uuid}
Description: {description}

Code:
{function_code}"""

    except Exception as e:
        return f"Registration failed: {str(e)}"


@mcp.tool
async def execute_function(
    function_name: str,
    endpoint_id: str,
    function_args: Tuple[Any, ...],
    function_kwargs: Dict[str, Any],
) -> str:
    """Execute a function"""
    if not compute_client:
        return "Not authenticated"

    if function_name not in registered_functions:
        return f"Function not found. Available: {list(registered_functions.keys())}"

    try:
        func_uuid = registered_functions[function_name]

        task_id = compute_client.run(
            *function_args,
            function_id=func_uuid,
            endpoint_id=endpoint_id,
            **function_kwargs,
        )

        return f"""Function execution submitted!

Function: {function_name}
Endpoint: {endpoint_id}
Task ID: {task_id}
Arguments: {function_args}
Kwargs: {function_kwargs}

Use check_task_status to monitor progress."""

    except Exception as e:
        return f"Execution failed: {str(e)}"


@mcp.tool
async def check_task_status(task_id: str) -> str:
    """Check task status"""
    if not compute_client:
        return "Not authenticated"

    try:
        status = compute_client.get_task(task_id)

        return f"""Task Status:

Task ID: {task_id}
Status: {status}

Use get_task_result when status is 'success'."""

    except Exception as e:
        return f"Status check failed: {str(e)}"


@mcp.tool
async def get_task_result(task_id: str) -> str:
    """Get task result"""
    if not compute_client:
        return "Not authenticated"

    try:
        result = compute_client.get_result(task_id)

        return f"""Task Result:

Task ID: {task_id}
Result: {str(result)}
Type: {type(result).__name__}"""

    except Exception as e:
        return f"Failed to get result: {str(e)}"


@mcp.tool
async def list_registered_functions() -> str:
    """List registered functions"""
    if not registered_functions:
        return "No functions registered"

    result = "Registered Functions:\n\n"
    for name, uuid in registered_functions.items():
        result += f"{name}: {uuid}\n"

    return result


@mcp.tool
async def create_hello_world() -> str:
    """Create hello world function"""
    function_code = """def hello_compute(name="World"):
    import platform
    import os

    hostname = platform.node()
    username = os.getenv('USER', 'unknown')

    return f"Hello {name}! Running on {hostname} as {username}" """

    return await register_function(
        function_code.strip(), "hello_world", "Test function that returns system info"
    )


# Entrypoint
if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        path="/mcps/globus-compute",
    )
