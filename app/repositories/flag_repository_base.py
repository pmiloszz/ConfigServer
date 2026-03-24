# app/repositories/flag_repository_base.py
from abc import ABC, abstractmethod

from sqlmodel import Session

from app.models import Flag


class FlagRepositoryBase(ABC):
    @abstractmethod
    def __init__(self, session: Session) -> None: ...

    @abstractmethod
    def list_by_app_env(self, app_name: str, env: str, limit: int = 200) -> list[Flag]: ...

    @abstractmethod
    def get_by_id(self, flag_id: int) -> Flag | None: ...

    @abstractmethod
    def create(self, flag: Flag) -> Flag: ...

    @abstractmethod
    def save(self, flag: Flag) -> None: ...

    @abstractmethod
    def delete(self, flag: Flag) -> None: ...

    @abstractmethod
    def list_apps(self) -> list[str]: ...

    @abstractmethod
    def list_envs(self, app_name: str) -> list[str]: ...
