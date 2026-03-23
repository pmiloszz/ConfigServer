# alembic/env.py
from logging.config import fileConfig

from sqlmodel import SQLModel

from alembic import context

# Import engine and settings from the application
# Use the same engine the app uses so migrations run against the same DB URL and options
from app.db import engine
from app.settings import settings

# Use SQLModel.metadata as the target for autogenerate
target_metadata = SQLModel.metadata

# Alembic config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline():
    """
    Run migrations in 'offline' mode.
    Use settings.database_url as the single source of truth for DB URL.
    """
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Run migrations in 'online' mode using the engine created by app.db.
    This ensures the same engine is used by the application and Alembic.
    """
    connectable = engine
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
