"""Pruebas unitarias del caso de uso `CreateCustomer`."""

from __future__ import annotations

from customers.application.address.support import AddressFieldsPayload
from customers.application.customer.create_customer import CreateCustomer, CreateCustomerRequest
from customers.domain.shared.status import EntityStatus

from ..fakes import FakeAddressRepository, FakeCustomerRepository


def _address_payload(
    country: str = "Colombia",
    state: str = "Bogotá D.C.",
    city: str = "Bogotá",
    address: str = "Calle 1 # 2-3",
    postal_code: str = "110111",
) -> AddressFieldsPayload:
    return AddressFieldsPayload(
        country=country, state=state, city=city, address=address, postal_code=postal_code
    )


def _customer_request(
    name: str = "Jane Doe",
    identification: str = "ID-001",
    age: int = 30,
    email: str = "jane.doe@example.com",
    addresses: list[AddressFieldsPayload] | None = None,
) -> CreateCustomerRequest:
    return CreateCustomerRequest(
        name=name,
        identification=identification,
        age=age,
        email=email,
        addresses=addresses if addresses is not None else [],
    )


class TestCreateCustomer:
    def test_creates_customer_without_addresses(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        use_case = CreateCustomer(customer_repository, address_repository)
        request = _customer_request()

        # Act
        result = use_case.execute(request)

        # Assert
        assert result.success is True
        assert result.entity_status is EntityStatus.ACTIVE
        assert result.data is not None
        assert result.data["email"] == "jane.doe@example.com"
        assert result.data["addresses"] == []
        assert result.data["created_at"] is not None
        assert result.data["updated_at"] is not None
        assert len(customer_repository.all()) == 1

    def test_creates_customer_with_up_to_five_addresses(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        use_case = CreateCustomer(customer_repository, address_repository)
        request = _customer_request(addresses=[_address_payload() for _ in range(5)])

        # Act
        result = use_case.execute(request)

        # Assert
        assert result.success is True
        assert result.data is not None
        assert len(result.data["addresses"]) == 5
        assert all(address["created_at"] is not None for address in result.data["addresses"])
        assert all(address["updated_at"] is not None for address in result.data["addresses"])
        assert len(address_repository.all()) == 5

    def test_rejects_more_than_five_addresses_without_creating_anything(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        use_case = CreateCustomer(customer_repository, address_repository)
        request = _customer_request(addresses=[_address_payload() for _ in range(6)])

        # Act
        result = use_case.execute(request)

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert any(error.code == "ERR-005" for error in result.errors)
        assert customer_repository.all() == []
        assert address_repository.all() == []

    def test_rejects_duplicate_email(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        use_case = CreateCustomer(customer_repository, address_repository)
        use_case.execute(_customer_request())

        # Act
        result = use_case.execute(
            _customer_request(identification="ID-002", email="jane.doe@example.com")
        )

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert any(error.code == "ERR-002" and error.field == "email" for error in result.errors)
        assert len(customer_repository.all()) == 1

    def test_rejects_duplicate_email_with_different_casing_and_whitespace(self) -> None:
        """Caso límite spec §16: correo con diferencias de mayúsculas/minúsculas
        y espacios debe detectarse como el mismo correo ya registrado
        (`Email` normaliza `trim`+`lower` antes de comparar, `plan.md` §1.1)."""
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        use_case = CreateCustomer(customer_repository, address_repository)
        use_case.execute(_customer_request(email="jane.doe@example.com"))

        # Act
        result = use_case.execute(
            _customer_request(identification="ID-002", email="  Jane.Doe@Example.com  ")
        )

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert any(error.code == "ERR-002" and error.field == "email" for error in result.errors)
        assert len(customer_repository.all()) == 1

    def test_rejects_duplicate_identification(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        use_case = CreateCustomer(customer_repository, address_repository)
        use_case.execute(_customer_request())

        # Act
        result = use_case.execute(
            _customer_request(identification="ID-001", email="other@example.com")
        )

        # Assert
        assert result.success is False
        assert result.errors is not None
        assert any(
            error.code == "ERR-008" and error.field == "identification" for error in result.errors
        )
        assert len(customer_repository.all()) == 1

    def test_accumulates_all_invalid_field_errors(self) -> None:
        # Arrange
        customer_repository = FakeCustomerRepository()
        address_repository = FakeAddressRepository()
        use_case = CreateCustomer(customer_repository, address_repository)
        request = _customer_request(name="   ", identification="", age=-1, email="not-an-email")

        # Act
        result = use_case.execute(request)

        # Assert
        assert result.success is False
        assert result.errors is not None
        codes = {error.code for error in result.errors}
        assert codes == {"VAL-001", "VAL-003", "VAL-004", "VAL-005"}
        assert customer_repository.all() == []
