"""Valida que `alembic upgrade head` reproduce exactamente el esquema de
`models.py`, ejecutando las migraciones reales contra una base de datos
completamente limpia (sin usar `Base.metadata.create_all()`).

Referencias: `specs/customers/implementation-plan.md` §8.1/§8.3,
`specs/customers/plan.md` §5.1/§6.2.

Es el único archivo de esta fase que ejercita Alembic en vez del fixture de
esquema compartido (`_schema` en `conftest.py`, basado en
`create_all()`/`drop_all()`). Para no depender del orden de ejecución de
los demás archivos de la suite (que asumen el esquema ya creado por
`create_all()`), este test:

1. Destruye **todo** el esquema `public` (`DROP SCHEMA ... CASCADE`), no
   solo las tablas de `Base.metadata`: esto también elimina la tabla
   `alembic_version` de ejecuciones manuales previas (p. ej. la validación
   de la Fase 3 documentada en memoria de proyecto), evitando que Alembic
   crea erróneamente que ya está en `head` cuando las tablas físicas no
   existen.
2. Corre `alembic upgrade head` contra la base realmente vacía.
3. Usa `alembic check` (Alembic >= 1.9) para confirmar que no hay
   diferencias de autogeneración pendientes entre el esquema recién
   aplicado y `models.Base.metadata` -es decir, que la migración
   `0001_create_customers_and_addresses.py` reproduce el modelo ORM sin
   *drift*-.
4. Restaura el esquema al estado que espera el resto de la suite
   (`Base.metadata.create_all()`, sin `alembic_version`) en un `finally`,
   sin importar si el test anterior falló.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import Engine

from customers.infrastructure.persistence.models import Base

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _alembic_config() -> Config:
    return Config(str(_PROJECT_ROOT / "alembic.ini"))


def _reset_schema(engine: Engine) -> None:
    """Elimina TODO el contenido del esquema `public` (tablas, secuencias,
    `alembic_version`, etc.), dejando una base de datos verdaderamente vacía.
    """
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))


def test_alembic_upgrade_head_matches_models_metadata(engine: Engine) -> None:
    _reset_schema(engine)
    try:
        alembic_cfg = _alembic_config()
        command.upgrade(alembic_cfg, "head")

        # No lanza excepción si el esquema recién aplicado no tiene
        # diferencias autogenerables pendientes respecto a
        # `models.Base.metadata` (sin *drift* entre migración y ORM).
        command.check(alembic_cfg)
    finally:
        _reset_schema(engine)
        Base.metadata.create_all(engine)
