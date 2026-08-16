"""Caso de uso `UpdateAddress` (RF-008)."""

from __future__ import annotations

from dataclasses import dataclass

from customers.application.address.support import (
    AddressFieldsPayload,
    address_to_dict,
    validate_address_fields,
)
from customers.application.error_codes import (
    ERR_ADDRESS_CUSTOMER_MISMATCH,
    ERR_ADDRESS_NOT_FOUND,
    ERR_CUSTOMER_NOT_FOUND,
)
from customers.application.operation_result import Entity, Operation, OperationResult
from customers.domain.address.exceptions import AddressCustomerMismatchError, AddressNotFoundError
from customers.domain.address.repository import AddressRepository
from customers.domain.address.value_objects import (
    AddressId,
    City,
    Country,
    PostalCode,
    State,
    StreetAddress,
)
from customers.domain.customer.exceptions import CustomerNotFoundError
from customers.domain.customer.repository import CustomerRepository
from customers.domain.customer.value_objects import CustomerId
from customers.domain.shared.validation import FieldError


@dataclass(frozen=True, slots=True)
class UpdateAddressRequest:
    """Payload de `PUT /customers/{id}/addresses/{address_id}` (`AddressRequest`)."""

    country: str
    state: str
    city: str
    address: str
    postal_code: str


class UpdateAddress:
    """Reemplaza por completo los datos de una dirección existente (RF-008).

    Verifica cliente y dirección existentes, y que la dirección pertenezca
    al cliente indicado (VAL-008/ERR-006).
    """

    def __init__(
        self, customer_repository: CustomerRepository, address_repository: AddressRepository
    ) -> None:
        self._customer_repository = customer_repository
        self._address_repository = address_repository

    def execute(
        self, customer_id: CustomerId, address_id: AddressId, request: UpdateAddressRequest
    ) -> OperationResult:
        customer = self._customer_repository.get_by_id(customer_id)
        if customer is None:
            error = CustomerNotFoundError(customer_id)
            return OperationResult.fail(
                operation=Operation.UPDATE,
                entity=Entity.ADDRESS,
                message=str(error),
                errors=[FieldError(code=ERR_CUSTOMER_NOT_FOUND, field=None, message=str(error))],
            )

        address = self._address_repository.get_by_id(address_id)
        if address is None:
            not_found_error = AddressNotFoundError(address_id)
            return OperationResult.fail(
                operation=Operation.UPDATE,
                entity=Entity.ADDRESS,
                message=str(not_found_error),
                errors=[
                    FieldError(code=ERR_ADDRESS_NOT_FOUND, field=None, message=str(not_found_error))
                ],
            )

        if address.customer_id != customer_id:
            mismatch_error = AddressCustomerMismatchError(address_id, customer_id)
            return OperationResult.fail(
                operation=Operation.UPDATE,
                entity=Entity.ADDRESS,
                message=str(mismatch_error),
                errors=[
                    FieldError(
                        code=ERR_ADDRESS_CUSTOMER_MISMATCH,
                        field=None,
                        message=str(mismatch_error),
                    )
                ],
            )

        payload = AddressFieldsPayload(
            country=request.country,
            state=request.state,
            city=request.city,
            address=request.address,
            postal_code=request.postal_code,
        )
        field_errors = validate_address_fields(payload)
        if field_errors:
            return OperationResult.fail(
                operation=Operation.UPDATE,
                entity=Entity.ADDRESS,
                message="No fue posible actualizar la dirección: uno o más campos son inválidos.",
                errors=field_errors,
            )

        address.country = Country(payload.country)
        address.state = State(payload.state)
        address.city = City(payload.city)
        address.street_address = StreetAddress(payload.address)
        address.postal_code = PostalCode(payload.postal_code)
        self._address_repository.update(address)

        return OperationResult.ok(
            operation=Operation.UPDATE,
            entity=Entity.ADDRESS,
            entity_status=address.status,
            message="Dirección actualizada exitosamente.",
            data=address_to_dict(address),
        )
