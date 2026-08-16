"""Pruebas unitarias del caso de uso `ListCustomers`."""

from __future__ import annotations

from customers.application.customer.create_customer import CreateCustomer, CreateCustomerRequest
from customers.application.customer.list_customers import ListCustomers, ListCustomersRequest

from ..fakes import FakeAddressRepository, FakeCustomerRepository


def _create_customers(
    count: int,
    customer_repository: FakeCustomerRepository,
    address_repository: FakeAddressRepository,
) -> None:
    create_use_case = CreateCustomer(customer_repository, address_repository)
    for index in range(count):
        create_use_case.execute(
            CreateCustomerRequest(
                name=f"Customer {index}",
                identification=f"ID-{index:03d}",
                age=30,
                email=f"customer{index}@example.com",
                addresses=[],
            )
        )


class TestListCustomers:
    def test_lists_with_default_pagination(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        _create_customers(3, customer_repository, address_repository)
        use_case = ListCustomers(customer_repository)

        # Act
        result = use_case.execute()

        # Assert
        assert result.success is True
        assert result.entity_status is None
        assert result.data is not None
        assert result.data["page"] == 1
        assert result.data["page_size"] == 20
        assert result.data["total"] == 3
        assert len(result.data["items"]) == 3
        assert "addresses" not in result.data["items"][0]

    def test_lists_with_explicit_pagination(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        _create_customers(5, customer_repository, address_repository)
        use_case = ListCustomers(customer_repository)

        # Act
        result = use_case.execute(ListCustomersRequest(page=2, page_size=2))

        # Assert
        assert result.success is True
        assert result.data is not None
        assert result.data["page"] == 2
        assert result.data["page_size"] == 2
        assert result.data["total"] == 5
        assert len(result.data["items"]) == 2

    def test_caps_page_size_at_maximum(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        _create_customers(1, customer_repository, address_repository)
        use_case = ListCustomers(customer_repository)

        # Act
        result = use_case.execute(ListCustomersRequest(page_size=500))

        # Assert
        assert result.success is True
        assert result.data is not None
        assert result.data["page_size"] == 100
