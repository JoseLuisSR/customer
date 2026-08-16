from __future__ import annotations

from typing import Any

from customers.application.dtos.customer_dto import (
    CreateCustomerInput,
    CustomerOutput,
    UpdateCustomerInput,
)
from customers.domain.exceptions import CustomerValidationError


def parse_create_customer_request(payload: Any) -> CreateCustomerInput:
    body = _require_json_object(payload)
    return CreateCustomerInput(
        name=_require_field(body, "name"),
        age=_require_field(body, "age"),
        email=_require_field(body, "email"),
    )


def parse_update_customer_request(
    customer_id: int, payload: Any
) -> UpdateCustomerInput:
    body = _require_json_object(payload)
    body_id = body.get("id")
    if body_id is not None and not _is_int(body_id):
        raise CustomerValidationError("id", "must be an integer")
    return UpdateCustomerInput(
        customer_id=customer_id,
        name=body.get("name"),
        age=body.get("age"),
        email=body.get("email"),
        body_id=body_id,
    )


def serialize_customer(output: CustomerOutput) -> dict[str, Any]:
    return {
        "id": output.id,
        "name": output.name,
        "age": output.age,
        "email": output.email,
    }


def _require_json_object(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CustomerValidationError("body", "invalid or missing JSON body")
    return payload


def _require_field(body: dict[str, Any], field: str) -> Any:
    if field not in body or body[field] is None:
        raise CustomerValidationError(field, "is required")
    return body[field]


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
