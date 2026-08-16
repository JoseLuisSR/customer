"""Pruebas unitarias de la entidad `Address`."""

from typing import NamedTuple

import pytest

from customers.domain.address.entities import Address
from customers.domain.address.exceptions import InvalidAddressFieldError
from customers.domain.address.value_objects import (
    AddressId,
    City,
    Country,
    PostalCode,
    State,
    StreetAddress,
)
from customers.domain.customer.value_objects import CustomerId
from customers.domain.shared.status import EntityStatus


class _AddressFields(NamedTuple):
    country: Country
    state: State
    city: City
    street_address: StreetAddress
    postal_code: PostalCode


def _valid_address_fields() -> _AddressFields:
    return _AddressFields(
        country=Country("Colombia"),
        state=State("Bogotá D.C."),
        city=City("Bogotá"),
        street_address=StreetAddress("Calle 1 # 2-3"),
        postal_code=PostalCode("110111"),
    )


def _build_address(customer_id: CustomerId) -> Address:
    fields = _valid_address_fields()
    return Address.create(
        customer_id=customer_id,
        country=fields.country,
        state=fields.state,
        city=fields.city,
        street_address=fields.street_address,
        postal_code=fields.postal_code,
    )


class TestAddressRequiresCustomerId:
    def test_create_builds_an_active_address_for_an_existing_customer(self) -> None:
        # Arrange
        customer_id = CustomerId.generate()

        # Act
        address = _build_address(customer_id)

        # Assert
        assert address.customer_id == customer_id
        assert address.status is EntityStatus.ACTIVE

    def test_cannot_be_constructed_without_a_valid_customer_id(self) -> None:
        # Arrange
        fields = _valid_address_fields()

        # Act / Assert
        with pytest.raises(InvalidAddressFieldError):
            Address(
                id=AddressId.generate(),
                customer_id=None,  # type: ignore[arg-type]
                country=fields.country,
                state=fields.state,
                city=fields.city,
                street_address=fields.street_address,
                postal_code=fields.postal_code,
                status=EntityStatus.ACTIVE,
            )


class TestAddressMarkDeleted:
    def test_marks_address_as_deleted(self) -> None:
        # Arrange
        address = _build_address(CustomerId.generate())

        # Act
        address.mark_deleted()

        # Assert
        assert address.status is EntityStatus.DELETED
