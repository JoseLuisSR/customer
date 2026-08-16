"""Caso de uso `DeleteAddress` (RF-009)."""

from __future__ import annotations

from customers.application.address.support import address_to_dict
from customers.application.error_codes import (
    ERR_ADDRESS_CUSTOMER_MISMATCH,
    ERR_ADDRESS_NOT_FOUND,
    ERR_CUSTOMER_NOT_FOUND,
)
from customers.application.operation_result import Entity, Operation, OperationResult
from customers.domain.address.exceptions import AddressCustomerMismatchError, AddressNotFoundError
from customers.domain.address.repository import AddressRepository
from customers.domain.address.value_objects import AddressId
from customers.domain.customer.exceptions import CustomerNotFoundError
from customers.domain.customer.repository import CustomerRepository
from customers.domain.customer.value_objects import CustomerId
from customers.domain.shared.validation import FieldError


class DeleteAddress:
    """Elimina lógicamente una dirección de un cliente existente (RF-009).

    Verifica cliente y dirección existentes, y que la dirección pertenezca
    al cliente indicado (VAL-008/ERR-006), antes de aplicar el borrado
    lógico.
    """

    def __init__(
        self, customer_repository: CustomerRepository, address_repository: AddressRepository
    ) -> None:
        self._customer_repository = customer_repository
        self._address_repository = address_repository

    def execute(self, customer_id: CustomerId, address_id: AddressId) -> OperationResult:
        customer = self._customer_repository.get_by_id(customer_id)
        if customer is None:
            error = CustomerNotFoundError(customer_id)
            return OperationResult.fail(
                operation=Operation.DELETE,
                entity=Entity.ADDRESS,
                message=str(error),
                errors=[FieldError(code=ERR_CUSTOMER_NOT_FOUND, field=None, message=str(error))],
            )

        address = self._address_repository.get_by_id(address_id)
        if address is None:
            not_found_error = AddressNotFoundError(address_id)
            return OperationResult.fail(
                operation=Operation.DELETE,
                entity=Entity.ADDRESS,
                message=str(not_found_error),
                errors=[
                    FieldError(code=ERR_ADDRESS_NOT_FOUND, field=None, message=str(not_found_error))
                ],
            )

        if address.customer_id != customer_id:
            mismatch_error = AddressCustomerMismatchError(address_id, customer_id)
            return OperationResult.fail(
                operation=Operation.DELETE,
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

        address.mark_deleted()
        self._address_repository.update(address)

        return OperationResult.ok(
            operation=Operation.DELETE,
            entity=Entity.ADDRESS,
            entity_status=address.status,
            message="Dirección eliminada exitosamente.",
            data=address_to_dict(address),
        )
