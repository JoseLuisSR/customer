from __future__ import annotations

from customers.application.dtos.customer_dto import CustomerOutput
from customers.domain.exceptions import CustomerNotFoundError
from customers.domain.repositories.customer_repository import CustomerRepository


class GetCustomerUseCase:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def execute(self, customer_id: int) -> CustomerOutput:
        customer = self._repository.get_by_id(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)
        return CustomerOutput.from_entity(customer)
