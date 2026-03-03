from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Flag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    app: str
    env: str
    key: str
    value: bool
    description: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1