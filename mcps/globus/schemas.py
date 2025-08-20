from typing import Dict
from pydantic import BaseModel, ConfigDict, Field, JsonValue


###
# Compute
###


class ComputeEndpoint(BaseModel):
    endpoint_id: str = Field(description="ID of the endpoint")
    name: str = Field(description="The endpoint name")
    display_name: str = Field(description="Friendly name for the endpoint")
    owner_id: str = Field(description="ID of the endpoint owner")


class ComputeFunctionRegisterResponse(BaseModel):
    function_id: str = Field(description="ID of the registered function")


class ComputeSubmitResponse(BaseModel):
    task_id: str = Field(description="ID of the task")


class ComputeTask(BaseModel):
    model_config = ConfigDict()

    task_id: str = Field(description="ID of the task")
    status: str = Field(description="The status of the task.")
    result: JsonValue = Field(
        description="When the task status is 'success', this will contain the task result.",
    )
    exception: str | None = Field(
        default=None,
        description=(
            "When the task status is 'failed', this will contain the exception traceback."
        ),
    )


###
# Transfer
###


class TransferEndpoint(BaseModel):
    endpoint_id: str = Field(description="ID if the endpoint")
    display_name: str = Field(description="Friendly name for the endpoint")
    owner_id: str = Field(description="ID of the endpoint owner")
    owner_string: str = Field(description="Identity name of the endpoint owner")
    type: str = Field(description="The type of endpoint")
    description: str | None = Field(
        default=None, description="A description of the endpoint"
    )


class TransferEvent(BaseModel):
    code: str = Field(description="A code indicating the type of the event.")
    is_error: bool = Field(description="true if event is an error event")
    description: str = Field(description="A description of the event.")
    details: str = Field(description="Type specific details about the event.")
    time: str = Field(
        description=(
            "The date and time the event occurred, in ISO 8601 format"
            " (YYYY-MM-DD HH:MM:SS) and UTC."
        )
    )


class TransferSubmitResponse(BaseModel):
    task_id: str = Field(description="ID of the transfer task")


class TransferFile(BaseModel):
    name: str = Field(description="Name of the file")
    type: str = Field(
        description="The type of the entry: dir, file, or invalid_symlink."
    )
    link_target: str | None = Field(
        default=None,
        description=(
            "If this entry is a symlink (valid or invalid), this is the path of its target,"
            " which may be an absolute or relative path. If this entry is not a symlink, this"
            " field is null."
        ),
    )
    user: str | None = Field(
        default=None,
        description="The user owning the file or directory, if applicable.",
    )
    group: str | None = Field(
        default=None,
        description="The group owning the file or directory, if applicable.",
    )
    permissions: str = Field(
        description="The unix permissions, as an octal mode string."
    )
    size: int = Field(description="The file size in bytes.")
    last_modified: str = Field(
        description=(
            "The date and time the file or directory was last modified, in modified ISO 8601"
            " format: YYYY-MM-DD HH:MM:SS+00:00, i.e. using space instead of 'T' to separate"
            " date and time. Always in UTC, indicated explicitly with a trailing '+00:00'"
            " timezone."
        )
    )


###
# Search
###


class SearchIndex(BaseModel):
    index_id: str = Field(description="ID of the search index")
    display_name: str = Field(description="Display name of the index")
    description: str | None = Field(
        default=None, description="Description of the index"
    )
    status: str = Field(description="Status of the index (open, closed, etc.)")
    size: int | None = Field(default=None, description="Size of the index in bytes")
    num_subjects: int | None = Field(
        default=None, description="Number of subjects in the index"
    )
    owner: str | None = Field(default=None, description="ID of the index owner")


class SearchCreateIndexResponse(BaseModel):
    index_id: str = Field(description="ID of the created search index")


class SearchIngestResponse(BaseModel):
    task_id: str = Field(description="ID of the ingestion task")


class SearchEntry(BaseModel):
    model_config = ConfigDict()

    entry_id: str | None = Field(default=None, description="ID of the search entry")
    content: JsonValue = Field(description="Content of the search entry")


class SearchSubject(BaseModel):
    subject: str = Field(description="Subject identifier")
    entries: list[SearchEntry] = Field(description="List of entries for this subject")


class SearchResult(BaseModel):
    gmeta: list[SearchSubject] = Field(description="Search results in GMetaList format")
    total: int = Field(description="Total number of results")
    offset: int = Field(description="Offset of current results")
    limit: int = Field(description="Limit used for current results")


class SearchIngestTask(BaseModel):
    task_id: str = Field(description="ID of the ingestion task")
    status: str = Field(description="Status of the ingestion task")
    message: str | None = Field(
        default=None, description="Message about the task status"
    )


###
# Flows
###


class FlowDefinition(BaseModel):
    model_config = ConfigDict()

    start_at: str = Field(description="Starting state name")
    states: Dict[str, JsonValue] = Field(description="State definitions")
    comment: str | None = Field(default=None, description="Flow description")


class Flow(BaseModel):
    model_config = ConfigDict()

    flow_id: str = Field(description="Flow UUID")
    title: str = Field(description="Flow title")
    definition: JsonValue = Field(description="Flow definition")
    input_schema: JsonValue | None = Field(
        default=None, description="Input schema for the flow"
    )
    subtitle: str | None = Field(default=None, description="Flow subtitle")
    owner_id: str | None = Field(default=None, description="Flow owner ID")
    created_at: str | None = Field(default=None, description="Flow creation timestamp")
    updated_at: str | None = Field(default=None, description="Flow update timestamp")


class FlowCreateResponse(BaseModel):
    flow_id: str = Field(description="ID of the created flow")


class FlowRun(BaseModel):
    model_config = ConfigDict()

    run_id: str = Field(description="Run UUID")
    flow_id: str = Field(description="Associated flow ID")
    status: str = Field(description="Run status (ACTIVE, SUCCEEDED, FAILED, etc.)")
    start_time: str | None = Field(default=None, description="Run start time")
    completion_time: str | None = Field(
        default=None, description="Run completion time"
    )
    details: JsonValue | None = Field(
        default=None, description="Run execution details"
    )


class FlowRunResponse(BaseModel):
    run_id: str = Field(description="ID of the started flow run")


class FlowRunLog(BaseModel):
    model_config = ConfigDict()

    time: str = Field(description="Log entry timestamp")
    task_name: str = Field(description="Name of the task that generated the log")
    message: str = Field(description="Log message")
    level: str | None = Field(default=None, description="Log level")
    details: JsonValue | None = Field(default=None, description="Additional log details")
