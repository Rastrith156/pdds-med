"""OpenProject status, project overview, and work-package detail endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.schemas.openproject import OpenProjectOverview, OpenProjectStatus, OpenProjectWorkPackage
from app.services.openproject_service import OpenProjectService, OpenProjectUnavailable

router = APIRouter(prefix="/api/openproject", tags=["OpenProject"])


def get_openproject_service() -> OpenProjectService:
    return OpenProjectService(get_settings())


@router.get("/status", response_model=OpenProjectStatus, summary="Check OpenProject configuration")
async def get_status(
    service: OpenProjectService = Depends(get_openproject_service),
) -> OpenProjectStatus:
    return service.status()


@router.get("/", response_model=OpenProjectOverview, summary="Get the configured project and work packages")
async def get_overview(
    service: OpenProjectService = Depends(get_openproject_service),
) -> OpenProjectOverview:
    try:
        return await service.overview()
    except OpenProjectUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/work-packages/{work_package_id}",
    response_model=OpenProjectWorkPackage,
    summary="Get work-package details",
)
async def get_work_package(
    work_package_id: int,
    service: OpenProjectService = Depends(get_openproject_service),
) -> OpenProjectWorkPackage:
    try:
        return await service.work_package(work_package_id)
    except OpenProjectUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc