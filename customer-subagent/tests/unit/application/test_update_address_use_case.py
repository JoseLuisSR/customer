import pytest

from customers.application.dtos.address_dto import (
    CreateAddressInput,
    UpdateAddressInput,
)
from customers.application.dtos.customer_dto import CreateCustomerInput
from customers.application.use_cases.create_address import CreateAddressUseCase
from customers.application.use_cases.create_customer import CreateCustomerUseCase
from customers.application.use_cases.update_address import UpdateAddressUseCase
from customers.domain.exceptions import (
    AddressNotFoundError,
    AddressValidationError,
    CustomerNotFoundError,
)


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


def test_updates_only_provided_fields(repository, address_repository):
    customer = create_customer(repository)
    created = create_address(repository, address_repository, customer.id)

    output = UpdateAddressUseCase(repository, address_repository).execute(
        UpdateAddressInput(
            customer_id=customer.id, address_id=created.id, city="Bogota"
        )
    )

    assert output.city == "Bogota"
    assert output.country == created.country
    assert output.postal_code == created.postal_code


def test_updates_all_fields(repository, address_repository):
    customer = create_customer(repository)
    created = create_address(repository, address_repository, customer.id)

    output = UpdateAddressUseCase(repository, address_repository).execute(
        UpdateAddressInput(
            customer_id=customer.id,
            address_id=created.id,
            country="Argentina",
            state="Cordoba",
            city="Cordoba",
            postal_code="5000",
            address_line="Av. Colon 100",
        )
    )

    assert output.country == "Argentina"
    assert output.state == "Cordoba"
    assert output.city == "Cordoba"
    assert output.postal_code == "5000"
    assert output.address_line == "Av. Colon 100"


def test_raises_when_no_fields_to_update(repository, address_repository):
    customer = create_customer(repository)
    created = create_address(repository, address_repository, customer.id)

    with pytest.raises(AddressValidationError) as exc_info:
        UpdateAddressUseCase(repository, address_repository).execute(
            UpdateAddressInput(customer_id=customer.id, address_id=created.id)
        )

    assert exc_info.value.field == "body"


def test_raises_when_body_id_does_not_match_url_id(repository, address_repository):
    customer = create_customer(repository)
    created = create_address(repository, address_repository, customer.id)

    with pytest.raises(AddressValidationError) as exc_info:
        UpdateAddressUseCase(repository, address_repository).execute(
            UpdateAddressInput(
                customer_id=customer.id,
                address_id=created.id,
                city="Bogota",
                body_id=created.id + 1,
            )
        )

    assert exc_info.value.field == "id"


def test_accepts_matching_body_id(repository, address_repository):
    customer = create_customer(repository)
    created = create_address(repository, address_repository, customer.id)

    output = UpdateAddressUseCase(repository, address_repository).execute(
        UpdateAddressInput(
            customer_id=customer.id,
            address_id=created.id,
            city="Bogota",
            body_id=created.id,
        )
    )

    assert output.city == "Bogota"


def test_raises_when_customer_does_not_exist(repository, address_repository):
    with pytest.raises(CustomerNotFoundError):
        UpdateAddressUseCase(repository, address_repository).execute(
            UpdateAddressInput(customer_id=999, address_id=1, city="Bogota")
        )


def test_raises_when_address_does_not_exist(repository, address_repository):
    customer = create_customer(repository)

    with pytest.raises(AddressNotFoundError):
        UpdateAddressUseCase(repository, address_repository).execute(
            UpdateAddressInput(customer_id=customer.id, address_id=999, city="Bogota")
        )


def test_raises_when_address_belongs_to_another_customer(
    repository, address_repository
):
    customer_a = create_customer(repository)
    customer_b = create_customer(repository, email="grace@example.com")
    address_of_b = create_address(repository, address_repository, customer_b.id)

    with pytest.raises(AddressNotFoundError):
        UpdateAddressUseCase(repository, address_repository).execute(
            UpdateAddressInput(
                customer_id=customer_a.id, address_id=address_of_b.id, city="Bogota"
            )
        )


def test_propagates_field_validation_error(repository, address_repository):
    customer = create_customer(repository)
    created = create_address(repository, address_repository, customer.id)

    with pytest.raises(AddressValidationError) as exc_info:
        UpdateAddressUseCase(repository, address_repository).execute(
            UpdateAddressInput(customer_id=customer.id, address_id=created.id, city="")
        )

    assert exc_info.value.field == "city"
