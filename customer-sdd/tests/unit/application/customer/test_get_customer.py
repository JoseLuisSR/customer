"""Pruebas unitarias del caso de uso `GetCustomer`."""

from __future__ import annotations

from customers.application.customer.create_customer import CreateCustomer, CreateCustomerRequest
from customers.application.customer.get_customer import GetCustomer
from customers.domain.customer.value_objects import CustomerId
from customers.domain.shared.status import EntityStatus

from ..fakes import FakeAddressRepository, FakeCustomerRepository


def _create_customer(
    customer_repository: FakeCustomerRepository, address_repository: FakeAddressRepository
) -> CustomerId:
    create_use_case = CreateCustomer(customer_repository, address_repository)
    result = create_use_case.execute(
        CreateCustomerRequest(
            name="Jane Doe",
            identification="ID-001",
            age=30,
            email="jane.doe@example.com",
            addresses=[],
        )
    )
    assert result.data is not None
    return CustomerId.from_string(result.data["id"])


class TestGetCustomer:
    def test_returns_existing_customer_with_active_addresses(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        use_case = GetCustomer(customer_repository, address_repository)

        # Act
        result = use_case.execute(customer_id)

        # Assert
        assert result.success is True
        assert result.entity_status is EntityStatus.ACTIVE
        assert result.data is not None
        assert result.data["id"] == str(customer_id)
        assert result.data["addresses"] == []

    def test_returns_not_found_for_unknown_customer(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        use_case = GetCustomer(customer_repository, address_repository)
        customer_id = CustomerId.generate()

        # Act
        result = use_case.execute(customer_id)

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert result.errors[0].code == "ERR-003"

    def test_returns_not_found_for_deleted_customer(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        customer = customer_repository.get_by_id(customer_id)
        assert customer is not None
        customer.mark_deleted()
        customer_repository.update(customer)
        use_case = GetCustomer(customer_repository, address_repository)

        # Act
        result = use_case.execute(customer_id)

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert result.errors[0].code == "ERR-003"
