import pytest

from customers.application.dtos.customer_dto import CreateCustomerInput
from customers.application.use_cases.create_customer import CreateCustomerUseCase
from customers.domain.exceptions import (
    CustomerEmailAlreadyExistsError,
    CustomerValidationError,
)


def test_creates_customer_and_assigns_id(repository):
    use_case = CreateCustomerUseCase(repository)

    output = use_case.execute(
        CreateCustomerInput(name="Ada Lovelace", age=30, email="ada@example.com")
    )

    assert output.id == 1
    assert output.name == "Ada Lovelace"
    assert output.age == 30
    assert output.email == "ada@example.com"


def test_persists_customer_so_it_can_be_retrieved(repository):
    use_case = CreateCustomerUseCase(repository)

    output = use_case.execute(
        CreateCustomerInput(name="Ada Lovelace", age=30, email="ada@example.com")
    )

    stored = repository.get_by_id(output.id)
    assert stored is not None
    assert stored.email == "ada@example.com"


def test_propagates_validation_error_from_entity(repository):
    use_case = CreateCustomerUseCase(repository)

    with pytest.raises(CustomerValidationError) as exc_info:
        use_case.execute(CreateCustomerInput(name="", age=30, email="ada@example.com"))

    assert exc_info.value.field == "name"


def test_rejects_duplicate_email(repository):
    use_case = CreateCustomerUseCase(repository)
    use_case.execute(
        CreateCustomerInput(name="Ada Lovelace", age=30, email="ada@example.com")
    )

    with pytest.raises(CustomerEmailAlreadyExistsError):
        use_case.execute(
            CreateCustomerInput(name="Grace Hopper", age=40, email="ada@example.com")
        )
