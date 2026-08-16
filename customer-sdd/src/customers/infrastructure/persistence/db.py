"""Motor y fábrica de sesiones de SQLAlchemy (`plan.md` §4/§5.1).

Expone utilidades reutilizables tanto por la futura Fase 4 (inyección de
la sesión por request en Flask, vía `teardown_appcontext`) como por los
tests de integración de la Fase 6 (que inicializan el motor contra el
servicio `db_test` de `docker-compose.yml`).
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from customers.infrastructure.config import get_config

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _Database:
    """Agrupa el `Engine` y la fábrica de sesiones activos del proceso."""

    engine: Engine
    session_factory: scoped_session[Session]


_database: _Database | None = None


def init_engine(database_url: str | None = None) -> Engine:
    """Crea (o recrea) el `Engine`/fábrica de sesiones global.

    `database_url` permite inyectar una URL distinta a la de `get_config()`
    (usado por los tests de integración contra `db_test`). Si no se pasa,
    se usa `DATABASE_URL`. Llamar de nuevo reemplaza el estado anterior
    (útil en tests que necesitan apuntar a otra base entre casos).
    """
    global _database
    url = database_url or get_config().database_url
    engine = create_engine(url, pool_pre_ping=True, future=True)
    session_factory: scoped_session[Session] = scoped_session(
        sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    )
    _database = _Database(engine=engine, session_factory=session_factory)
    logger.info("Motor de base de datos inicializado.")
    return engine


def _get_database() -> _Database:
    if _database is None:
        init_engine()
    if _database is None:  # pragma: no cover - defensivo, init_engine siempre asigna
        raise RuntimeError("No fue posible inicializar la base de datos.")
    return _database


def get_engine() -> Engine:
    """Devuelve el `Engine` global, inicializándolo si aún no existe."""
    return _get_database().engine


def get_session_factory() -> scoped_session[Session]:
    """Devuelve la fábrica de sesiones (`scoped_session`) global."""
    return _get_database().session_factory


def get_session() -> Session:
    """Obtiene la sesión de SQLAlchemy asociada al scope actual.

    Reutilizable tanto para inyectar repositorios en cada request (Fase 4)
    como en los tests de integración (Fase 6).
    """
    return _get_database().session_factory()


def remove_session() -> None:
    """Cierra/limpia la sesión del scope actual.

    Pensado para invocarse en `teardown_appcontext` (Fase 4) o al final de
    cada test de integración.
    """
    if _database is not None:
        _database.session_factory.remove()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager transaccional: `commit` si todo va bien, `rollback` si no.

    Útil para scripts y tests que necesiten una unidad de trabajo completa
    sin depender del ciclo de vida de una request Flask.
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        remove_session()
