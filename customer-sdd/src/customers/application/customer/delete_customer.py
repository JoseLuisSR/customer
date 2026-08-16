"""Caso de uso `DeleteCustomer` (RF-005)."""

from __future__ import annotations

from customers.application.customer.support import customer_to_dict
from customers.application.error_codes import ERR_CUSTOMER_NOT_FOUND
from customers.application.operation_result import Entity, Operation, OperationResult
from customers.domain.address.repository import AddressRepository
from customers.domain.customer.exceptions import CustomerNotFoundError
from customers.domain.customer.repository import CustomerRepository
from customers.domain.customer.value_objects import CustomerId
from customers.domain.shared.validation import FieldError


class DeleteCustomer:
    """Elimina lógicamente un cliente y todas sus direcciones (RF-005/RN-004).

    Usa `Customer.mark_deleted()` para el propio cliente (y cualquier
    dirección que ya estuviera cargada en el agregado) y, de forma
    autoritativa, `AddressRepository.mark_all_deleted_by_customer` para
    garantizar que ninguna dirección quede huérfana en estado `ACTIVE`,
    sin depender de si el repositorio de clientes precarga direcciones.
    """

    def __init__(
        self, customer_repository: CustomerRepository, address_repository: AddressRepository
    ) -> None:
        self._customer_repository = customer_repository
        self._address_repository = address_repository

    def execute(self, customer_id: CustomerId) -> OperationResult:
        customer = self._customer_repository.get_by_id(customer_id)
        if customer is None:
            error = CustomerNotFoundError(customer_id)
            return OperationResult.fail(
                operation=Operation.DELETE,
                entity=Entity.CUSTOMER,
                message=str(error),
                errors=[FieldError(code=ERR_CUSTOMER_NOT_FOUND, field=None, message=str(error))],
            )

        customer.mark_deleted()
        self._customer_repository.update(customer)
        self._address_repository.mark_all_deleted_by_customer(customer_id)

        addresses = self._address_repository.list_by_customer(customer_id, include_deleted=True)
        return OperationResult.ok(
            operation=Operation.DELETE,
            entity=Entity.CUSTOMER,
            entity_status=customer.status,
            message="Cliente eliminado exitosamente.",
            data=customer_to_dict(customer, addresses=addresses),
        )
