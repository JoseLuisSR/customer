"""Pruebas unitarias del caso de uso `ListAddresses`."""

from __future__ import annotations

from customers.application.address.create_address import CreateAddress, CreateAddressRequest
from customers.application.address.list_addresses import ListAddresses
from customers.application.customer.create_customer import CreateCustomer, CreateCustomerRequest
from customers.domain.customer.value_objects import CustomerId

from ..fakes import FakeAddressRepository, FakeCustomerRepository


def _create_customer(
    customer_repository: FakeCustomerRepository,
    address_repository: FakeAddressRepository,
    *,
    identification: str = "ID-001",
    email: str = "jane.doe@example.com",
) -> CustomerId:
    create_use_case = CreateCustomer(customer_repository, address_repository)
    result = create_use_case.execute(
        CreateCustomerRequest(
            name="Jane Doe", identification=identification, age=30, email=email, addresses=[]
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


class TestListAddresses:
    def test_lists_only_addresses_of_requested_customer(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        other_customer_id = _create_customer(
            customer_repository,
            address_repository,
            identification="ID-002",
            email="other@example.com",
        )
        create_address_use_case = CreateAddress(customer_repository, address_repository)
        create_address_use_case.execute(customer_id, _address_request())
        create_address_use_case.execute(other_customer_id, _address_request())
        use_case = ListAddresses(customer_repository, address_repository)

        # Act
        result = use_case.execute(customer_id)

        # Assert
        assert result.success is True
        assert result.data is not None
        assert len(result.data["items"]) == 1
        assert result.data["items"][0]["customer_id"] == str(customer_id)

    def test_returns_not_found_for_unknown_customer(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        use_case = ListAddresses(customer_repository, address_repository)

        # Act
        result = use_case.execute(CustomerId.generate())

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert result.errors[0].code == "ERR-003"
