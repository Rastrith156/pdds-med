"""OpenProject REST API client; credentials and upstream payloads stay server-side."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import Settings
from app.schemas.openproject import (
    OpenProjectOverview,
    OpenProjectProject,
    OpenProjectStatus,
    OpenProjectWorkPackage,
)

SETUP_INSTRUCTIONS = (
    "Set OPENPROJECT_URL, OPENPROJECT_API_KEY, and OPENPROJECT_PROJECT_ID "
    "in the backend environment, then restart the API."
)
_UNAVAILABLE = "OpenProject could not be reached. Check the server configuration and try again."


class OpenProjectUnavailable(Exception):
    """The upstream OpenProject instance returned an unusable response."""


class OpenProjectService:
    """Fetch one configured project's details and work packages from API v3."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport

    def status(self) -> OpenProjectStatus:
        if not self.settings.openproject_configured:
            return OpenProjectStatus(
                configured=False,
                setup_instructions=SETUP_INSTRUCTIONS,
            )
        return OpenProjectStatus(
            configured=True,
            workspace_url=self.settings.openproject_url.strip().rstrip("/"),
        )

    async def overview(self) -> OpenProjectOverview:
        status = self.status()
        if not status.configured:
            return OpenProjectOverview(
                configured=False,
                setup_instructions=status.setup_instructions,
            )

        project_id = self.settings.openproject_project_id.strip()
        project_data = await self._get(f"/api/v3/projects/{project_id}")
        package_data = await self._get(
            f"/api/v3/projects/{project_id}/work_packages?pageSize=100"
        )

        try:
            project = OpenProjectProject(
                id=project_data["id"],
                name=project_data["name"],
                description=_plain_text(project_data.get("description")),
                url=f"{self.settings.openproject_url.strip().rstrip('/')}/projects/{project_id}",
            )
            embedded = package_data.get("_embedded", {}).get("elements", [])
            packages = [self._work_package(item) for item in embedded]
        except (KeyError, TypeError, ValueError) as exc:
            raise OpenProjectUnavailable(_UNAVAILABLE) from exc

        return OpenProjectOverview(
            configured=True,
            workspace_url=self.settings.openproject_url.strip().rstrip("/"),
            project=project,
            work_packages=packages,
            total_count=package_data.get("total", len(packages)),
        )

    async def work_package(self, work_package_id: int) -> OpenProjectWorkPackage:
        if not self.settings.openproject_configured:
            raise OpenProjectUnavailable(_UNAVAILABLE)
        payload = await self._get(f"/api/v3/work_packages/{work_package_id}")
        try:
            self._ensure_configured_project(payload)
            return self._work_package(payload)
        except (KeyError, TypeError, ValueError) as exc:
            raise OpenProjectUnavailable(_UNAVAILABLE) from exc

    def _ensure_configured_project(self, item: dict[str, Any]) -> None:
        """Do not let the detail proxy read packages outside its configured project."""
        links = item.get("_links")
        project = links.get("project") if isinstance(links, dict) else None
        project_link = project.get("href") if isinstance(project, dict) else None
        if not isinstance(project_link, str):
            raise OpenProjectUnavailable(_UNAVAILABLE)

        base = urlparse(self.settings.openproject_url.strip())
        linked_project = urlparse(project_link)
        expected_path = (
            f"{base.path.rstrip('/')}/api/v3/projects/"
            f"{self.settings.openproject_project_id.strip()}"
        )
        same_origin = not linked_project.netloc or (
            linked_project.scheme == base.scheme
            and linked_project.netloc.casefold() == base.netloc.casefold()
        )
        if not same_origin or linked_project.path.rstrip("/") != expected_path:
            raise OpenProjectUnavailable(_UNAVAILABLE)

    async def _get(self, path: str) -> dict[str, Any]:
        base_url = self.settings.openproject_url.strip().rstrip("/")
        parsed_base = urlparse(base_url)
        if not self.settings.openproject_configured or not parsed_base.hostname:
            raise OpenProjectUnavailable(_UNAVAILABLE)
        try:
            async with httpx.AsyncClient(
                transport=self.transport,
                timeout=10.0,
                follow_redirects=False,
                auth=("apikey", self.settings.openproject_api_key.get_secret_value()),
            ) as client:
                response = await client.get(f"{base_url}{path}")
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OpenProjectUnavailable(_UNAVAILABLE) from exc
        if not isinstance(payload, dict):
            raise OpenProjectUnavailable(_UNAVAILABLE)
        return payload

    def _work_package(self, item: dict[str, Any]) -> OpenProjectWorkPackage:
        links = item.get("_links", {})
        status = _linked_name(links.get("status")) or "Unknown"
        priority = _linked_name(links.get("priority"))
        assignee = _linked_name(links.get("assignee"))
        return OpenProjectWorkPackage(
            id=item["id"],
            subject=item["subject"],
            status=status,
            priority=priority,
            assignee=assignee,
            start_date=item.get("startDate"),
            due_date=item.get("dueDate"),
            description=_plain_text(item.get("description")),
            url=f"{self.settings.openproject_url.strip().rstrip('/')}/work_packages/{item['id']}",
        )


def _linked_name(link: Any) -> str | None:
    if isinstance(link, dict):
        title = link.get("title")
        return title if isinstance(title, str) and title else None
    return None


def _plain_text(value: Any) -> str:
    if isinstance(value, dict):
        text = value.get("raw")
        return text if isinstance(text, str) else ""
    return value if isinstance(value, str) else ""