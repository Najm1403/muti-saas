from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from core.config import settings
from db.base import Base

# Import all models so SQLAlchemy registers them
# with Base.metadata.
import models  # noqa: F401


# Alembic Config object
config = context.config


# ------------------------------------------------------------
# DATABASE URL
# ------------------------------------------------------------

config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL,
)


# ------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ------------------------------------------------------------
# SQLALCHEMY METADATA
# ------------------------------------------------------------

target_metadata = Base.metadata


# ------------------------------------------------------------
# OFFLINE MIGRATIONS
# ------------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Run migrations without creating a database connection.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
    )

    with context.begin_transaction():
        context.run_migrations()


# ------------------------------------------------------------
# ONLINE MIGRATIONS
# ------------------------------------------------------------

def run_migrations_online() -> None:
    """
    Run migrations using an active database connection.
    """

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ------------------------------------------------------------
# RUN
# ------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()