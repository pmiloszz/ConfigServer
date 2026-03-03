# app/api.py
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.models import Flag
from pydantic import BaseModel

router = APIRouter(prefix="/flags", tags=["flags"])

class FlagCreate(BaseModel):
    app: str
    env: str
    key: str
    value: bool
    description: Optional[str] = None

class FlagUpdate(BaseModel):
    value: Optional[bool] = None
    description: Optional[str] = None
    version: int

@router.post("", response_model=Flag, status_code=status.HTTP_201_CREATED)
def create_flag(payload: FlagCreate, session: Session = Depends(get_session)):
    # Optional: check uniqueness by (app, env, key)
    stmt = select(Flag).where(Flag.app == payload.app, Flag.env == payload.env, Flag.key == payload.key)
    existing = session.exec(stmt).first()
    if existing:
        raise HTTPException(status_code=409, detail="Flag already exists for app/env/key")
    f = Flag(
        app=payload.app,
        env=payload.env,
        key=payload.key,
        value=payload.value,
        description=payload.description,
    )
    session.add(f)
    session.commit()
    session.refresh(f)
    return f

@router.put("/{flag_id}", response_model=Flag)
def update_flag(flag_id: int, payload: FlagUpdate, session: Session = Depends(get_session)):
    f = session.get(Flag, flag_id)
    if not f:
        raise HTTPException(status_code=404, detail="Flag not found")
    # optimistic locking: require client to send current version
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