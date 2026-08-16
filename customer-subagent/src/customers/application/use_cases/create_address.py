from __future__ import annotations

from customers.application.dtos.address_dto import AddressOutput, CreateAddressInput
from customers.domain.entities.address import Address
from customers.domain.exceptions import CustomerNotFoundError
from customers.domain.repositories.address_repository import AddressRepository
from customers.domain.repositories.customer_repository import CustomerRepository


class CreateAddressUseCase:
    def __init__(
        self,
        customer_repository: CustomerRepository,
        address_repository: AddressRepository,
    ) -> None:
        self._customer_repository = customer_repository
        self._address_repository = address_repository

    def execute(self, input_dto: CreateAddressInput) -> AddressOutput:
        customer = self._customer_repository.get_by_id(input_dto.customer_id)
        if customer is None:
            raise CustomerNotFoundError(input_dto.customer_id)

        address = Address(
            customer_id=input_dto.customer_id,
            country=input_dto.country,
            state=input_dto.state,
            city=input_dto.city,
            postal_code=input_dto.postal_code,
            address_line=input_dto.address_line,
        )
        created = self._address_repository.add(address)
        return AddressOutput.from_entity(created)
