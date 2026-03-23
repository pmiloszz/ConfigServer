from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models import Flag
from app.repositories.flag_repository_base import FlagRepositoryBase
from app.services.exceptions import FlagAlreadyExists


class FlagRepository(FlagRepositoryBase):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_app_env(self, app_name: str, env: str) -> list[Flag]:
        stmt = select(Flag).where(Flag.app == app_name, Flag.env == env)
        return self._session.exec(stmt).all()

    def get_by_id(self, flag_id: int) -> Flag | None:
        return self._session.get(Flag, flag_id)

    def create(self, flag: Flag) -> Flag:
        self._session.add(flag)
        try:
            self._session.commit()
        except IntegrityError as err:
            self._session.rollback()
            raise FlagAlreadyExists("Flag already exists for app/env/key") from err
        self._session.refresh(flag)
        return flag

    def save(self, flag: Flag) -> None:
        self._session.add(flag)
        self._session.commit()
        self._session.refresh(flag)

    def delete(self, flag: Flag) -> None:
        self._session.delete(flag)
        self._session.commit()
