import pytest

from customers.application.dtos.customer_dto import CreateCustomerInput
from customers.application.use_cases.create_customer import CreateCustomerUseCase
from customers.application.use_cases.delete_customer import DeleteCustomerUseCase
from customers.application.use_cases.get_customer import GetCustomerUseCase
from customers.domain.exceptions import (
    CustomerAlreadyDeletedError,
    CustomerNotFoundError,
)


def create_customer(repository):
    return CreateCustomerUseCase(repository).execute(
        CreateCustomerInput(name="Ada Lovelace", age=30, email="ada@example.com")
    )


def test_soft_deletes_customer(repository):
    created = create_customer(repository)

    DeleteCustomerUseCase(repository).execute(created.id)

    with pytest.raises(CustomerNotFoundError):
        GetCustomerUseCase(repository).execute(created.id)

    stored = repository.get_by_id(created.id, include_deleted=True)
    assert stored.is_deleted() is True


def test_raises_not_found_for_unknown_id(repository):
    with pytest.raises(CustomerNotFoundError):
        DeleteCustomerUseCase(repository).execute(999)


def test_raises_when_already_deleted(repository):
    created = create_customer(repository)
    DeleteCustomerUseCase(repository).execute(created.id)

    with pytest.raises(CustomerAlreadyDeletedError):
        DeleteCustomerUseCase(repository).execute(created.id)
