"""OpenProject configuration, REST mapping, and API error tests."""

import httpx
import pytest
from pydantic import SecretStr

from app.config import Settings
from app.services.openproject_service import OpenProjectService, OpenProjectUnavailable


def configured_settings(**overrides) -> Settings:
    values = {
        "openproject_url": "https://projects.example.test",
        "openproject_api_key": SecretStr("private-token"),
        "openproject_project_id": "42",
    }
    values.update(overrides)
    return Settings(**values)


def test_openproject_requires_safe_url_token_and_numeric_project_id() -> None:
    assert configured_settings().openproject_configured
    assert not configured_settings(openproject_api_key=SecretStr("")).openproject_configured
    assert not configured_settings(openproject_project_id="team").openproject_configured
    assert not configured_settings(openproject_url="https://user:pass@example.test").openproject_configured
    assert not configured_settings(openproject_url="https://projects.example.test:invalid").openproject_configured
    assert not Settings().openproject_configured


def test_unconfigured_service_returns_setup_state_without_upstream_call() -> None:
    status = OpenProjectService(Settings()).status()
    assert status.configured is False
    assert "OPENPROJECT_API_KEY" in status.setup_instructions
    assert "private-token" not in str(status.model_dump())


@pytest.mark.anyio
async def test_overview_maps_project_and_work_packages_from_rest_api() -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/projects/42"):
            return httpx.Response(200, json={"id": 42, "name": "Care rollout", "description": {"raw": "Milestone plan"}})
        return httpx.Response(200, json={
            "total": 1,
            "_embedded": {"elements": [{
                "id": 7,
                "subject": "Review clinic onboarding",
                "description": {"raw": "Confirm the checklist"},
                "startDate": "2026-10-01",
                "dueDate": "2026-10-15",
                "_links": {
                    "status": {"title": "In progress"},
                    "priority": {"title": "Normal"},
                    "assignee": {"title": "Alex"},
                },
            }]},
        })

    overview = await OpenProjectService(
        configured_settings(), transport=httpx.MockTransport(handler)
    ).overview()

    assert overview.project.name == "Care rollout"
    assert overview.work_packages[0].status == "In progress"
    assert overview.work_packages[0].assignee == "Alex"
    assert overview.work_packages[0].description == "Confirm the checklist"
    assert requests[0].headers["authorization"].startswith("Basic ")
    assert "private-token" not in overview.model_dump_json()
    assert all(request.url.host == "projects.example.test" for request in requests)


@pytest.mark.anyio
async def test_upstream_auth_failure_is_sanitized() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="private-token rejected")

    service = OpenProjectService(configured_settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(OpenProjectUnavailable) as error:
        await service.overview()

    assert "private-token" not in str(error.value)
    assert "401" not in str(error.value)


@pytest.mark.anyio
async def test_work_package_detail_is_limited_to_configured_project() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "id": 7,
            "subject": "Another project's item",
            "_links": {"project": {"href": "/api/v3/projects/99"}},
        })

    service = OpenProjectService(configured_settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(OpenProjectUnavailable):
        await service.work_package(7)


@pytest.mark.anyio
async def test_work_package_detail_rejects_malformed_project_link() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": 7, "subject": "Incomplete", "_links": None})

    service = OpenProjectService(configured_settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(OpenProjectUnavailable):
        await service.work_package(7)


def test_openproject_routes_are_registered(client) -> None:
    status = client.get("/api/openproject/status")
    overview = client.get("/api/openproject/")

    assert status.status_code == 200
    assert status.json()["configured"] is False
    assert overview.status_code == 200
    assert overview.json()["work_packages"] == []
    assert "OPENPROJECT_URL" in overview.json()["setup_instructions"]


def test_upstream_auth_failure_returns_sanitized_gateway_error(client, monkeypatch) -> None:
    from app.main import app
    from app.routers.openproject import get_openproject_service

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="private-token rejected")

    service = OpenProjectService(configured_settings(), transport=httpx.MockTransport(handler))
    monkeypatch.setitem(app.dependency_overrides, get_openproject_service, lambda: service)
    response = client.get("/api/openproject/")

    assert response.status_code == 502
    assert "private-token" not in response.text
    assert "401" not in response.text


def test_work_package_detail_route_returns_configured_project_item(client, monkeypatch) -> None:
    from app.main import app
    from app.routers.openproject import get_openproject_service

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v3/work_packages/7"
        return httpx.Response(200, json={
            "id": 7,
            "subject": "Review onboarding",
            "_links": {
                "project": {"href": "/api/v3/projects/42"},
                "status": {"title": "In progress"},
            },
        })

    service = OpenProjectService(configured_settings(), transport=httpx.MockTransport(handler))
    monkeypatch.setitem(app.dependency_overrides, get_openproject_service, lambda: service)
    response = client.get("/api/openproject/work-packages/7")

    assert response.status_code == 200
    assert response.json()["subject"] == "Review onboarding"
    assert response.json()["status"] == "In progress"