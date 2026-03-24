# app/api/apps.py
#
# Discovery endpoints — answer the question "what exists in this server?"
#
# Without these, a client must already know the app name and environment
# before it can query flags. These endpoints make the API self-describing:
# you can land on a fresh server and discover everything through the API
# without reading any documentation or source code.
#
# GET /apps                        → list of distinct app names
# GET /apps/{app_name}/envs        → list of envs that exist for that app

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.repositories.flag_repository import FlagRepository
from app.repositories.flag_repository_base import FlagRepositoryBase
from app.services.flag_service import FlagService

router = APIRouter(tags=["discovery"])


def get_flag_repository(
    session: Annotated[Session, Depends(get_session)],
) -> FlagRepositoryBase:
    return FlagRepository(session)


def get_flag_service(
    repo: Annotated[FlagRepositoryBase, Depends(get_flag_repository)],
) -> FlagService:
    return FlagService(repo)


@router.get("/apps", response_model=list[str])
def list_apps(
    service: Annotated[FlagService, Depends(get_flag_service)],
):
    """Return a sorted list of all distinct app names that have flags."""
    return service.list_apps()


@router.get("/apps/{app_name}/envs", response_model=list[str])
def list_envs(
    app_name: str,
    service: Annotated[FlagService, Depends(get_flag_service)],
):
    """Return a sorted list of all environments that exist for the given app."""
    return service.list_envs(app_name=app_name)
