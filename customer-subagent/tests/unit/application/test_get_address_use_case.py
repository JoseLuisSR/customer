import pytest

from customers.application.dtos.address_dto import CreateAddressInput
from customers.application.dtos.customer_dto import CreateCustomerInput
from customers.application.use_cases.create_address import CreateAddressUseCase
from customers.application.use_cases.create_customer import CreateCustomerUseCase
from customers.application.use_cases.delete_address import DeleteAddressUseCase
from customers.application.use_cases.get_address import GetAddressUseCase
from customers.domain.exceptions import AddressNotFoundError, CustomerNotFoundError


def create_customer(repository, **overrides):
    fields = {"name": "Ada Lovelace", "age": 30, "email": "ada@example.com"}
    fields.update(overrides)
    return CreateCustomerUseCase(repository).execute(CreateCustomerInput(**fields))


def create_address(repository, address_repository, customer_id, **overrides):
    fields = {
        "customer_id": customer_id,
        "country": "Colombia",
        "state": "Meta",
        "city": "Villavicencio",
        "postal_code": "50001",
        "address_line": "Calle 10 #5-20",
    }
    fields.update(overrides)
    return CreateAddressUseCase(repository, address_repository).execute(
        CreateAddressInput(**fields)
    )


def test_returns_existing_address(repository, address_repository):
    customer = create_customer(repository)
    created = create_address(repository, address_repository, customer.id)

    output = GetAddressUseCase(repository, address_repository).execute(
        customer.id, created.id
    )

    assert output == created


def test_raises_when_customer_does_not_exist(repository, address_repository):
    with pytest.raises(CustomerNotFoundError):
        GetAddressUseCase(repository, address_repository).execute(999, 1)


def test_raises_when_address_does_not_exist(repository, address_repository):
    customer = create_customer(repository)

    with pytest.raises(AddressNotFoundError) as exc_info:
        GetAddressUseCase(repository, address_repository).execute(customer.id, 999)

    assert exc_info.value.address_id == 999


def test_raises_when_address_is_soft_deleted(repository, address_repository):
    customer = create_customer(repository)
    created = create_address(repository, address_repository, customer.id)
    DeleteAddressUseCase(repository, address_repository).execute(
        customer.id, created.id
    )

    with pytest.raises(AddressNotFoundError):
        GetAddressUseCase(repository, address_repository).execute(
            customer.id, created.id
        )


def test_raises_when_address_belongs_to_another_customer(
    repository, address_repository
):
    customer_a = create_customer(repository)
    customer_b = create_customer(repository, email="grace@example.com")
    address_of_b = create_address(repository, address_repository, customer_b.id)

    with pytest.raises(AddressNotFoundError):
        GetAddressUseCase(repository, address_repository).execute(
            customer_a.id, address_of_b.id
        )
