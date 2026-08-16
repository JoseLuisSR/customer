"""Pruebas unitarias del caso de uso `DeleteCustomer`."""

from __future__ import annotations

from customers.application.address.support import AddressFieldsPayload
from customers.application.customer.create_customer import CreateCustomer, CreateCustomerRequest
from customers.application.customer.delete_customer import DeleteCustomer
from customers.domain.customer.value_objects import CustomerId
from customers.domain.shared.status import EntityStatus

from ..fakes import FakeAddressRepository, FakeCustomerRepository


class TestDeleteCustomer:
    def test_deletes_customer_successfully(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        create_use_case = CreateCustomer(customer_repository, address_repository)
        created = create_use_case.execute(
            CreateCustomerRequest(
                name="Jane Doe",
                identification="ID-001",
                age=30,
                email="jane.doe@example.com",
                addresses=[],
            )
        )
        assert created.data is not None
        customer_id = CustomerId.from_string(created.data["id"])
        use_case = DeleteCustomer(customer_repository, address_repository)

        # Act
        result = use_case.execute(customer_id)

        # Assert
        assert result.success is True
        assert result.entity_status is EntityStatus.DELETED
        assert customer_repository.get_by_id(customer_id) is None

    def test_deletes_associated_addresses_instead_of_orphaning_them(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        create_use_case = CreateCustomer(customer_repository, address_repository)
        address_payload = AddressFieldsPayload(
            country="Colombia",
            state="Bogotá D.C.",
            city="Bogotá",
            address="Calle 1 # 2-3",
            postal_code="110111",
        )
        created = create_use_case.execute(
            CreateCustomerRequest(
                name="Jane Doe",
                identification="ID-001",
                age=30,
                email="jane.doe@example.com",
                addresses=[address_payload, address_payload],
            )
        )
        assert created.data is not None
        customer_id = CustomerId.from_string(created.data["id"])
        use_case = DeleteCustomer(customer_repository, address_repository)

        # Act
        use_case.execute(customer_id)

        # Assert
        assert address_repository.list_by_customer(customer_id) == []
        all_addresses = address_repository.list_by_customer(customer_id, include_deleted=True)
        assert len(all_addresses) == 2
        assert all(address.status is EntityStatus.DELETED for address in all_addresses)

    def test_returns_not_found_for_unknown_customer(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        use_case = DeleteCustomer(customer_repository, address_repository)

        # Act
        result = use_case.execute(CustomerId.generate())

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert result.errors[0].code == "ERR-003"

    def test_returns_not_found_for_repeated_deletion_of_already_deleted_customer(self) -> None:
        """Caso límite spec §16: eliminar dos veces la misma entidad se
        comporta como no encontrada en el segundo intento (`plan.md` §1.1)."""
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        create_use_case = CreateCustomer(customer_repository, address_repository)
        created = create_use_case.execute(
            CreateCustomerRequest(
                name="Jane Doe",
                identification="ID-001",
                age=30,
                email="jane.doe@example.com",
                addresses=[],
            )
        )
        assert created.data is not None
        customer_id = CustomerId.from_string(created.data["id"])
        use_case = DeleteCustomer(customer_repository, address_repository)
        first_result = use_case.execute(customer_id)
        assert first_result.success is True

        # Act
        second_result = use_case.execute(customer_id)

        # Assert
        assert second_result.success is False
        assert second_result.errors is not None
        assert second_result.errors[0].code == "ERR-003"
