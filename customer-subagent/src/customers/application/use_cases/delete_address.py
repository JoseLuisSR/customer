from __future__ import annotations

from datetime import UTC, datetime

from customers.domain.exceptions import AddressNotFoundError, CustomerNotFoundError
from customers.domain.repositories.address_repository import AddressRepository
from customers.domain.repositories.customer_repository import CustomerRepository


class DeleteAddressUseCase:
    def __init__(
        self,
        customer_repository: CustomerRepository,
        address_repository: AddressRepository,
    ) -> None:
        self._customer_repository = customer_repository
        self._address_repository = address_repository

    def execute(self, customer_id: int, address_id: int) -> None:
        customer = self._customer_repository.get_by_id(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)

        address = self._address_repository.get_by_id(
            customer_id, address_id, include_deleted=True
        )
        if address is None:
            raise AddressNotFoundError(address_id)

        address.mark_deleted(datetime.now(UTC))
        self._address_repository.soft_delete(address)
