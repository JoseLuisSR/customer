from __future__ import annotations

from customers.application.dtos.customer_dto import CustomerOutput
from customers.domain.repositories.customer_repository import CustomerRepository


class ListCustomersUseCase:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def execute(self) -> list[CustomerOutput]:
        customers = self._repository.list_active()
        return [CustomerOutput.from_entity(customer) for customer in customers]
