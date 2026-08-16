from __future__ import annotations

from customers.application.dtos.customer_dto import CustomerOutput, UpdateCustomerInput
from customers.domain.exceptions import CustomerNotFoundError, CustomerValidationError
from customers.domain.repositories.customer_repository import CustomerRepository


class UpdateCustomerUseCase:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def execute(self, input_dto: UpdateCustomerInput) -> CustomerOutput:
        self._validate_body_id_matches_url(input_dto)
        self._validate_has_fields_to_update(input_dto)

        customer = self._repository.get_by_id(input_dto.customer_id)
        if customer is None:
            raise CustomerNotFoundError(input_dto.customer_id)

        if input_dto.name is not None:
            customer.rename(input_dto.name)
        if input_dto.age is not None:
            customer.update_age(input_dto.age)
        if input_dto.email is not None:
            customer.update_email(input_dto.email)

        updated = self._repository.update(customer)
        return CustomerOutput.from_entity(updated)

    @staticmethod
    def _validate_body_id_matches_url(input_dto: UpdateCustomerInput) -> None:
        if input_dto.body_id is not None and input_dto.body_id != input_dto.customer_id:
            raise CustomerValidationError("id", "does not match the id in the URL")

    @staticmethod
    def _validate_has_fields_to_update(input_dto: UpdateCustomerInput) -> None:
        if input_dto.name is None and input_dto.age is None and input_dto.email is None:
            raise CustomerValidationError("body", "no fields to update")
