"""Caso de uso `CreateCustomer` (RF-001)."""

from __future__ import annotations

from dataclasses import dataclass, field

from customers.application.address.support import (
    AddressFieldsPayload,
    build_address,
    validate_address_fields,
)
from customers.application.customer.support import (
    CustomerFieldsPayload,
    build_customer_value_objects,
    customer_to_dict,
    ensure_unique_email_and_identification,
    validate_customer_fields,
)
from customers.application.error_codes import ERR_MAX_ADDRESSES_EXCEEDED
from customers.application.operation_result import Entity, Operation, OperationResult
from customers.domain.address.repository import AddressRepository
from customers.domain.customer.entities import Customer
from customers.domain.customer.repository import CustomerRepository
from customers.domain.shared.validation import FieldError

_MAX_ADDRESSES_ERROR = FieldError(
    code=ERR_MAX_ADDRESSES_EXCEEDED,
    field="addresses",
    message="Un cliente no puede tener más de cinco direcciones.",
)


@dataclass(frozen=True, slots=True)
class CreateCustomerRequest:
    """Payload de entrada de `POST /customers` (`CustomerCreateRequest`)."""

    name: str
    identification: str
    age: int
    email: str
    addresses: list[AddressFieldsPayload] = field(default_factory=list)


class CreateCustomer:
    """Crea un cliente nuevo, junto con hasta cinco direcciones (RF-001).

    Todo o nada (`plan.md` §2.5): si el payload trae más de cinco
    direcciones, cualquier campo del cliente/direcciones es inválido, o
    `email`/`identification` ya existen, no se crea ni el cliente ni
    ninguna dirección.
    """

    def __init__(
        self, customer_repository: CustomerRepository, address_repository: AddressRepository
    ) -> None:
        self._customer_repository = customer_repository
        self._address_repository = address_repository

    def execute(self, request: CreateCustomerRequest) -> OperationResult:
        customer_payload = CustomerFieldsPayload(
            name=request.name,
            identification=request.identification,
            age=request.age,
            email=request.email,
        )
        field_errors = validate_customer_fields(customer_payload)
        field_errors.extend(self._validate_addresses(request.addresses))
        if field_errors:
            return OperationResult.fail(
                operation=Operation.CREATE,
                entity=Entity.CUSTOMER,
                message="No fue posible crear el cliente: uno o más campos son inválidos.",
                errors=field_errors,
            )

        name, identification, age, email = build_customer_value_objects(customer_payload)

        duplicate_errors = ensure_unique_email_and_identification(
            self._customer_repository, email=email, identification=identification
        )
        if duplicate_errors:
            return OperationResult.fail(
                operation=Operation.CREATE,
                entity=Entity.CUSTOMER,
                message=(
                    "No fue posible crear el cliente: ya existe un cliente con el correo o "
                    "la identificación indicados."
                ),
                errors=duplicate_errors,
            )

        customer = Customer.create(name=name, identification=identification, age=age, email=email)
        for address_payload in request.addresses:
            customer.add_address(build_address(address_payload, customer_id=customer.id))

        self._customer_repository.add(customer)
        for address in customer.addresses:
            self._address_repository.add(address)

        return OperationResult.ok(
            operation=Operation.CREATE,
            entity=Entity.CUSTOMER,
            entity_status=customer.status,
            message="Cliente creado exitosamente.",
            data=customer_to_dict(customer, addresses=customer.addresses),
        )

    @staticmethod
    def _validate_addresses(addresses: list[AddressFieldsPayload]) -> list[FieldError]:
        if len(addresses) > Customer.MAX_ACTIVE_ADDRESSES:
            return [_MAX_ADDRESSES_ERROR]
        errors: list[FieldError] = []
        for index, payload in enumerate(addresses):
            for error in validate_address_fields(payload):
                errors.append(
                    FieldError(
                        code=error.code,
                        field=f"addresses[{index}].{error.field}",
                        message=error.message,
                    )
                )
        return errors
