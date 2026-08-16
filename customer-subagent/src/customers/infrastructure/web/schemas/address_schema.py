from __future__ import annotations

from typing import Any

from customers.application.dtos.address_dto import (
    AddressOutput,
    CreateAddressInput,
    UpdateAddressInput,
)
from customers.domain.exceptions import AddressValidationError


def parse_create_address_request(customer_id: int, payload: Any) -> CreateAddressInput:
    body = _require_json_object(payload)
    return CreateAddressInput(
        customer_id=customer_id,
        country=_require_field(body, "country"),
        state=_require_field(body, "state"),
        city=_require_field(body, "city"),
        postal_code=_require_field(body, "postalcode", internal_field="postal_code"),
        address_line=_require_field(body, "address", internal_field="address_line"),
    )


def parse_update_address_request(
    customer_id: int, address_id: int, payload: Any
) -> UpdateAddressInput:
    body = _require_json_object(payload)
    body_id = body.get("id")
    if body_id is not None and not _is_int(body_id):
        raise AddressValidationError("id", "must be an integer")
    return UpdateAddressInput(
        customer_id=customer_id,
        address_id=address_id,
        country=body.get("country"),
        state=body.get("state"),
        city=body.get("city"),
        postal_code=body.get("postalcode"),
        address_line=body.get("address"),
        body_id=body_id,
    )


def serialize_address(output: AddressOutput) -> dict[str, Any]:
    return {
        "id": output.id,
        "country": output.country,
        "state": output.state,
        "city": output.city,
        "postalcode": output.postal_code,
        "address": output.address_line,
    }


def _require_json_object(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AddressValidationError("body", "invalid or missing JSON body")
    return payload


def _require_field(
    body: dict[str, Any], field: str, *, internal_field: str | None = None
) -> Any:
    value = body.get(field)
    if value is None:
        raise AddressValidationError(internal_field or field, "is required")
    return value


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
