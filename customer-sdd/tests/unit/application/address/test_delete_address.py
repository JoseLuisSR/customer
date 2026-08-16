"""Pruebas unitarias del caso de uso `DeleteAddress`."""

from __future__ import annotations

from customers.application.address.create_address import CreateAddress, CreateAddressRequest
from customers.application.address.delete_address import DeleteAddress
from customers.application.customer.create_customer import CreateCustomer, CreateCustomerRequest
from customers.domain.address.value_objects import AddressId
from customers.domain.customer.value_objects import CustomerId
from customers.domain.shared.status import EntityStatus

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


class TestDeleteAddress:
    def test_deletes_address_successfully(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        address_id = _create_address(customer_id, customer_repository, address_repository)
        use_case = DeleteAddress(customer_repository, address_repository)

        # Act
        result = use_case.execute(customer_id, address_id)

        # Assert
        assert result.success is True
        assert result.entity_status is EntityStatus.DELETED
        assert address_repository.get_by_id(address_id) is None

    def test_returns_not_found_for_unknown_address(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        use_case = DeleteAddress(customer_repository, address_repository)

        # Act
        result = use_case.execute(customer_id, AddressId.generate())

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
        use_case = DeleteAddress(customer_repository, address_repository)

        # Act
        result = use_case.execute(customer_id, address_id)

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert result.errors[0].code == "ERR-006"

    def test_returns_not_found_for_repeated_deletion_of_already_deleted_address(self) -> None:
        """Caso límite spec §16: eliminar dos veces la misma dirección se
        comporta como no encontrada en el segundo intento (`plan.md` §1.1)."""
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        customer_id = _create_customer(customer_repository, address_repository)
        address_id = _create_address(customer_id, customer_repository, address_repository)
        use_case = DeleteAddress(customer_repository, address_repository)
        first_result = use_case.execute(customer_id, address_id)
        assert first_result.success is True

        # Act
        second_result = use_case.execute(customer_id, address_id)

        # Assert
        assert second_result.success is False
        assert second_result.errors is not None
        assert second_result.errors[0].code == "ERR-004"
