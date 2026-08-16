"""Excepciones de dominio del agregado `Customer`.

Ver `specs/customers/spec.md` VAL-001 a VAL-006 y `specs/customers/plan.md`
§2.4 para el mapeo funcional de cada excepción a un código de error HTTP
(traducción que ocurre en `infrastructure/http/error_handlers.py`, Fase 4).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from customers.domain.customer.value_objects import CustomerId


class CustomerDomainError(Exception):
    """Excepción base de todas las excepciones de dominio de `Customer`."""


class InvalidEmailError(CustomerDomainError):
    """VAL-001: el correo electrónico no tiene un formato válido."""


class InvalidNameError(CustomerDomainError):
    """VAL-003: el nombre está vacío tras `trim`."""


class InvalidIdentificationError(CustomerDomainError):
    """VAL-004: la identificación está vacía tras `trim`."""


class InvalidAgeError(CustomerDomainError):
    """VAL-005: la edad no es un entero dentro del rango permitido."""


class DuplicateEmailError(CustomerDomainError):
    """VAL-002/ERR-002: ya existe un cliente con el correo indicado."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Ya existe un cliente con el correo '{email}'.")
        self.email = email


class DuplicateIdentificationError(CustomerDomainError):
    """Ya existe un cliente con la identificación indicada.

    NOTA (código funcional provisional): esta regla corresponde a `VAL-011`
    y se traduce a `ERR-008` (409 Conflict) en `infrastructure/http/
    error_handlers.py` (Fase 4). Q-001 fue confirmada por negocio el
    2026-07-25 (unicidad de `identification`, ver `specs/customers/plan.md`
    §1.1/§2.4/§7.1), pero `specs/customers/spec.md` v0.1.0 todavía no
    documenta esta regla con un código funcional propio (Q-001 sigue
    "Abierta" en su sección 20). Ver riesgo documentado en
    `specs/customers/implementation-plan.md` §11 punto 1: si el spec
    funcional se actualiza con códigos distintos, renombrar esta excepción
    y su mapeo en `error_handlers.py`.
    """

    def __init__(self, identification: str) -> None:
        super().__init__(f"Ya existe un cliente con la identificación '{identification}'.")
        self.identification = identification


class MaxAddressesExceededError(CustomerDomainError):
    """RN-003/VAL-007: el cliente ya tiene cinco direcciones activas."""

    def __init__(self, customer_id: CustomerId | None = None) -> None:
        super().__init__("El cliente ya tiene cinco direcciones.")
        self.customer_id = customer_id


class CustomerNotFoundError(CustomerDomainError):
    """VAL-006: el cliente no existe (o está `DELETED`, que se trata igual)."""

    def __init__(self, customer_id: CustomerId | str) -> None:
        super().__init__("Cliente no encontrado.")
        self.customer_id = customer_id
