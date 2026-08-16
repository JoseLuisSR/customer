"""Caso de uso `UpdateCustomer` (RF-004)."""

from __future__ import annotations

from dataclasses import dataclass

from customers.application.customer.support import (
    CustomerFieldsPayload,
    build_customer_value_objects,
    customer_to_dict,
    ensure_unique_email_and_identification,
    validate_customer_fields,
)
from customers.application.error_codes import ERR_CUSTOMER_NOT_FOUND
from customers.application.operation_result import Entity, Operation, OperationResult
from customers.domain.address.repository import AddressRepository
from customers.domain.customer.exceptions import CustomerNotFoundError
from customers.domain.customer.repository import CustomerRepository
from customers.domain.customer.value_objects import CustomerId
from customers.domain.shared.validation import FieldError


@dataclass(frozen=True, slots=True)
class UpdateCustomerRequest:
    """Payload de `PUT /customers/{id}` (`CustomerUpdateRequest`)."""

    name: str
    identification: str
    age: int
    email: str


class UpdateCustomer:
    """Reemplaza por completo los datos de un cliente existente (RF-004).

    Excluye al propio cliente en la verificación de unicidad de
    `email`/`identification` (`plan.md` §2.5), evitando un falso duplicado
    cuando el cliente reenvía su propio valor sin cambios.
    """

    def __init__(
        self, customer_repository: CustomerRepository, address_repository: AddressRepository
    ) -> None:
        self._customer_repository = customer_repository
        self._address_repository = address_repository

    def execute(self, customer_id: CustomerId, request: UpdateCustomerRequest) -> OperationResult:
        customer = self._customer_repository.get_by_id(customer_id)
        if customer is None:
            error = CustomerNotFoundError(customer_id)
            return OperationResult.fail(
                operation=Operation.UPDATE,
                entity=Entity.CUSTOMER,
                message=str(error),
                errors=[FieldError(code=ERR_CUSTOMER_NOT_FOUND, field=None, message=str(error))],
            )

        payload = CustomerFieldsPayload(
            name=request.name,
            identification=request.identification,
            age=request.age,
            email=request.email,
        )
        field_errors = validate_customer_fields(payload)
        if field_errors:
            return OperationResult.fail(
                operation=Operation.UPDATE,
                entity=Entity.CUSTOMER,
                message="No fue posible actualizar el cliente: uno o más campos son inválidos.",
                errors=field_errors,
            )

        name, identification, age, email = build_customer_value_objects(payload)

        duplicate_errors = ensure_unique_email_and_identification(
            self._customer_repository,
            email=email,
            identification=identification,
            exclude_customer_id=customer_id,
        )
        if duplicate_errors:
            return OperationResult.fail(
                operation=Operation.UPDATE,
                entity=Entity.CUSTOMER,
                message=(
                    "No fue posible actualizar el cliente: ya existe otro cliente con el "
                    "correo o la identificación indicados."
                ),
                errors=duplicate_errors,
            )

        customer.name = name
        customer.identification = identification
        customer.age = age
        customer.email = email
        self._customer_repository.update(customer)

        addresses = self._address_repository.list_by_customer(customer_id)
        return OperationResult.ok(
            operation=Operation.UPDATE,
            entity=Entity.CUSTOMER,
            entity_status=customer.status,
            message="Cliente actualizado exitosamente.",
            data=customer_to_dict(customer, addresses=addresses),
        )
