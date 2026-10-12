"""Response schemas for the server-side OpenProject integration."""

from pydantic import BaseModel, Field


class OpenProjectStatus(BaseModel):
    configured: bool
    workspace_url: str | None = None
    setup_instructions: str | None = None


class OpenProjectProject(BaseModel):
    id: int
    name: str
    description: str = ""
    url: str


class OpenProjectWorkPackage(BaseModel):
    id: int
    subject: str
    status: str = "Unknown"
    priority: str | None = None
    assignee: str | None = None
    start_date: str | None = None
    due_date: str | None = None
    description: str = ""
    url: str


class OpenProjectOverview(BaseModel):
    configured: bool
    workspace_url: str | None = None
    setup_instructions: str | None = None
    project: OpenProjectProject | None = None
    work_packages: list[OpenProjectWorkPackage] = Field(default_factory=list)
    total_count: int = 0