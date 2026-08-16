"""Caso de uso `GetCustomer` (RF-002)."""

from __future__ import annotations

from customers.application.customer.support import customer_to_dict
from customers.application.error_codes import ERR_CUSTOMER_NOT_FOUND
from customers.application.operation_result import Entity, Operation, OperationResult
from customers.domain.address.repository import AddressRepository
from customers.domain.customer.exceptions import CustomerNotFoundError
from customers.domain.customer.repository import CustomerRepository
from customers.domain.customer.value_objects import CustomerId
from customers.domain.shared.validation import FieldError


class GetCustomer:
    """Obtiene un cliente por id, con sus direcciones activas embebidas.

    Excluye clientes `DELETED` (VAL-006): se comportan como "no
    encontrados" (RF-002).
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
                operation=Operation.READ,
                entity=Entity.CUSTOMER,
                message=str(error),
                errors=[FieldError(code=ERR_CUSTOMER_NOT_FOUND, field=None, message=str(error))],
            )

        addresses = self._address_repository.list_by_customer(customer_id)
        return OperationResult.ok(
            operation=Operation.READ,
            entity=Entity.CUSTOMER,
            entity_status=customer.status,
            message="Cliente encontrado.",
            data=customer_to_dict(customer, addresses=addresses),
        )
