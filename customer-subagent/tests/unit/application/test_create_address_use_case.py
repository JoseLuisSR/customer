import pytest

from customers.application.dtos.address_dto import CreateAddressInput
from customers.application.dtos.customer_dto import CreateCustomerInput
from customers.application.use_cases.create_address import CreateAddressUseCase
from customers.application.use_cases.create_customer import CreateCustomerUseCase
from customers.application.use_cases.delete_customer import DeleteCustomerUseCase
from customers.domain.exceptions import AddressValidationError, CustomerNotFoundError


def create_customer(repository, **overrides):
    fields = {"name": "Ada Lovelace", "age": 30, "email": "ada@example.com"}
    fields.update(overrides)
    return CreateCustomerUseCase(repository).execute(CreateCustomerInput(**fields))


def valid_address_input(customer_id, **overrides):
    fields = {
        "customer_id": customer_id,
        "country": "Colombia",
        "state": "Meta",
        "city": "Villavicencio",
        "postal_code": "50001",
        "address_line": "Calle 10 #5-20",
    }
    fields.update(overrides)
    return CreateAddressInput(**fields)


def test_creates_address_for_existing_customer(repository, address_repository):
    customer = create_customer(repository)
    use_case = CreateAddressUseCase(repository, address_repository)

    output = use_case.execute(valid_address_input(customer.id))

    assert output.id == 1
    assert output.country == "Colombia"
    assert output.postal_code == "50001"
    assert output.address_line == "Calle 10 #5-20"


def test_raises_when_customer_does_not_exist(repository, address_repository):
    use_case = CreateAddressUseCase(repository, address_repository)

    with pytest.raises(CustomerNotFoundError) as exc_info:
        use_case.execute(valid_address_input(999))

    assert exc_info.value.customer_id == 999


def test_raises_when_customer_is_soft_deleted(repository, address_repository):
    customer = create_customer(repository)
    DeleteCustomerUseCase(repository).execute(customer.id)
    use_case = CreateAddressUseCase(repository, address_repository)

    with pytest.raises(CustomerNotFoundError):
        use_case.execute(valid_address_input(customer.id))


def test_propagates_field_validation_error(repository, address_repository):
    customer = create_customer(repository)
    use_case = CreateAddressUseCase(repository, address_repository)

    with pytest.raises(AddressValidationError) as exc_info:
        use_case.execute(valid_address_input(customer.id, country=""))

    assert exc_info.value.field == "country"
