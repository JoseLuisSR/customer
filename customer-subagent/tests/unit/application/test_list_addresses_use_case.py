import pytest

from customers.application.dtos.address_dto import CreateAddressInput
from customers.application.dtos.customer_dto import CreateCustomerInput
from customers.application.use_cases.create_address import CreateAddressUseCase
from customers.application.use_cases.create_customer import CreateCustomerUseCase
from customers.application.use_cases.delete_address import DeleteAddressUseCase
from customers.application.use_cases.list_addresses import ListAddressesUseCase
from customers.domain.exceptions import CustomerNotFoundError


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


def test_returns_empty_list_when_no_addresses(repository, address_repository):
    customer = create_customer(repository)
    use_case = ListAddressesUseCase(repository, address_repository)

    assert use_case.execute(customer.id) == []


def test_returns_all_addresses_for_customer(repository, address_repository):
    customer = create_customer(repository)
    create_address(repository, address_repository, customer.id, city="Villavicencio")
    create_address(repository, address_repository, customer.id, city="Bogota")

    use_case = ListAddressesUseCase(repository, address_repository)
    outputs = use_case.execute(customer.id)

    assert {output.city for output in outputs} == {"Villavicencio", "Bogota"}


def test_excludes_soft_deleted_addresses(repository, address_repository):
    customer = create_customer(repository)
    active = create_address(repository, address_repository, customer.id)
    deleted = create_address(repository, address_repository, customer.id, city="Bogota")
    DeleteAddressUseCase(repository, address_repository).execute(
        customer.id, deleted.id
    )

    use_case = ListAddressesUseCase(repository, address_repository)
    outputs = use_case.execute(customer.id)

    assert [output.id for output in outputs] == [active.id]


def test_excludes_addresses_from_other_customers(repository, address_repository):
    customer_a = create_customer(repository)
    customer_b = create_customer(repository, email="grace@example.com")
    create_address(repository, address_repository, customer_a.id)
    create_address(repository, address_repository, customer_b.id, city="Bogota")

    use_case = ListAddressesUseCase(repository, address_repository)
    outputs = use_case.execute(customer_a.id)

    assert len(outputs) == 1


def test_raises_when_customer_does_not_exist(repository, address_repository):
    use_case = ListAddressesUseCase(repository, address_repository)

    with pytest.raises(CustomerNotFoundError):
        use_case.execute(999)
