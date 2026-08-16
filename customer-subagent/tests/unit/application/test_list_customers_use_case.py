from customers.application.dtos.customer_dto import CreateCustomerInput
from customers.application.use_cases.create_customer import CreateCustomerUseCase
from customers.application.use_cases.delete_customer import DeleteCustomerUseCase
from customers.application.use_cases.list_customers import ListCustomersUseCase


def test_returns_empty_list_when_no_customers(repository):
    use_case = ListCustomersUseCase(repository)

    assert use_case.execute() == []


def test_returns_all_active_customers(repository):
    create = CreateCustomerUseCase(repository)
    create.execute(
        CreateCustomerInput(name="Ada Lovelace", age=30, email="ada@example.com")
    )
    create.execute(
        CreateCustomerInput(name="Grace Hopper", age=40, email="grace@example.com")
    )

    use_case = ListCustomersUseCase(repository)
    outputs = use_case.execute()

    assert {output.email for output in outputs} == {
        "ada@example.com",
        "grace@example.com",
    }


def test_excludes_soft_deleted_customers(repository):
    create = CreateCustomerUseCase(repository)
    active = create.execute(
        CreateCustomerInput(name="Ada Lovelace", age=30, email="ada@example.com")
    )
    deleted = create.execute(
        CreateCustomerInput(name="Grace Hopper", age=40, email="grace@example.com")
    )
    DeleteCustomerUseCase(repository).execute(deleted.id)

    use_case = ListCustomersUseCase(repository)
    outputs = use_case.execute()

    assert [output.id for output in outputs] == [active.id]
