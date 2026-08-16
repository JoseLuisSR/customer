"""Caso de uso `CreateAddress` (RF-006)."""

from __future__ import annotations

from dataclasses import dataclass

from customers.application.address.support import (
    AddressFieldsPayload,
    address_to_dict,
    build_address,
    validate_address_fields,
)
from customers.application.error_codes import ERR_CUSTOMER_NOT_FOUND, ERR_MAX_ADDRESSES_EXCEEDED
from customers.application.operation_result import Entity, Operation, OperationResult
from customers.domain.address.repository import AddressRepository
from customers.domain.customer.entities import Customer
from customers.domain.customer.exceptions import CustomerNotFoundError, MaxAddressesExceededError
from customers.domain.customer.repository import CustomerRepository
from customers.domain.customer.value_objects import CustomerId
from customers.domain.shared.validation import FieldError


@dataclass(frozen=True, slots=True)
class CreateAddressRequest:
    """Payload de `POST /customers/{id}/addresses` (`AddressRequest`)."""

    country: str
    state: str
    city: str
    address: str
    postal_code: str


class CreateAddress:
    """Crea una dirección para un cliente existente (RF-006/RN-003/RN-005).

    Usa `CustomerRepository.get_by_id_for_update` (bloqueo pesimista,
    `plan.md` §1.4) antes de contar direcciones activas e insertar, para
    evitar que dos altas simultáneas superen el límite de cinco
    direcciones activas.
    """

    def __init__(
        self, customer_repository: CustomerRepository, address_repository: AddressRepository
    ) -> None:
        self._customer_repository = customer_repository
        self._address_repository = address_repository

    def execute(self, customer_id: CustomerId, request: CreateAddressRequest) -> OperationResult:
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
                operation=Operation.CREATE,
                entity=Entity.ADDRESS,
                message="No fue posible crear la dirección: uno o más campos son inválidos.",
                errors=field_errors,
            )

        customer = self._customer_repository.get_by_id_for_update(customer_id)
        if customer is None:
            not_found_error = CustomerNotFoundError(customer_id)
            return OperationResult.fail(
                operation=Operation.CREATE,
                entity=Entity.ADDRESS,
                message=str(not_found_error),
                errors=[
                    FieldError(
                        code=ERR_CUSTOMER_NOT_FOUND, field=None, message=str(not_found_error)
                    )
                ],
            )

        active_count = self._address_repository.count_active_by_customer(customer_id)
        if active_count >= Customer.MAX_ACTIVE_ADDRESSES:
            max_exceeded_error = MaxAddressesExceededError(customer_id)
            return OperationResult.fail(
                operation=Operation.CREATE,
                entity=Entity.ADDRESS,
                message=str(max_exceeded_error),
                errors=[
                    FieldError(
                        code=ERR_MAX_ADDRESSES_EXCEEDED, field=None, message=str(max_exceeded_error)
                    )
                ],
            )

        address = build_address(payload, customer_id=customer_id)
        self._address_repository.add(address)

        return OperationResult.ok(
            operation=Operation.CREATE,
            entity=Entity.ADDRESS,
            entity_status=address.status,
            message="Dirección creada exitosamente.",
            data=address_to_dict(address),
        )
