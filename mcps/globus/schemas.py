from pydantic import BaseModel, Field


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
