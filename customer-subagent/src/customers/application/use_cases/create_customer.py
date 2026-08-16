from __future__ import annotations

from customers.application.dtos.customer_dto import CreateCustomerInput, CustomerOutput
from customers.domain.entities.customer import Customer
from customers.domain.repositories.customer_repository import CustomerRepository


class CreateCustomerUseCase:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def execute(self, input_dto: CreateCustomerInput) -> CustomerOutput:
        customer = Customer(
            name=input_dto.name, age=input_dto.age, email=input_dto.email
        )
        created = self._repository.add(customer)
        return CustomerOutput.from_entity(created)
