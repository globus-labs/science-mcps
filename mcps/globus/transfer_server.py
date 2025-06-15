"""FastMCP server exposing Globus Transfer functionality via Globus SDK."""

import logging
import os
from typing import Optional

import globus_sdk
from fastmcp import FastMCP

logger = logging.getLogger(__name__)
CLIENT_ID = os.getenv("GLOBUS_CLIENT_ID", "ee05bbfa-2a1a-4659-95df-ed8946e3aae6")

mcp = FastMCP("Globus Transfer Bridge")


# Globals – initialised lazily after auth
transfer_client: Optional[globus_sdk.TransferClient] = None
auth_client: Optional[globus_sdk.NativeAppAuthClient] = None


@mcp.tool
async def globus_authenticate() -> str:
    """Authenticate with Globus and get authorization URL."""
    global auth_client

    if not CLIENT_ID.lower():
        return "❌ Please set the GLOBUS_CLIENT_ID environment variable."

    try:
        auth_client = globus_sdk.NativeAppAuthClient(CLIENT_ID)
        auth_client.oauth2_start_flow(
            requested_scopes=["urn:globus:auth:scope:transfer.api.globus.org:all"]
        )
        authorize_url = auth_client.oauth2_get_authorize_url()
        return (
            "🔗 **Authorization URL**\n\n"
            "Visit the link, approve access, then call `complete_globus_auth(<code>)` with the returned code.\n\n "
            f"{authorize_url}"
        )

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return f"❌ Authentication failed: {str(e)}"


@mcp.tool
async def complete_globus_auth(auth_code: str) -> str:
    """Complete Globus authentication with the authorization code"""
    global auth_client, transfer_client
    if not auth_client:
        return "❌ Please call globus_authenticate first to start the auth flow."

    try:
        token_response = auth_client.oauth2_exchange_code_for_tokens(auth_code.strip())
        transfer_token = token_response.by_resource_server["transfer.api.globus.org"][
            "access_token"
        ]
        authorizer = globus_sdk.AccessTokenAuthorizer(transfer_token)
        transfer_client = globus_sdk.TransferClient(authorizer=authorizer)

        return "✅ **Authentication completed successfully!** You can now use all Globus transfer functions."
    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        return f"❌ Authentication completion failed: {str(e)}"


@mcp.tool
async def list_endpoints(filter_name: str = "") -> str:
    """List available Globus endpoints"""
    if not transfer_client:
        return "❌ Not authenticated. Please run globus_authenticate first."

    try:
        # Get endpoints
        search_filter = filter_name if filter_name else None
        endpoints = transfer_client.endpoint_search(filter_fulltext=search_filter)

        if not endpoints.data:
            return "No endpoints found matching your criteria."

        result = "📡 **Available Endpoints:**\n\n"
        for ep in endpoints.data["DATA"][:10]:  # Limit to first 10 results
            result += f"**{ep['display_name']}**\n"
            result += f"   📋 ID: `{ep['id']}`\n"
            result += f"   👤 Owner: {ep['owner_string']}\n"
            result += f"   📝 Description: {ep.get('description', 'N/A')}\n"
            result += f"   🔌 Type: {ep.get('entity_type', 'Unknown')}\n"
            result += "-" * 60 + "\n"

        if len(endpoints.data["DATA"]) > 10:
            result += f"\n... and {len(endpoints.data['DATA']) - 10} more endpoints. Use filter_name to narrow results."

        return result

    except Exception as e:
        logger.error(f"Error listing endpoints: {e}")
        return f"❌ Failed to list endpoints: {str(e)}"


