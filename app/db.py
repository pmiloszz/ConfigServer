# app/db.py
from typing import Generator
from sqlmodel import create_engine, Session
from sqlalchemy.engine import Engine
from app.settings import settings

DATABASE_URL = settings.database_url

# sqlite needs connect_args
is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine: Engine = create_engine(DATABASE_URL, echo=settings.debug, connect_args=connect_args)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session