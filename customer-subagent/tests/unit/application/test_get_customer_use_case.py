import pytest

from customers.application.dtos.customer_dto import CreateCustomerInput
from customers.application.use_cases.create_customer import CreateCustomerUseCase
from customers.application.use_cases.delete_customer import DeleteCustomerUseCase
from customers.application.use_cases.get_customer import GetCustomerUseCase
from customers.domain.exceptions import CustomerNotFoundError


def test_returns_existing_customer(repository):
    created = CreateCustomerUseCase(repository).execute(
        CreateCustomerInput(name="Ada Lovelace", age=30, email="ada@example.com")
    )

    output = GetCustomerUseCase(repository).execute(created.id)

    assert output == created


def test_raises_not_found_for_unknown_id(repository):
    with pytest.raises(CustomerNotFoundError) as exc_info:
        GetCustomerUseCase(repository).execute(999)

    assert exc_info.value.customer_id == 999


def test_raises_not_found_for_soft_deleted_customer(repository):
    created = CreateCustomerUseCase(repository).execute(
        CreateCustomerInput(name="Ada Lovelace", age=30, email="ada@example.com")
    )
    DeleteCustomerUseCase(repository).execute(created.id)

    with pytest.raises(CustomerNotFoundError):
        GetCustomerUseCase(repository).execute(created.id)
