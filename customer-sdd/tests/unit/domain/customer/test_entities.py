"""Pruebas unitarias del agregado `Customer`."""

import pytest

from customers.domain.address.entities import Address
from customers.domain.address.exceptions import AddressCustomerMismatchError
from customers.domain.address.value_objects import City, Country, PostalCode, State, StreetAddress
from customers.domain.customer.entities import Customer
from customers.domain.customer.exceptions import MaxAddressesExceededError
from customers.domain.customer.value_objects import Age, CustomerId, Email, Identification, Name
from customers.domain.shared.status import EntityStatus


def _build_customer() -> Customer:
    return Customer.create(
        name=Name("Jane Doe"),
        identification=Identification("ID-001"),
        age=Age(30),
        email=Email("jane.doe@example.com"),
    )


def _build_address(customer_id: CustomerId) -> Address:
    return Address.create(
        customer_id=customer_id,
        country=Country("Colombia"),
        state=State("Bogotá D.C."),
        city=City("Bogotá"),
        street_address=StreetAddress("Calle 1 # 2-3"),
        postal_code=PostalCode("110111"),
    )


class TestCustomerAddAddress:
    def test_adds_address_when_under_the_limit(self) -> None:
        # Arrange
        customer = _build_customer()
        address = _build_address(customer.id)

        # Act
        customer.add_address(address)

        # Assert
        assert customer.addresses == [address]

    def test_accepts_exactly_five_active_addresses(self) -> None:
        # Arrange
        customer = _build_customer()
        addresses = [_build_address(customer.id) for _ in range(5)]

        # Act
        for address in addresses:
            customer.add_address(address)

        # Assert
        assert len(customer.active_addresses()) == 5

    def test_rejects_sixth_active_address(self) -> None:
        # Arrange
        customer = _build_customer()
        for _ in range(5):
            customer.add_address(_build_address(customer.id))
        sixth_address = _build_address(customer.id)

        # Act / Assert
        with pytest.raises(MaxAddressesExceededError):
            customer.add_address(sixth_address)
        assert len(customer.addresses) == 5

    def test_rejects_address_belonging_to_another_customer(self) -> None:
        # Arrange
        customer = _build_customer()
        another_customer_id = CustomerId.generate()
        foreign_address = _build_address(another_customer_id)

        # Act / Assert
        with pytest.raises(AddressCustomerMismatchError):
            customer.add_address(foreign_address)


class TestCustomerMarkDeleted:
    def test_marks_customer_as_deleted(self) -> None:
        # Arrange
        customer = _build_customer()

        # Act
        customer.mark_deleted()

        # Assert
        assert customer.status is EntityStatus.DELETED

    def test_marks_all_active_addresses_as_deleted(self) -> None:
        # Arrange
        customer = _build_customer()
        for _ in range(3):
            customer.add_address(_build_address(customer.id))

        # Act
        customer.mark_deleted()

        # Assert
        assert all(address.status is EntityStatus.DELETED for address in customer.addresses)
        assert customer.active_addresses() == []

    def test_does_not_resurrect_already_deleted_addresses(self) -> None:
        # Arrange
        customer = _build_customer()
        address = _build_address(customer.id)
        customer.add_address(address)
        address.mark_deleted()

        # Act
        customer.mark_deleted()

        # Assert
        assert address.status is EntityStatus.DELETED
