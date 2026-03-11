# app/models.py
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint

class Flag(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("app", "env", "key", name="uix_flag_app_env_key"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    app: str
    env: str
    key: str
    value: bool
    description: str | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1)