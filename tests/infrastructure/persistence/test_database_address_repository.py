import uuid

import pytest
from flask import Flask

from src.domain.address import Address
from src.exception.address_exception import AddressNotFoundError
from src.exception.customer_exception import CustomerNotFoundError
from src.infrastructure.persistence.database_address_repository import (
    DatabaseAddressRepository,
)

# Every test in this module needs a live Postgres connection (see
# tests/conftest.py::app for the requirements).
pytestmark = pytest.mark.usefixtures("app")


@pytest.fixture
def repository(app: Flask) -> DatabaseAddressRepository:
    return DatabaseAddressRepository()


def _new_address(customer_id: uuid.UUID, **overrides: str) -> Address:
    payload = {
        "country": "Colombia",
        "state": "Bogota D.C.",
        "city": "Bogota",
        "address": "Cra 1 # 2-3",
        "postal_code": "110111",
    }
    payload.update(overrides)
    return Address.create(customer_id, **payload)


class TestCreate:
    def test_creates_and_persists_the_address(
        self, repository: DatabaseAddressRepository, customer_id: uuid.UUID
    ):
        address = _new_address(customer_id)

        repository.create(address)

        fetched = repository.get_by_id(customer_id, address.id)
        assert fetched.id == address.id
        assert fetched.customer_id == customer_id
        assert fetched.country == "Colombia"
        assert fetched.postal_code == "110111"

    def test_raises_customer_not_found_when_customer_does_not_exist(
        self, repository: DatabaseAddressRepository
    ):
        address = _new_address(uuid.uuid4())

        with pytest.raises(CustomerNotFoundError):
            repository.create(address)


class TestGetById:
    def test_returns_the_address(
        self, repository: DatabaseAddressRepository, customer_id: uuid.UUID
    ):
        address = _new_address(customer_id)
        repository.create(address)

        fetched = repository.get_by_id(customer_id, address.id)

        assert fetched.id == address.id

    def test_raises_when_the_address_does_not_exist(
        self, repository: DatabaseAddressRepository, customer_id: uuid.UUID
    ):
        with pytest.raises(AddressNotFoundError):
            repository.get_by_id(customer_id, uuid.uuid4())


class TestGetAllByCustomerId:
    def test_returns_all_addresses_of_the_customer(
        self, repository: DatabaseAddressRepository, customer_id: uuid.UUID
    ):
        first = _new_address(customer_id, city="Bogota")
        second = _new_address(customer_id, city="Medellin")
        repository.create(first)
        repository.create(second)

        addresses = repository.get_all_by_customer_id(customer_id)

        assert {address.id for address in addresses} == {first.id, second.id}

    def test_returns_an_empty_list_when_the_customer_has_no_addresses(
        self, repository: DatabaseAddressRepository, customer_id: uuid.UUID
    ):
        assert repository.get_all_by_customer_id(customer_id) == []


class TestCountByCustomerId:
    def test_counts_addresses_of_the_customer(
        self, repository: DatabaseAddressRepository, customer_id: uuid.UUID
    ):
        repository.create(_new_address(customer_id))
        repository.create(_new_address(customer_id, city="Medellin"))

        assert repository.count_by_customer_id(customer_id) == 2

    def test_returns_zero_when_the_customer_has_no_addresses(
        self, repository: DatabaseAddressRepository, customer_id: uuid.UUID
    ):
        assert repository.count_by_customer_id(customer_id) == 0


class TestUpdatePartial:
    def test_updates_and_returns_the_address(
        self, repository: DatabaseAddressRepository, customer_id: uuid.UUID
    ):
        address = _new_address(customer_id)
        repository.create(address)
        address.city = "Medellin"

        updated = repository.update_partial(customer_id, address.id, address)

        assert updated.city == "Medellin"
        fetched = repository.get_by_id(customer_id, address.id)
        assert fetched.city == "Medellin"

    def test_raises_when_the_address_does_not_exist(
        self, repository: DatabaseAddressRepository, customer_id: uuid.UUID
    ):
        missing = _new_address(customer_id)

        with pytest.raises(AddressNotFoundError):
            repository.update_partial(customer_id, missing.id, missing)


class TestUpsert:
    def test_creates_when_the_address_does_not_exist(
        self, repository: DatabaseAddressRepository, customer_id: uuid.UUID
    ):
        address = _new_address(customer_id)

        result, created = repository.upsert(customer_id, address.id, address)

        assert created is True
        assert result.id == address.id
        assert repository.get_by_id(customer_id, address.id).city == "Bogota"

    def test_updates_when_the_address_already_exists(
        self, repository: DatabaseAddressRepository, customer_id: uuid.UUID
    ):
        address = _new_address(customer_id)
        repository.create(address)
        replacement = Address.restore(
            id=address.id,
            customer_id=customer_id,
            country="Mexico",
            state="Jalisco",
            city="Guadalajara",
            address="Av. Siempre Viva 742",
            postal_code="45000",
        )

        result, created = repository.upsert(customer_id, address.id, replacement)

        assert created is False
        assert result.country == "Mexico"
        fetched = repository.get_by_id(customer_id, address.id)
        assert fetched.country == "Mexico"
        assert fetched.city == "Guadalajara"


class TestDeleteById:
    def test_deletes_the_address(
        self, repository: DatabaseAddressRepository, customer_id: uuid.UUID
    ):
        address = _new_address(customer_id)
        repository.create(address)

        repository.delete_by_id(customer_id, address.id)

        with pytest.raises(AddressNotFoundError):
            repository.get_by_id(customer_id, address.id)

    def test_raises_when_the_address_does_not_exist(
        self, repository: DatabaseAddressRepository, customer_id: uuid.UUID
    ):
        with pytest.raises(AddressNotFoundError):
            repository.delete_by_id(customer_id, uuid.uuid4())
