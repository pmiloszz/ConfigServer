# app/db.py
import os
from typing import Generator
from sqlmodel import create_engine, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./flags.db")

# detect sqlite vs other dialects
is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        echo=True,
        connect_args={"check_same_thread": False},  # only for sqlite
    )
else:
    engine = create_engine(DATABASE_URL, echo=True)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session