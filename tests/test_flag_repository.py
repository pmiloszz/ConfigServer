import pytest

from app.models import Flag
from app.services.exceptions import FlagAlreadyExists


def test_flag_repository_crud(flag_repository):
    created = flag_repository.create(
        Flag(
            app="demo",
            env="dev",
            key="t_feature",
            value=True,
            description="init",
        )
    )
    assert created.id is not None

    fetched = flag_repository.get_by_id(created.id)
    assert fetched is not None
    assert fetched.key == "t_feature"
    assert fetched.value is True

    listed = flag_repository.list_by_app_env("demo", "dev")
    assert any(item.id == created.id for item in listed)

    created.value = False
    flag_repository.save(created)
    fetched_after_save = flag_repository.get_by_id(created.id)
    assert fetched_after_save is not None
    assert fetched_after_save.value is False

    flag_repository.delete(created)
    assert flag_repository.get_by_id(created.id) is None


def test_flag_repository_create_duplicate_raises(flag_repository):
    flag_repository.create(Flag(app="demo", env="dev", key="dup", value=True, description=None))

    with pytest.raises(FlagAlreadyExists):
        flag_repository.create(Flag(app="demo", env="dev", key="dup", value=False, description=None))
