from __future__ import annotations

from customers.application.dtos.address_dto import AddressOutput
from customers.domain.exceptions import CustomerNotFoundError
from customers.domain.repositories.address_repository import AddressRepository
from customers.domain.repositories.customer_repository import CustomerRepository


class ListAddressesUseCase:
    def __init__(
        self,
        customer_repository: CustomerRepository,
        address_repository: AddressRepository,
    ) -> None:
        self._customer_repository = customer_repository
        self._address_repository = address_repository

    def execute(self, customer_id: int) -> list[AddressOutput]:
        customer = self._customer_repository.get_by_id(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)

        addresses = self._address_repository.list_active_by_customer(customer_id)
        return [AddressOutput.from_entity(address) for address in addresses]
