"""Shared fixtures for the infrastructure (persistence + web) test suites.

These fixtures require a real Postgres instance reachable at connect time,
i.e. `docker compose up -d postgres` (schema migrated) must be running
before any test that depends on the `app` fixture (directly or
transitively via `client`/`customer_repository`/`customer_id`) executes.

Tests under `tests/domain/` and `tests/application/dto/` and
`tests/application/services/` never import this module's fixtures and can
run without a database at all (`uv run pytest tests/domain tests/application`).

`POSTGRES_HOST` defaults to "localhost" here because these tests run on the
host, outside the `docker-compose` network (where the app normally resolves
the `postgres` service by its container name). Export `POSTGRES_HOST`
yourself before running pytest to override this (e.g. when running the
suite from inside a container attached to the compose network).
"""

import os
import uuid
from collections.abc import Iterator

os.environ.setdefault("POSTGRES_HOST", "localhost")

import flask_migrate
import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.application.repository.customer_repository import CustomerRepository
from src.domain.customer import Customer
from src.infrastructure.persistence.database_customer_repository import (
    DatabaseCustomerRepository,
)
from src.infrastructure.web.app import create_app


@pytest.fixture(scope="session")
def app() -> Iterator[Flask]:
    flask_app = create_app()
    with flask_app.app_context():
        flask_migrate.upgrade()
        yield flask_app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def customer_repository(app: Flask) -> CustomerRepository:
    return DatabaseCustomerRepository()


@pytest.fixture
def customer_id(customer_repository: CustomerRepository) -> Iterator[uuid.UUID]:
    """Creates a real customer row (to satisfy the addresses FK) and cleans
    it up afterwards. `ON DELETE CASCADE` takes care of any addresses
    created against it during the test."""
    customer = Customer.create(
        name="Test Customer", age=30, email=f"{uuid.uuid4()}@example.com"
    )
    customer_repository.create(customer)

    yield customer.id

    customer_repository.delete_by_id(customer.id)
