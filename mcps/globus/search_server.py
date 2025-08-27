import logging
from typing import Annotated, Any, Callable, Dict

import globus_sdk
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from auth import get_globus_app
from schemas import (
    SearchCreateIndexResponse,
    SearchIndex,
    SearchIngestResponse,
    SearchIngestTask,
    SearchResult,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("Globus Search MCP Server")


def get_search_client():
    app = get_globus_app()
    scopes = globus_sdk.scopes.SearchScopes
    return globus_sdk.SearchClient(app=app, app_scopes=scopes.all)


def _format_search_response(res: globus_sdk.GlobusHTTPResponse) -> SearchResult:
    data = res.data
    return SearchResult(
        gmeta=data.get("gmeta", []),
        total=data.get("total", 0),
        offset=data.get("offset", 0),
        limit=data.get("limit", 10),
    )


def _format_index_list_response(
    res: globus_sdk.GlobusHTTPResponse,
) -> list[SearchIndex]:
    indices = []
    for idx_data in res.data.get("index_list", []):
        index = SearchIndex(
            index_id=idx_data["id"],
            display_name=idx_data["display_name"],
            description=idx_data.get("description"),
            status=idx_data["status"],
            size=idx_data.get("size"),
            num_subjects=idx_data.get("num_subjects"),
            owner=idx_data.get("owner") or idx_data.get("owner_id"),
        )
        indices.append(index)
    return indices


@mcp.tool
def create_index(
    display_name: Annotated[str, Field(description="Display name for the search index")],
    description: Annotated[
        str, Field(description="Description of the search index", default="")
    ],
) -> SearchCreateIndexResponse:
    """Create a new Globus Search index."""
    sc = get_search_client()

    data = {"display_name": display_name}
    if description:
        data["description"] = description

    try:
        r = handle_gare(sc.create_index, data)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to create index: {e}")

    return SearchCreateIndexResponse(index_id=r.data["id"])


@mcp.tool
def list_my_indices() -> list[SearchIndex]:
    """List Globus Search indices that the user has access to."""
    sc = get_search_client()

    try:
        r = sc.index_list()
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to list indices: {e}")

    return _format_index_list_response(r)


@mcp.tool
def get_index_info(
    index_id: Annotated[str, Field(description="ID of the search index")],
) -> SearchIndex:
    """Get detailed information about a specific Globus Search index."""
    sc = get_search_client()

    try:
        r = sc.get_index(index_id)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to get index info: {e}")

    idx_data = r.data
    return SearchIndex(
        index_id=idx_data["id"],
        display_name=idx_data["display_name"],
        description=idx_data.get("description"),
        status=idx_data["status"],
        size=idx_data.get("size"),
        num_subjects=idx_data.get("num_subjects"),
        owner=idx_data.get("owner") or idx_data.get("owner_id"),
    )


@mcp.tool
def delete_index(
    index_id: Annotated[str, Field(description="ID of the search index to delete")],
) -> Dict[str, str]:
    """Delete a Globus Search index. Only the index owner can delete an index."""
    sc = get_search_client()

    try:
        sc.delete_index(index_id)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to delete index: {e}")

    return {"message": f"Index {index_id} deleted successfully"}


@mcp.tool
def ingest_document(
    index_id: Annotated[str, Field(description="ID of the search index")],
    subject: Annotated[str, Field(description="Unique subject identifier for the document")],
    content: Annotated[Dict[str, Any], Field(description="Document content as a JSON object")],
    visible_to: Annotated[
        list[str], 
        Field(description="List of principals who can see this document", default=["public"])
    ],
) -> SearchIngestResponse:
    """Ingest a single document into a Globus Search index."""
    sc = get_search_client()

    gmeta_doc = {
        "ingest_type": "GMetaEntry",
        "ingest_data": {
            "subject": subject,
            "visible_to": visible_to,
            "content": content,
        }
    }

    try:
        r = sc.ingest(index_id, gmeta_doc)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to ingest document: {e}")

    return SearchIngestResponse(task_id=r.data["task_id"])


@mcp.tool
def ingest_documents(
    index_id: Annotated[str, Field(description="ID of the search index")],
    documents: Annotated[
        list[Dict[str, Any]], 
        Field(description="List of documents to ingest. Each document must have 'subject', 'content', and optionally 'visible_to' fields")
    ],
) -> SearchIngestResponse:
    """Ingest multiple documents into a Globus Search index."""
    sc = get_search_client()

    gmeta_docs = []
    for doc in documents:
        if "subject" not in doc or "content" not in doc:
            raise ToolError("Each document must have 'subject' and 'content' fields")
        
        visible_to = doc.get("visible_to", ["public"])
        gmeta_doc = {
            "ingest_type": "GMetaEntry",
            "ingest_data": {
                "subject": doc["subject"],
                "visible_to": visible_to,
                "content": doc["content"],
            }
        }
        gmeta_docs.append(gmeta_doc)

    try:
        r = sc.ingest(index_id, gmeta_docs)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to ingest documents: {e}")

    return SearchIngestResponse(task_id=r.data["task_id"])


@mcp.tool
def get_ingestion_status(
    task_id: Annotated[str, Field(description="ID of the ingestion task")],
) -> SearchIngestTask:
    """Get the status of a document ingestion task."""
    sc = get_search_client()

    try:
        r = sc.get_task(task_id)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to get task status: {e}")

    task_data = r.data
    return SearchIngestTask(
        task_id=task_data["task_id"],
        status=task_data["state"],
        message=task_data.get("message"),
    )


@mcp.tool
def delete_subject(
    index_id: Annotated[str, Field(description="ID of the search index")],
    subject: Annotated[str, Field(description="Subject identifier to delete")],
) -> Dict[str, str]:
    """Delete a subject and all its entries from a Globus Search index."""
    sc = get_search_client()

    try:
        sc.delete_subject(index_id, subject)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to delete subject: {e}")

    return {"message": f"Subject '{subject}' deleted from index {index_id}"}


@mcp.tool
def search_index(
    index_id: Annotated[str, Field(description="ID of the search index")],
    query: Annotated[str, Field(description="Search query string")],
    limit: Annotated[int, Field(description="Maximum number of results to return", default=10)],
    offset: Annotated[int, Field(description="Number of results to skip for pagination", default=0)],
) -> SearchResult:
    """Search for documents in a Globus Search index using a simple query string."""
    sc = get_search_client()

    try:
        r = sc.search(index_id, q=query, limit=limit, offset=offset)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Search failed: {e}")

    return _format_search_response(r)


@mcp.tool
def advanced_search(
    index_id: Annotated[str, Field(description="ID of the search index")],
    search_params: Annotated[
        Dict[str, Any], 
        Field(description="Advanced search parameters including query, filters, facets, sorting")
    ],
) -> SearchResult:
    """Perform an advanced search with complex filters, facets, and sorting."""
    sc = get_search_client()

    try:
        r = sc.post_search(index_id, search_params)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Advanced search failed: {e}")

    return _format_search_response(r)


@mcp.tool
def get_subject(
    index_id: Annotated[str, Field(description="ID of the search index")],
    subject: Annotated[str, Field(description="Subject identifier to retrieve")],
) -> Dict[str, Any]:
    """Get detailed information about a specific subject in a Globus Search index."""
    sc = get_search_client()

    try:
        r = sc.get_subject(index_id, subject)
    except globus_sdk.GlobusAPIError as e:
        raise ToolError(f"Failed to get subject: {e}")

    return r.data


if __name__ == "__main__":
    mcp.run(transport="stdio")