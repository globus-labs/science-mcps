from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

###
# NERSC
###


class NERSCSystem(BaseModel):
    name: str = Field(description="System identifier name")
    full_name: str = Field(description="Full display name of the system")
    description: str = Field(description="Description of the system status")
    system_type: str = Field(
        description="Type of system (compute, filesystem, service, storage)"
    )
    notes: list[str] = Field(description="Additional notes about the system")
    status: str = Field(description="Current status of the system")
    updated_at: str = Field(description="Timestamp of last status update")


class NERSCApiResponse(BaseModel):
    systems: list[NERSCSystem] = Field(
        description="List of all NERSC systems and their status"
    )


###
# ALCF
###


class ALCFJob(BaseModel):
    model_config = ConfigDict(extra="allow")
    jobid: Optional[str] = Field(default=None, description="Job identifier")
    project: Optional[str] = Field(default=None, description="Project name")
    queue: Optional[str] = Field(default=None, description="Queue name")
    starttime: Optional[str] = Field(default=None, description="Job start time")


class ALCFMOTD(BaseModel):
    display_end: str = Field(description="Display end time")
    display_start: str = Field(description="Display start time")
    message: str = Field(description="Message content")
    resource: str = Field(description="Resource name")
    type: str = Field(description="Message type")


class ALCFApiResponse(BaseModel):
    # Maintenance fields
    maint: Optional[bool] = Field(default=None, description="System in maintenance")
    start: Optional[int] = Field(
        default=None, description="Maintenance start timestamp"
    )
    end: Optional[int] = Field(default=None, description="Maintenance end timestamp")

    # Job queue fields
    running: list[ALCFJob] = Field(default_factory=list, description="Running jobs")
    starting: list[ALCFJob] = Field(default_factory=list, description="Starting jobs")
    queued: list[ALCFJob] = Field(default_factory=list, description="Queued jobs")
    reservation: list[ALCFJob] = Field(default_factory=list, description="Reservations")

    # MOTD info
    motd_info: list[ALCFMOTD] = Field(
        default_factory=list, description="Messages of the day"
    )

    # updated timestamp
    updated: Optional[int] = Field(default=None, description="Last update timestamp")


# Summarized status returned by get_alcf_status tool
class MaintenanceInfo(BaseModel):
    start: Optional[int] = Field(
        default=None, description="Maintenance start timestamp"
    )
    end: Optional[int] = Field(default=None, description="Maintenance end timestamp")


class JobCounts(BaseModel):
    running: int = Field(description="Count of running jobs")
    starting: int = Field(description="Count of starting jobs")
    queued: int = Field(description="Count of queued jobs")
    reservation: int = Field(description="Count of reservation jobs")


class ALCFStatusResponse(BaseModel):
    is_operational: bool = Field(description="Whether the system is operational")
    motd_info: Optional[list[ALCFMOTD]] = Field(
        default=None, description="Messages of the day"
    )
    maintenance_info: MaintenanceInfo = Field(description="Maintenance window info")
    job_counts: JobCounts = Field(description="Aggregated job counts by state")
    last_updated: Optional[int] = Field(
        default=None, description="Last update timestamp"
    )


# Paginated tasks returned by get_alcf_tasks tool
class ALCFJobsResponse(BaseModel):
    total: int = Field(description="Total number of tasks in this queue")
    tasks: list[ALCFJob] = Field(description="Page of tasks with common fields")
