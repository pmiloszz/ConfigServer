# app/api/flags.py
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.db import get_session
from app.models import Flag
from app.schemas.flag import FlagCreate, FlagUpdate, FlagRead

router = APIRouter(prefix="/flags", tags=["flags"])

@router.get("", response_model=List[FlagRead])
def list_flags(app_name: str, env: str, session: Session = Depends(get_session)):
    stmt = select(Flag).where(Flag.app == app_name, Flag.env == env)
    return session.exec(stmt).all()

@router.get("/{flag_id}", response_model=FlagRead)
def get_flag(flag_id: int, session: Session = Depends(get_session)):
    f = session.get(Flag, flag_id)
    if not f:
        raise HTTPException(status_code=404, detail="Flag not found")
    return f

@router.post("", response_model=FlagRead, status_code=status.HTTP_201_CREATED)
def create_flag(payload: FlagCreate, session: Session = Depends(get_session)):
    f = Flag(
        app=payload.app,
        env=payload.env,
        key=payload.key,
        value=payload.value,
        description=payload.description,
    )
    session.add(f)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Flag already exists for app/env/key")
    session.refresh(f)
    return f

@router.put("/{flag_id}", response_model=FlagRead)
def update_flag(flag_id: int, payload: FlagUpdate, session: Session = Depends(get_session)):
    f = session.get(Flag, flag_id)
    if not f:
        raise HTTPException(status_code=404, detail="Flag not found")
    if payload.version != f.version:
        raise HTTPException(status_code=409, detail="Version mismatch")
    updated = False
    if payload.value is not None and payload.value != f.value:
        f.value = payload.value
        updated = True
    if payload.description is not None and payload.description != f.description:
        f.description = payload.description
        updated = True
    if updated:
        f.version = f.version + 1
        f.updated_at = datetime.utcnow()
        session.add(f)
        session.commit()
        session.refresh(f)
    return f

@router.delete("/{flag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flag(flag_id: int, session: Session = Depends(get_session)):
    f = session.get(Flag, flag_id)
    if not f:
        raise HTTPException(status_code=404, detail="Flag not found")
    session.delete(f)
    session.commit()
    return None