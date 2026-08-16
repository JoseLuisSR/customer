"""Excepciones de dominio de la entidad `Address`.

Ver `specs/customers/spec.md` VAL-008 a VAL-010 y `specs/customers/plan.md`
§2.4 para el mapeo funcional de cada excepción a un código de error HTTP.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from customers.domain.address.value_objects import AddressId
    from customers.domain.customer.value_objects import CustomerId


class AddressDomainError(Exception):
    """Excepción base de todas las excepciones de dominio de `Address`."""


class InvalidAddressFieldError(AddressDomainError):
    """VAL-009: un campo obligatorio de la dirección está vacío tras `trim`

    (o RN-005: la dirección se intentó construir sin un `customer_id`
    válido).
    """


class AddressNotFoundError(AddressDomainError):
    """VAL-010: la dirección no existe (o está `DELETED`, se trata igual)."""

    def __init__(self, address_id: AddressId | str) -> None:
        super().__init__("Dirección no encontrada.")
        self.address_id = address_id


class AddressCustomerMismatchError(AddressDomainError):
    """VAL-008/ERR-006: la dirección no pertenece al cliente indicado."""

    def __init__(self, address_id: AddressId | str, customer_id: CustomerId | str) -> None:
        super().__init__("La dirección no pertenece al cliente indicado.")
        self.address_id = address_id
        self.customer_id = customer_id
