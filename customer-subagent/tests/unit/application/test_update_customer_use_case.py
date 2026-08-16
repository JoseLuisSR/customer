import pytest

from customers.application.dtos.customer_dto import (
    CreateCustomerInput,
    UpdateCustomerInput,
)
from customers.application.use_cases.create_customer import CreateCustomerUseCase
from customers.application.use_cases.update_customer import UpdateCustomerUseCase
from customers.domain.exceptions import (
    CustomerEmailAlreadyExistsError,
    CustomerNotFoundError,
    CustomerValidationError,
)


def create_customer(repository, **overrides):
    fields = {"name": "Ada Lovelace", "age": 30, "email": "ada@example.com"}
    fields.update(overrides)
    return CreateCustomerUseCase(repository).execute(CreateCustomerInput(**fields))


def test_updates_only_provided_fields(repository):
    created = create_customer(repository)

    output = UpdateCustomerUseCase(repository).execute(
        UpdateCustomerInput(customer_id=created.id, name="Ada Byron")
    )

    assert output.name == "Ada Byron"
    assert output.age == created.age
    assert output.email == created.email


def test_updates_all_fields(repository):
    created = create_customer(repository)

    output = UpdateCustomerUseCase(repository).execute(
        UpdateCustomerInput(
            customer_id=created.id,
            name="Ada Byron",
            age=31,
            email="ada.byron@example.com",
        )
    )

    assert output.name == "Ada Byron"
    assert output.age == 31
    assert output.email == "ada.byron@example.com"


def test_raises_when_no_fields_to_update(repository):
    created = create_customer(repository)

    with pytest.raises(CustomerValidationError) as exc_info:
        UpdateCustomerUseCase(repository).execute(
            UpdateCustomerInput(customer_id=created.id)
        )

    assert exc_info.value.field == "body"


def test_raises_when_body_id_does_not_match_url_id(repository):
    created = create_customer(repository)

    with pytest.raises(CustomerValidationError) as exc_info:
        UpdateCustomerUseCase(repository).execute(
            UpdateCustomerInput(
                customer_id=created.id, name="Ada Byron", body_id=created.id + 1
            )
        )

    assert exc_info.value.field == "id"


def test_accepts_matching_body_id(repository):
    created = create_customer(repository)

    output = UpdateCustomerUseCase(repository).execute(
        UpdateCustomerInput(
            customer_id=created.id, name="Ada Byron", body_id=created.id
        )
    )

    assert output.name == "Ada Byron"


def test_raises_not_found_for_unknown_id(repository):
    with pytest.raises(CustomerNotFoundError):
        UpdateCustomerUseCase(repository).execute(
            UpdateCustomerInput(customer_id=999, name="Ada Byron")
        )


def test_propagates_field_validation_error(repository):
    created = create_customer(repository)

    with pytest.raises(CustomerValidationError) as exc_info:
        UpdateCustomerUseCase(repository).execute(
            UpdateCustomerInput(customer_id=created.id, age=-1)
        )

    assert exc_info.value.field == "age"


def test_rejects_email_already_used_by_another_customer(repository):
    create_customer(repository, email="ada@example.com")
    other = create_customer(repository, name="Grace Hopper", email="grace@example.com")

    with pytest.raises(CustomerEmailAlreadyExistsError):
        UpdateCustomerUseCase(repository).execute(
            UpdateCustomerInput(customer_id=other.id, email="ada@example.com")
        )
