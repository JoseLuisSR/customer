"""Pruebas unitarias del caso de uso `UpdateAddress`."""

from __future__ import annotations

from customers.application.address.create_address import CreateAddress, CreateAddressRequest
from customers.application.address.delete_address import DeleteAddress
from customers.application.address.update_address import UpdateAddress, UpdateAddressRequest
from customers.application.customer.create_customer import CreateCustomer, CreateCustomerRequest
from customers.domain.address.value_objects import AddressId
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


def _create_address(
    customer_id: CustomerId,
    customer_repository: FakeCustomerRepository,
    address_repository: FakeAddressRepository,
) -> AddressId:
    create_address_use_case = CreateAddress(customer_repository, address_repository)
    result = create_address_use_case.execute(
        customer_id,
        CreateAddressRequest(
            country="Colombia",
            state="Bogotá D.C.",
            city="Bogotá",
            address="Calle 1 # 2-3",
            postal_code="110111",
        ),
    )
    assert result.data is not None
    return AddressId.from_string(result.data["id"])


class TestUpdateAddress:
    def test_updates_address_successfully(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        address_id = _create_address(customer_id, customer_repository, address_repository)
        use_case = UpdateAddress(customer_repository, address_repository)
        request = UpdateAddressRequest(
            country="Colombia",
            state="Antioquia",
            city="Medellín",
            address="Carrera 50 # 10-20",
            postal_code="050001",
        )

        # Act
        result = use_case.execute(customer_id, address_id, request)

        # Assert
        assert result.success is True
        assert result.data is not None
        assert result.data["city"] == "Medellín"

    def test_returns_not_found_for_unknown_address(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        use_case = UpdateAddress(customer_repository, address_repository)
        request = UpdateAddressRequest(
            country="Colombia",
            state="Antioquia",
            city="Medellín",
            address="Carrera 50 # 10-20",
            postal_code="050001",
        )

        # Act
        result = use_case.execute(customer_id, AddressId.generate(), request)

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert result.errors[0].code == "ERR-004"

    def test_rejects_address_belonging_to_another_customer(self) -> None:
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
        address_id = _create_address(other_customer_id, customer_repository, address_repository)
        use_case = UpdateAddress(customer_repository, address_repository)
        request = UpdateAddressRequest(
            country="Colombia",
            state="Antioquia",
            city="Medellín",
            address="Carrera 50 # 10-20",
            postal_code="050001",
        )

        # Act
        result = use_case.execute(customer_id, address_id, request)

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert result.errors[0].code == "ERR-006"

    def test_returns_not_found_for_already_deleted_address(self) -> None:
        """Caso límite spec §16: actualizar una dirección ya eliminada se
        comporta como no encontrada (`plan.md` §1.1)."""
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        address_id = _create_address(customer_id, customer_repository, address_repository)
        DeleteAddress(customer_repository, address_repository).execute(customer_id, address_id)
        use_case = UpdateAddress(customer_repository, address_repository)
        request = UpdateAddressRequest(
            country="Colombia",
            state="Antioquia",
            city="Medellín",
            address="Carrera 50 # 10-20",
            postal_code="050001",
        )

        # Act
        result = use_case.execute(customer_id, address_id, request)

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert result.errors[0].code == "ERR-004"
