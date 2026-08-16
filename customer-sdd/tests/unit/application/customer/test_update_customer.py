"""Pruebas unitarias del caso de uso `UpdateCustomer`."""

from __future__ import annotations

from customers.application.customer.create_customer import CreateCustomer, CreateCustomerRequest
from customers.application.customer.delete_customer import DeleteCustomer
from customers.application.customer.update_customer import UpdateCustomer, UpdateCustomerRequest
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


class TestUpdateCustomer:
    def test_updates_customer_successfully(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        use_case = UpdateCustomer(customer_repository, address_repository)
        request = UpdateCustomerRequest(
            name="Jane Updated", identification="ID-001", age=31, email="jane.updated@example.com"
        )

        # Act
        result = use_case.execute(customer_id, request)

        # Assert
        assert result.success is True
        assert result.data is not None
        assert result.data["name"] == "Jane Updated"
        assert result.data["email"] == "jane.updated@example.com"

    def test_does_not_raise_false_duplicate_when_email_unchanged(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        use_case = UpdateCustomer(customer_repository, address_repository)
        request = UpdateCustomerRequest(
            name="Jane Updated", identification="ID-001", age=31, email="jane.doe@example.com"
        )

        # Act
        result = use_case.execute(customer_id, request)

        # Assert
        assert result.success is True

    def test_does_not_raise_false_duplicate_when_identification_unchanged(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        use_case = UpdateCustomer(customer_repository, address_repository)
        request = UpdateCustomerRequest(
            name="Jane Updated", identification="ID-001", age=31, email="jane.updated@example.com"
        )

        # Act
        result = use_case.execute(customer_id, request)

        # Assert
        assert result.success is True

    def test_rejects_email_belonging_to_another_customer(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        _create_customer(
            customer_repository,
            address_repository,
            identification="ID-002",
            email="other@example.com",
        )
        use_case = UpdateCustomer(customer_repository, address_repository)
        request = UpdateCustomerRequest(
            name="Jane Updated", identification="ID-001", age=31, email="other@example.com"
        )

        # Act
        result = use_case.execute(customer_id, request)

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert any(error.code == "ERR-002" for error in result.errors)

    def test_rejects_identification_belonging_to_another_customer(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        _create_customer(
            customer_repository,
            address_repository,
            identification="ID-002",
            email="other@example.com",
        )
        use_case = UpdateCustomer(customer_repository, address_repository)
        request = UpdateCustomerRequest(
            name="Jane Updated", identification="ID-002", age=31, email="jane.doe@example.com"
        )

        # Act
        result = use_case.execute(customer_id, request)

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert any(error.code == "ERR-008" for error in result.errors)

    def test_returns_not_found_for_unknown_customer(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        use_case = UpdateCustomer(customer_repository, address_repository)
        request = UpdateCustomerRequest(
            name="Jane Doe", identification="ID-001", age=30, email="jane.doe@example.com"
        )

        # Act
        result = use_case.execute(CustomerId.generate(), request)

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert result.errors[0].code == "ERR-003"

    def test_returns_not_found_for_already_deleted_customer(self) -> None:
        """Caso límite spec §16: actualizar una entidad ya eliminada se
        comporta como no encontrada (`plan.md` §1.1)."""
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        DeleteCustomer(customer_repository, address_repository).execute(customer_id)
        use_case = UpdateCustomer(customer_repository, address_repository)
        request = UpdateCustomerRequest(
            name="Jane Updated", identification="ID-001", age=31, email="jane.updated@example.com"
        )

        # Act
        result = use_case.execute(customer_id, request)

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert result.errors[0].code == "ERR-003"