@mcp.tool
async def submit_transfer(
    source_endpoint: str,
    dest_endpoint: str,
    source_path: str,
    dest_path: str,
    label: str = "MCP Transfer",
) -> str:
    """Submit a transfer job between two Globus endpoints"""
    if not transfer_client:
        return "❌ Not authenticated. Please run globus_authenticate first."

    try:
        # Create transfer data
        transfer_data = globus_sdk.TransferData(
            source_endpoint=source_endpoint,
            destination_endpoint=dest_endpoint,
            label=label,
        )

        # Add transfer item
        transfer_data.add_item(source_path=source_path, destination_path=dest_path)

        # Submit the transfer
        result = transfer_client.submit_transfer(transfer_data)

        return f"""
🚀 **Transfer Submitted Successfully!**

📋 **Task ID:** `{result["task_id"]}`
📊 **Status:** {result["message"]}
🏷️ **Label:** {label}
📁 **Source:** `{source_path}` on `{source_endpoint}`
📁 **Destination:** `{dest_path}` on `{dest_endpoint}`

Use check_transfer_status with the Task ID to monitor progress.
        """.strip()

    except Exception as e:
        logger.error(f"Transfer submission error: {e}")
        return f"❌ Transfer submission failed: {str(e)}"


@mcp.tool
async def check_transfer_status(task_id: str) -> str:
    """Check the status of a Globus transfer job"""
    if not transfer_client:
        return "❌ Not authenticated. Please run globus_authenticate first."

    try:
        # Get task status
        task = transfer_client.get_task(task_id)

        # Format status with emoji
        status_emoji = {
            "ACTIVE": "🔄",
            "SUCCEEDED": "✅",
            "FAILED": "❌",
            "INACTIVE": "⏸️",
        }.get(task["status"], "❓")

        result = f"""
{status_emoji} **Transfer Status Report**

📋 **Task ID:** `{task["task_id"]}`
📊 **Status:** {task["status"]}
🏷️ **Label:** {task["label"]}
📁 **Files Transferred:** {task.get("files_transferred", 0)}
📊 **Bytes Transferred:** {task.get("bytes_transferred", 0):,} bytes
🎯 **Source:** {task.get("source_endpoint_display_name", "Unknown")}
🎯 **Destination:** {task.get("destination_endpoint_display_name", "Unknown")}
⏰ **Submitted:** {task.get("request_time", "N/A")}
⏰ **Completed:** {task.get("completion_time", "In Progress" if task["status"] == "ACTIVE" else "N/A")}
        """.strip()

        if task["status"] == "FAILED":
            result += f"\n\n❌ **Error Details:** {task.get('nice_status_details', 'Unknown error')}"
        elif task["status"] == "ACTIVE":
            result += (
                "\n\n🔄 **Progress:** Transfer is currently active and processing..."
            )

        return result

    except Exception as e:
        logger.error(f"Status check error: {e}")
        return f"❌ Failed to check transfer status: {str(e)}"


@mcp.tool
async def list_directory(endpoint_id: str, path: str = "/") -> str:
    """List contents of a directory on a Globus endpoint"""
    if not transfer_client:
        return "❌ Not authenticated. Please run globus_authenticate first."

    try:
        # List directory contents
        response = transfer_client.operation_ls(endpoint_id, path=path)

        if not response.data:
            return f"📁 Directory `{path}` is empty or inaccessible."

        result = f"📁 **Directory listing for `{path}`**\n"
        result += f"🎯 **Endpoint:** `{endpoint_id}`\n\n"

        # Sort: directories first, then files
        items = sorted(
            response.data["DATA"], key=lambda x: (x["type"] != "dir", x["name"].lower())
        )

        for item in items[:50]:  # Limit to 50 items
            icon = "📁" if item["type"] == "dir" else "📄"
            size = f" ({item['size']:,} bytes)" if item.get("size") else ""
            modified = (
                f" - {item['last_modified']}" if item.get("last_modified") else ""
            )
            result += f"{icon} `{item['name']}`{size}{modified}\n"

        if len(response.data["DATA"]) > 50:
            result += f"\n... and {len(response.data['DATA']) - 50} more items."

        return result

    except Exception as e:
        logger.error(f"Directory listing error: {e}")
        return f"❌ Failed to list directory: {str(e)}"


# Entrypoint
if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        path="/mcps/globus-transfer",
    )
