import pytest

from app.schemas.flag import FlagCreate, FlagUpdate
from app.services.exceptions import FlagAlreadyExists, FlagNotFound, VersionConflict


def test_flag_service_get_not_found(flag_service):
    with pytest.raises(FlagNotFound):
        flag_service.get_flag(flag_id=123)


def test_flag_service_create_and_update_versioning(flag_service):
    created = flag_service.create_flag(
        payload=FlagCreate(
            app="demo",
            env="dev",
            key="t_feature",
            value=True,
            description="init",
        )
    )
    assert created.version == 1

    updated = flag_service.update_flag(
        flag_id=created.id,
        payload=FlagUpdate(
            value=False,
            description="turned off",
            version=created.version,
        ),
    )
    assert updated.value is False
    assert updated.description == "turned off"
    assert updated.version == 2


def test_flag_service_update_stale_version_conflict(flag_service):
    created = flag_service.create_flag(
        payload=FlagCreate(
            app="demo",
            env="dev",
            key="t_feature",
            value=True,
            description="init",
        )
    )

    with pytest.raises(VersionConflict):
        flag_service.update_flag(
            flag_id=created.id,
            payload=FlagUpdate(
                value=False,
                description="stale",
                version=created.version + 1,
            ),
        )


def test_flag_service_delete(flag_service):
    created = flag_service.create_flag(
        payload=FlagCreate(
            app="demo",
            env="dev",
            key="t_feature",
            value=True,
            description="init",
        )
    )

    flag_service.delete_flag(flag_id=created.id)
    with pytest.raises(FlagNotFound):
        flag_service.get_flag(flag_id=created.id)


def test_flag_service_create_duplicate_raises(flag_service):
    flag_service.create_flag(
        payload=FlagCreate(
            app="demo",
            env="dev",
            key="dup",
            value=True,
            description=None,
        )
    )

    with pytest.raises(FlagAlreadyExists):
        flag_service.create_flag(
            payload=FlagCreate(
                app="demo",
                env="dev",
                key="dup",
                value=False,
                description=None,
            )
        )
