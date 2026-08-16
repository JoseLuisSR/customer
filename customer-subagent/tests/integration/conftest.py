from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from customers.infrastructure.config.settings import Settings
from customers.infrastructure.persistence.database import Base, create_sqlalchemy_engine
from customers.infrastructure.web.app import create_app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://customers:change-me@localhost:5433/customers_test",
)


@pytest.fixture(scope="session")
def engine():
    engine = create_sqlalchemy_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def clean_db(engine):
    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE TABLE customers, addresses RESTART IDENTITY CASCADE")
        )


@pytest.fixture
def app(clean_db):
    settings = Settings(database_url=TEST_DATABASE_URL, flask_env="testing")
    return create_app(settings)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def create_customer(client):
    def _create_customer(**overrides):
        payload = {"name": "Ada Lovelace", "age": 30, "email": "ada@example.com"}
        payload.update(overrides)
        return client.post("/customers", json=payload)

    return _create_customer


@pytest.fixture
def create_address(client):
    def _create_address(customer_id: int, **overrides):
        payload = {
            "country": "Colombia",
            "state": "Meta",
            "city": "Villavicencio",
            "postalcode": "50001",
            "address": "Calle 10 #5-20",
        }
        payload.update(overrides)
        return client.post(f"/customers/{customer_id}/addresses", json=payload)

    return _create_address
