# app/schemas/flag.py
from datetime import datetime
from typing import Optional
from pydantic import ConfigDict
from pydantic import BaseModel

class FlagBase(BaseModel):
    app: str
    env: str
    key: str
    value: bool
    description: str | None = None

class FlagCreate(FlagBase):
    pass

class FlagUpdate(BaseModel):
    value: bool | None = None
    description: str | None = None
    version: int

class FlagRead(FlagBase):
    id: int
    version: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
