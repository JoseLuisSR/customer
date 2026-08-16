"""Utilidades compartidas por los casos de uso de `Customer`.

Centraliza la validación de los campos comunes a `CreateCustomer` y
`UpdateCustomer` (VAL-001, VAL-003 a VAL-005), la verificación de unicidad
de `email`/`identification` (`specs/customers/implementation-plan.md`
§4.2: helper compartido para no duplicar la consulta a los repositorios) y
la serialización de `Customer` al `dict` que viaja en
`OperationResult.data` (`CustomerResponse`, `specs/customers/plan.md`
§2.2).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from customers.application.address.support import address_to_dict
from customers.application.error_codes import ERR_DUPLICATE_EMAIL, ERR_DUPLICATE_IDENTIFICATION
from customers.domain.address.entities import Address
from customers.domain.customer.entities import Customer
from customers.domain.customer.exceptions import DuplicateEmailError, DuplicateIdentificationError
from customers.domain.customer.repository import CustomerRepository
from customers.domain.customer.value_objects import Age, CustomerId, Email, Identification, Name
from customers.domain.shared.validation import FieldError


@dataclass(frozen=True, slots=True)
class CustomerFieldsPayload:
    """Campos comunes a `CustomerCreateRequest`/`CustomerUpdateRequest`."""

    name: str
    identification: str
    age: int
    email: str


def validate_customer_fields(payload: CustomerFieldsPayload) -> list[FieldError]:
    """Valida `name`, `identification`, `age`, `email` sin lanzar excepción.

    Acumula un `FieldError` por cada campo inválido (`plan.md` §2.5).
    """
    errors: list[FieldError] = []
    for error in (
        Name.validate(payload.name),
        Identification.validate(payload.identification),
        Age.validate(payload.age),
        Email.validate(payload.email),
    ):
        if error is not None:
            errors.append(error)
    return errors


def build_customer_value_objects(
    payload: CustomerFieldsPayload,
) -> tuple[Name, Identification, Age, Email]:
    """Construye los value objects de `Customer` a partir de un payload ya
    validado con `validate_customer_fields`.
    """
    return (
        Name(payload.name),
        Identification(payload.identification),
        Age(payload.age),
        Email(payload.email),
    )


def ensure_unique_email_and_identification(
    customer_repository: CustomerRepository,
    *,
    email: Email,
    identification: Identification,
    exclude_customer_id: CustomerId | None = None,
) -> list[FieldError]:
    """Verifica unicidad de `email` (ERR-002) e `identification` (ERR-008).

    `exclude_customer_id` evita un falso duplicado cuando `UpdateCustomer`
    reenvía el propio valor sin cambios (`plan.md` §2.5, caso límite §16).
    """
    errors: list[FieldError] = []
    if (
        customer_repository.find_by_email(email, exclude_customer_id=exclude_customer_id)
        is not None
    ):
        errors.append(
            FieldError(
                code=ERR_DUPLICATE_EMAIL,
                field="email",
                message=str(DuplicateEmailError(email.value)),
            )
        )
    if (
        customer_repository.find_by_identification(
            identification, exclude_customer_id=exclude_customer_id
        )
        is not None
    ):
        errors.append(
            FieldError(
                code=ERR_DUPLICATE_IDENTIFICATION,
                field="identification",
                message=str(DuplicateIdentificationError(identification.value)),
            )
        )
    return errors


def customer_to_dict(
    customer: Customer, *, addresses: list[Address] | None = None
) -> dict[str, Any]:
    """Serializa `Customer` al `dict` de `CustomerResponse` (`plan.md` §2.2).

    `addresses` permite inyectar explícitamente la colección de direcciones
    a embeber (consultada de forma independiente vía `AddressRepository`,
    para no depender de si el repositorio de clientes las precarga). Si es
    `None`, la clave `addresses` se omite (usado por `list_customers.py`,
    que no embebe direcciones, `plan.md` §2.2).
    """
    data: dict[str, Any] = {
        "id": str(customer.id),
        "name": customer.name.value,
        "identification": customer.identification.value,
        "age": customer.age.value,
        "email": customer.email.value,
        "status": customer.status.value,
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
        "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,
    }
    if addresses is not None:
        data["addresses"] = [address_to_dict(address) for address in addresses]
    return data
