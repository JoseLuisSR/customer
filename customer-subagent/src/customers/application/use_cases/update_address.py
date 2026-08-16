from __future__ import annotations

from customers.application.dtos.address_dto import AddressOutput, UpdateAddressInput
from customers.domain.exceptions import (
    AddressNotFoundError,
    AddressValidationError,
    CustomerNotFoundError,
)
from customers.domain.repositories.address_repository import AddressRepository
from customers.domain.repositories.customer_repository import CustomerRepository


class UpdateAddressUseCase:
    def __init__(
        self,
        customer_repository: CustomerRepository,
        address_repository: AddressRepository,
    ) -> None:
        self._customer_repository = customer_repository
        self._address_repository = address_repository

    def execute(self, input_dto: UpdateAddressInput) -> AddressOutput:
        self._validate_body_id_matches_url(input_dto)
        self._validate_has_fields_to_update(input_dto)

        customer = self._customer_repository.get_by_id(input_dto.customer_id)
        if customer is None:
            raise CustomerNotFoundError(input_dto.customer_id)

        address = self._address_repository.get_by_id(
            input_dto.customer_id, input_dto.address_id
        )
        if address is None:
            raise AddressNotFoundError(input_dto.address_id)

        if input_dto.country is not None:
            address.update_country(input_dto.country)
        if input_dto.state is not None:
            address.update_state(input_dto.state)
        if input_dto.city is not None:
            address.update_city(input_dto.city)
        if input_dto.postal_code is not None:
            address.update_postal_code(input_dto.postal_code)
        if input_dto.address_line is not None:
            address.update_address_line(input_dto.address_line)

        updated = self._address_repository.update(address)
        return AddressOutput.from_entity(updated)

    @staticmethod
    def _validate_body_id_matches_url(input_dto: UpdateAddressInput) -> None:
        if input_dto.body_id is not None and input_dto.body_id != input_dto.address_id:
            raise AddressValidationError("id", "does not match the id in the URL")

    @staticmethod
    def _validate_has_fields_to_update(input_dto: UpdateAddressInput) -> None:
        has_no_fields = (
            input_dto.country is None
            and input_dto.state is None
            and input_dto.city is None
            and input_dto.postal_code is None
            and input_dto.address_line is None
        )
        if has_no_fields:
            raise AddressValidationError("body", "no fields to update")
