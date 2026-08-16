"""Fixtures compartidas de las pruebas de integración (Fase 6).

Referencias: `specs/customers/implementation-plan.md` §8.1, `specs/customers/
plan.md` §6.2. Requiere el servicio `db_test` de `docker-compose.yml`
levantado (`docker compose up -d db_test`) antes de correr esta suite.

**Mecanismo de aislamiento entre tests (decisión de diseño de esta fase):**
se eligió **truncar las tablas `customers`/`addresses` antes de cada test**
(fixture `_clean_tables`, function-scoped y `autouse`) en vez del patrón
clásico de "transacción externa + `SAVEPOINT` + rollback envolviendo la
sesión de la app". El motivo es que los tests HTTP (`tests/integration/
http/*`) ejercitan la aplicación completa a través de `client`
(`app.test_client()`), y `flask_app.py::_teardown_session` hace un
`commit()` real al final de cada request (decisión de diseño ya validada en
la Fase 4). Envolver la sesión de la app en una transacción externa que
nunca se confirma habría exigido parchear ese comportamiento de producción
solo para los tests, probando así un camino de código distinto al que
corre realmente en producción -riesgo que se prefiere evitar-. El truncado
es barato porque `db_test` corre sobre `tmpfs` (Fase 0) y las tablas son
pequeñas en cada test.

Para los tests de persistencia que sí necesitan manipular sesiones propias
sin pasar por Flask (`tests/integration/persistence/*`), se expone
`make_session`/`db_session`, que abren una sesión "de verdad" (con su
propia conexión del pool) y hacen `rollback()`+`close()` al finalizar cada
test, además del truncado compartido.
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Callable, Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from customers.infrastructure.persistence import db
from customers.infrastructure.persistence.models import Base

_DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://customers_test:customers_test@localhost:5433/customers_test"
)


def _database_url() -> str:
    """URL de `db_test` (`docker-compose.yml`, Fase 0).

    Prioriza `DATABASE_URL` si ya está definida en el entorno (permite
    apuntar a otra base en CI/local sin tocar código); en caso contrario
    usa el valor por defecto de `db_test` (usuario/contraseña/base
    `customers_test`, puerto `5433`).
    """
    return os.environ.get("DATABASE_URL") or _DEFAULT_DATABASE_URL


@pytest.fixture(scope="session", autouse=True)
def _configure_environment() -> Iterator[None]:
    """Fuerza `DATABASE_URL`/`FLASK_ENV`/`LOG_LEVEL` antes de que cualquier
    módulo de la aplicación llame `get_config()` (memoizado con
    `lru_cache`, ver `infrastructure/config.py`).
    """
    from customers.infrastructure.config import get_config

    os.environ["DATABASE_URL"] = _database_url()
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("LOG_LEVEL", "WARNING")
    get_config.cache_clear()
    yield
    get_config.cache_clear()


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """Motor de SQLAlchemy contra `db_test`, compartido por toda la sesión de pruebas."""
    sqlalchemy_engine = db.init_engine(_database_url())
    yield sqlalchemy_engine
    sqlalchemy_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _schema(engine: Engine) -> Iterator[None]:
    """Crea el esquema una vez por sesión de pruebas vía `create_all()`.

    `tests/integration/test_migrations.py` es la única excepción explícita
    que ejercita `alembic upgrade head` en vez de `create_all()`
    (`implementation-plan.md` §8.1); ese archivo restaura el esquema de
    `create_all()` al finalizar (ver su propio docstring), por lo que este
    fixture no necesita preocuparse por el orden de ejecución de archivos.
    """
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean_tables(engine: Engine) -> Iterator[None]:
    """Aísla cada test truncando `addresses`/`customers` antes de ejecutarlo.

    Ver nota de diseño completa en el docstring del módulo.
    """
    with engine.begin() as connection:
        connection.execute(text('TRUNCATE TABLE "addresses", "customers" RESTART IDENTITY CASCADE'))
    yield


@pytest.fixture(scope="session")
def session_factory(engine: Engine) -> sessionmaker[Session]:
    """Fábrica de sesiones "crudas" (sin pasar por `db.get_session()`/Flask).

    Usada por los tests de `tests/integration/persistence/*`, que ejercitan
    los adaptadores de repositorio directamente.
    """
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def make_session(session_factory: sessionmaker[Session]) -> Iterator[Callable[[], Session]]:
    """Fábrica de sesiones nuevas para un test, con limpieza automática al final.

    Cada llamada crea una sesión (y por tanto una conexión propia del
    pool) independiente; útil para pruebas de bloqueo pesimista que
    necesitan varias sesiones concurrentes reales (`test_customer_repository.py`).
    Todas las sesiones creadas durante el test se cierran (`rollback()` +
    `close()`) al finalizar, sin importar si el test las cerró explícitamente.
    """
    created: list[Session] = []

    def factory() -> Session:
        session = session_factory()
        created.append(session)
        return session

    yield factory

    for session in created:
        with contextlib.suppress(Exception):  # limpieza best-effort
            session.rollback()
        session.close()


@pytest.fixture
def db_session(make_session: Callable[[], Session]) -> Session:
    """Sesión única "de verdad" para un test de repositorio simple."""
    return make_session()


@pytest.fixture(scope="session")
def app() -> Flask:
    """App Flask (`create_app()`) apuntando a `db_test`, reutilizada por toda la sesión."""
    from customers.infrastructure.flask_app import create_app

    return create_app()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Cliente de pruebas de Flask (`app.test_client()`)."""
    return app.test_client()
