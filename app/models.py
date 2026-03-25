# app/models.py
from datetime import UTC, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Flag(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("app", "env", "key", name="uix_flag_app_env_key"),)

    id: int | None = Field(default=None, primary_key=True)
    app: str
    env: str
    key: str
    value: bool
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: int = Field(default=1)
