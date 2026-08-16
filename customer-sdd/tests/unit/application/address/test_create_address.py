"""Pruebas unitarias del caso de uso `CreateAddress`."""

from __future__ import annotations

from customers.application.address.create_address import CreateAddress, CreateAddressRequest
from customers.application.customer.create_customer import CreateCustomer, CreateCustomerRequest
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


def _address_request() -> CreateAddressRequest:
    return CreateAddressRequest(
        country="Colombia",
        state="Bogotá D.C.",
        city="Bogotá",
        address="Calle 1 # 2-3",
        postal_code="110111",
    )


class TestCreateAddress:
    def test_creates_address_for_existing_customer(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        use_case = CreateAddress(customer_repository, address_repository)

        # Act
        result = use_case.execute(customer_id, _address_request())

        # Assert
        assert result.success is True
        assert result.entity_status is EntityStatus.ACTIVE
        assert result.data is not None
        assert result.data["customer_id"] == str(customer_id)
        assert result.data["created_at"] is not None
        assert result.data["updated_at"] is not None

    def test_returns_not_found_for_unknown_customer(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        use_case = CreateAddress(customer_repository, address_repository)

        # Act
        result = use_case.execute(CustomerId.generate(), _address_request())

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert result.errors[0].code == "ERR-003"

    def test_rejects_sixth_active_address(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        use_case = CreateAddress(customer_repository, address_repository)
        for _ in range(5):
            result = use_case.execute(customer_id, _address_request())
            assert result.success is True

        # Act
        result = use_case.execute(customer_id, _address_request())

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert result.errors[0].code == "ERR-005"
        assert address_repository.count_active_by_customer(customer_id) == 5
