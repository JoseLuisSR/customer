from __future__ import annotations

from datetime import UTC, datetime

from customers.domain.exceptions import CustomerNotFoundError
from customers.domain.repositories.customer_repository import CustomerRepository


class DeleteCustomerUseCase:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def execute(self, customer_id: int) -> None:
        customer = self._repository.get_by_id(customer_id, include_deleted=True)
        if customer is None:
            raise CustomerNotFoundError(customer_id)

        customer.mark_deleted(datetime.now(UTC))
        self._repository.soft_delete(customer)
