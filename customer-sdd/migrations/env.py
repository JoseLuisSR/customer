import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from customers.infrastructure.persistence import models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# `target_metadata` habilita `alembic revision --autogenerate` a partir de
# los modelos SQLAlchemy (`plan.md` §5.1).
target_metadata = models.Base.metadata

# La URL de conexión NUNCA se hardcodea en `alembic.ini` (que la deja vacía
# intencionalmente): se inyecta en tiempo de ejecución desde la variable de
# entorno `DATABASE_URL` (`plan.md` §5.1), la misma que usa
# `infrastructure/config.py` para el resto de la aplicación.
_database_url = os.environ.get("DATABASE_URL")
if not _database_url:
    raise RuntimeError(
        "La variable de entorno DATABASE_URL es obligatoria para ejecutar migraciones "
        "de Alembic y no fue definida. Ver .env.example para el formato esperado."
    )
config.set_main_option("sqlalchemy.url", _database_url)

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
