# tests/test_flag_service.py
# Fixtures (temp_engine, session, flag_repository, flag_service, client)
# come from conftest.py automatically — never redeclare them here.

import pytest

from app.schemas.flag import FlagCreate, FlagUpdate
from app.services.exceptions import FlagNotFound, VersionConflict


def test_create_and_get_flag(flag_service):
    payload = FlagCreate(app="svc", env="prod", key="my_flag", value=True, description="hello")
    created = flag_service.create_flag(payload)

    assert created.id is not None
    assert created.version == 1
    assert created.value is True

    fetched = flag_service.get_flag(created.id)
    assert fetched.id == created.id


def test_get_nonexistent_raises(flag_service):
    with pytest.raises(FlagNotFound):
        flag_service.get_flag(999999)


def test_update_increments_version(flag_service):
    created = flag_service.create_flag(FlagCreate(app="svc", env="prod", key="versioned", value=True))
    updated = flag_service.update_flag(created.id, FlagUpdate(value=False, version=1))

    assert updated.value is False
    assert updated.version == 2


def test_update_wrong_version_raises(flag_service):
    created = flag_service.create_flag(FlagCreate(app="svc", env="prod", key="conflict_key", value=True))

    with pytest.raises(VersionConflict):
        flag_service.update_flag(created.id, FlagUpdate(value=False, version=99))


def test_update_no_change_does_not_bump_version(flag_service):
    """Sending the same value/description must NOT increment version."""
    created = flag_service.create_flag(FlagCreate(app="svc", env="prod", key="stable", value=True, description="same"))
    result = flag_service.update_flag(created.id, FlagUpdate(value=True, description="same", version=1))

    assert result.version == 1


def test_delete_flag(flag_service):
    created = flag_service.create_flag(FlagCreate(app="svc", env="prod", key="to_delete", value=True))
    flag_service.delete_flag(created.id)

    with pytest.raises(FlagNotFound):
        flag_service.get_flag(created.id)


def test_list_flags_returns_only_matching(flag_service):
    flag_service.create_flag(FlagCreate(app="app1", env="staging", key="a", value=True))
    flag_service.create_flag(FlagCreate(app="app1", env="staging", key="b", value=False))
    flag_service.create_flag(FlagCreate(app="app2", env="staging", key="c", value=True))

    results = flag_service.list_flags(app_name="app1", env="staging")

    assert len(results) == 2
    assert all(f.app == "app1" for f in results)


def test_list_flags_respects_limit(flag_service):
    for i in range(5):
        flag_service.create_flag(FlagCreate(app="limited", env="dev", key=f"flag_{i}", value=True))

    results = flag_service.list_flags(app_name="limited", env="dev", limit=3)

    assert len(results) == 3


def test_list_flags_returns_stable_order(flag_service):
    """Results must be ordered by key so clients get consistent ordering."""
    flag_service.create_flag(FlagCreate(app="ordered", env="dev", key="z_last", value=True))
    flag_service.create_flag(FlagCreate(app="ordered", env="dev", key="a_first", value=True))
    flag_service.create_flag(FlagCreate(app="ordered", env="dev", key="m_middle", value=True))

    results = flag_service.list_flags(app_name="ordered", env="dev")
    keys = [f.key for f in results]

    assert keys == sorted(keys)
