"""Utilidades compartidas por los casos de uso de `Address`.

Centraliza la validación de los cinco campos de una dirección (VAL-009), la
construcción de la entidad `Address` a partir de un payload ya validado y
su serialización al `dict` que viaja en `OperationResult.data`
(`AddressResponse`, `specs/customers/plan.md` §2.3). La reutilizan
`create_address.py`, `update_address.py` y, de forma indexada, también
`customer/create_customer.py` (direcciones embebidas en la creación de un
cliente).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from customers.domain.address.entities import Address
from customers.domain.address.value_objects import (
    AddressId,
    City,
    Country,
    PostalCode,
    State,
    StreetAddress,
)
from customers.domain.customer.value_objects import CustomerId
from customers.domain.shared.validation import FieldError


@dataclass(frozen=True, slots=True)
class AddressFieldsPayload:
    """Campos de `AddressRequest` (`specs/customers/plan.md` §2.3)."""

    country: str
    state: str
    city: str
    address: str
    postal_code: str


def validate_address_fields(payload: AddressFieldsPayload) -> list[FieldError]:
    """Valida los cinco campos de una dirección (VAL-009), sin lanzar.

    Acumula un `FieldError` por cada campo inválido (`plan.md` §2.5).
    """
    errors: list[FieldError] = []
    for error in (
        Country.validate(payload.country),
        State.validate(payload.state),
        City.validate(payload.city),
        StreetAddress.validate(payload.address),
        PostalCode.validate(payload.postal_code),
    ):
        if error is not None:
            errors.append(error)
    return errors


def build_address(
    payload: AddressFieldsPayload,
    *,
    customer_id: CustomerId,
    address_id: AddressId | None = None,
) -> Address:
    """Construye una `Address` `ACTIVE` a partir de un payload ya validado.

    Solo debe invocarse tras confirmar con `validate_address_fields` que no
    hay errores; de lo contrario los constructores de los value objects
    lanzarían `InvalidAddressFieldError`.
    """
    return Address.create(
        customer_id=customer_id,
        country=Country(payload.country),
        state=State(payload.state),
        city=City(payload.city),
        street_address=StreetAddress(payload.address),
        postal_code=PostalCode(payload.postal_code),
        address_id=address_id,
    )


def address_to_dict(address: Address) -> dict[str, Any]:
    """Serializa `Address` al `dict` de `AddressResponse` (`plan.md` §2.3)."""
    return {
        "id": str(address.id),
        "customer_id": str(address.customer_id),
        "country": address.country.value,
        "state": address.state.value,
        "city": address.city.value,
        "address": address.street_address.value,
        "postal_code": address.postal_code.value,
        "status": address.status.value,
        "created_at": address.created_at.isoformat() if address.created_at else None,
        "updated_at": address.updated_at.isoformat() if address.updated_at else None,
    }
