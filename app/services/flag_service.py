from datetime import UTC, datetime

from app.models import Flag
from app.repositories.flag_repository_base import FlagRepositoryBase
from app.schemas.flag import FlagCreate, FlagUpdate
from app.services.exceptions import FlagNotFound, VersionConflict


class FlagService:
    def __init__(self, repo: FlagRepositoryBase) -> None:
        self._repo = repo

    def list_flags(self, app_name: str, env: str) -> list[Flag]:
        return self._repo.list_by_app_env(app_name=app_name, env=env)

    def get_flag(self, flag_id: int) -> Flag:
        f = self._repo.get_by_id(flag_id)
        if f is None:
            raise FlagNotFound(flag_id)
        return f

    def create_flag(self, payload: FlagCreate) -> Flag:
        flag = Flag(
            app=payload.app,
            env=payload.env,
            key=payload.key,
            value=payload.value,
            description=payload.description,
        )
        return self._repo.create(flag)

    def update_flag(self, flag_id: int, payload: FlagUpdate) -> Flag:
        f = self.get_flag(flag_id)
        if payload.version != f.version:
            raise VersionConflict(flag_id)

        updated = False
        if payload.value is not None and payload.value != f.value:
            f.value = payload.value
            updated = True
        if payload.description is not None and payload.description != f.description:
            f.description = payload.description
            updated = True

        if updated:
            f.version = f.version + 1
            f.updated_at = datetime.now(UTC)
            self._repo.save(f)

        return f

    def delete_flag(self, flag_id: int) -> None:
        f = self.get_flag(flag_id)
        self._repo.delete(f)
