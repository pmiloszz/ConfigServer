# app/api/flags.py
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db import get_session
from app.repositories.flag_repository import FlagRepository
from app.repositories.flag_repository_base import FlagRepositoryBase
from app.schemas.flag import FlagCreate, FlagRead, FlagUpdate
from app.services.exceptions import (
    FlagAlreadyExists,
    FlagNotFound,
    VersionConflict,
)
from app.services.flag_service import FlagService

router = APIRouter(prefix="/flags", tags=["flags"])


def get_flag_repository(
    session: Annotated[Session, Depends(get_session)],
) -> FlagRepositoryBase:
    return FlagRepository(session)


def get_flag_service(
    repo: Annotated[FlagRepositoryBase, Depends(get_flag_repository)],
) -> FlagService:
    return FlagService(repo)


@router.get("", response_model=list[FlagRead])
def list_flags(
    app_name: str,
    env: str,
    service: Annotated[FlagService, Depends(get_flag_service)],
):
    return service.list_flags(app_name=app_name, env=env)


@router.get("/{flag_id}", response_model=FlagRead)
def get_flag(
    flag_id: int,
    service: Annotated[FlagService, Depends(get_flag_service)],
):
    try:
        return service.get_flag(flag_id)
    except FlagNotFound as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


@router.post("", response_model=FlagRead, status_code=status.HTTP_201_CREATED)
def create_flag(
    payload: FlagCreate,
    service: Annotated[FlagService, Depends(get_flag_service)],
):
    try:
        return service.create_flag(payload)
    except FlagAlreadyExists as err:
        raise HTTPException(status_code=409, detail=str(err)) from err


@router.put("/{flag_id}", response_model=FlagRead)
def update_flag(
    flag_id: int,
    payload: FlagUpdate,
    service: Annotated[FlagService, Depends(get_flag_service)],
):
    try:
        return service.update_flag(flag_id, payload)
    except FlagNotFound as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except VersionConflict as err:
        raise HTTPException(status_code=409, detail=str(err)) from err


@router.delete("/{flag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flag(
    flag_id: int,
    service: Annotated[FlagService, Depends(get_flag_service)],
):
    try:
        service.delete_flag(flag_id)
    except FlagNotFound as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    return None
