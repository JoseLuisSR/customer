"""Parseo manual de payloads HTTP -> DTOs de la capa de aplicación.

Python puro, sin `pydantic`/`marshmallow` (decisión de `specs/customers/
plan.md` §3: el stack declarado no las incluye). Reutiliza el mismo
mecanismo de acumulación de errores del dominio (`FieldError`,
`Value.validate(raw_value)`, ver `domain/shared/validation.py`) para
reportar en un solo intento **todos** los campos de forma/tipo inválidos
de un payload (VAL-001, VAL-003, VAL-004, VAL-005, VAL-009 "a nivel de
forma del JSON": campo ausente o de tipo incorrecto), tal como exige
`specs/customers/plan.md` §2.5 para el contenido de los campos.

Cuando el payload no puede convertirse en un DTO válido, las funciones de
este módulo lanzan `RequestParsingError` con la lista completa de
`FieldError` encontrados; `infrastructure/http/error_handlers.py` registra
el manejador de Flask que la traduce a `ERR-001`/400.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from customers.application.address.create_address import CreateAddressRequest
from customers.application.address.support import AddressFieldsPayload
from customers.application.address.update_address import UpdateAddressRequest
from customers.application.customer.create_customer import CreateCustomerRequest
from customers.application.customer.list_customers import ListCustomersRequest
from customers.application.customer.update_customer import UpdateCustomerRequest
from customers.domain.address.value_objects import (
    AddressId,
    City,
    Country,
    PostalCode,
    State,
    StreetAddress,
)
from customers.domain.customer.value_objects import Age, CustomerId, Email, Identification, Name
from customers.domain.shared.validation import FieldError

ERR_INVALID_BODY = "ERR-001"


class RequestParsingError(Exception):
    """El cuerpo o un parámetro de la petición no tiene la forma/tipo esperado.

    Se lanza cuando el JSON de entrada no es un objeto, le faltan campos
    obligatorios, un campo tiene un tipo incorrecto, o un identificador de
    ruta (`customer_id`/`address_id`) no es un `UUID` válido. Traducida a
    `ERR-001`/400 por `infrastructure/http/error_handlers.py`.
    """

    def __init__(self, errors: list[FieldError]) -> None:
        super().__init__("El cuerpo o los parámetros de la petición no son válidos.")
        self.errors = errors


# --- Parseo de identificadores de ruta ---------------------------------


def parse_customer_id(raw_value: str) -> CustomerId:
    """Convierte el segmento `{customer_id}` de la ruta en un `CustomerId`."""
    try:
        return CustomerId.from_string(raw_value)
    except ValueError as exc:
        raise RequestParsingError(
            [FieldError(code=ERR_INVALID_BODY, field="customer_id", message=str(exc))]
        ) from exc


def parse_address_id(raw_value: str) -> AddressId:
    """Convierte el segmento `{address_id}` de la ruta en un `AddressId`."""
    try:
        return AddressId.from_string(raw_value)
    except ValueError as exc:
        raise RequestParsingError(
            [FieldError(code=ERR_INVALID_BODY, field="address_id", message=str(exc))]
        ) from exc


# --- Parseo de query params de paginación (RF-003, Q-006) --------------


def parse_list_customers_request(args: Mapping[str, str]) -> ListCustomersRequest:
    """Construye `ListCustomersRequest` desde los query params `page`/`page_size`.

    Un valor ausente o no convertible a entero se deja como `None`: el
    propio caso de uso `ListCustomers` normaliza `None`/valores fuera de
    rango a los valores por defecto (`plan.md` §7.6), por lo que no se
    considera un error de forma rechazable con `ERR-001`.
    """
    return ListCustomersRequest(
        page=_parse_optional_int(args.get("page")),
        page_size=_parse_optional_int(args.get("page_size")),
    )


def _parse_optional_int(raw_value: str | None) -> int | None:
    if raw_value is None:
        return None
    try:
        return int(raw_value)
    except ValueError:
        return None


# --- Helpers internos de parseo de campos de cuerpo JSON ----------------


def _require_json_object(raw_body: Any) -> dict[str, Any]:
    if not isinstance(raw_body, dict):
        raise RequestParsingError(
            [
                FieldError(
                    code=ERR_INVALID_BODY,
                    field=None,
                    message="El cuerpo de la petición debe ser un objeto JSON.",
                )
            ]
        )
    return raw_body


def _parse_str_field(
    payload: dict[str, Any], field: str, code: str
) -> tuple[str, FieldError | None]:
    if field not in payload:
        return "", FieldError(code=code, field=field, message=f"El campo '{field}' es obligatorio.")
    value = payload[field]
    if not isinstance(value, str):
        return "", FieldError(
            code=code, field=field, message=f"El campo '{field}' debe ser una cadena de texto."
        )
    return value, None


def _parse_int_field(
    payload: dict[str, Any], field: str, code: str
) -> tuple[int, FieldError | None]:
    if field not in payload:
        return 0, FieldError(code=code, field=field, message=f"El campo '{field}' es obligatorio.")
    value = payload[field]
    if isinstance(value, bool) or not isinstance(value, int):
        return 0, FieldError(
            code=code, field=field, message=f"El campo '{field}' debe ser un número entero."
        )
    return value, None


def _parse_and_validate_str(
    payload: dict[str, Any],
    field: str,
    code: str,
    validate_fn: Any,
) -> tuple[str, FieldError | None]:
    """Parsea `field` como cadena y, si la forma es correcta, valida su
    contenido con el mismo `validate()` del value object de dominio
    correspondiente (p. ej. `Email.validate`), sin lanzar excepción.
    """
    value, shape_error = _parse_str_field(payload, field, code)
    if shape_error is not None:
        return value, shape_error
    content_error: FieldError | None = validate_fn(value)
    return value, content_error


def _parse_and_validate_int(
    payload: dict[str, Any],
    field: str,
    code: str,
    validate_fn: Any,
) -> tuple[int, FieldError | None]:
    value, shape_error = _parse_int_field(payload, field, code)
    if shape_error is not None:
        return value, shape_error
    content_error: FieldError | None = validate_fn(value)
    return value, content_error


def _prefixed(error: FieldError, prefix: str) -> FieldError:
    field = f"{prefix}{error.field}" if error.field else prefix.rstrip(".")
    return FieldError(code=error.code, field=field, message=error.message)


# --- Direcciones (`AddressRequest`, `plan.md` §2.3) ----------------------


def _parse_address_fields(
    payload: dict[str, Any], *, field_prefix: str = ""
) -> tuple[AddressFieldsPayload, list[FieldError]]:
    errors: list[FieldError] = []

    country, error = _parse_and_validate_str(payload, "country", "VAL-009", Country.validate)
    if error is not None:
        errors.append(_prefixed(error, field_prefix))

    state, error = _parse_and_validate_str(payload, "state", "VAL-009", State.validate)
    if error is not None:
        errors.append(_prefixed(error, field_prefix))

    city, error = _parse_and_validate_str(payload, "city", "VAL-009", City.validate)
    if error is not None:
        errors.append(_prefixed(error, field_prefix))

    address, error = _parse_and_validate_str(payload, "address", "VAL-009", StreetAddress.validate)
    if error is not None:
        errors.append(_prefixed(error, field_prefix))

    postal_code, error = _parse_and_validate_str(
        payload, "postal_code", "VAL-009", PostalCode.validate
    )
    if error is not None:
        errors.append(_prefixed(error, field_prefix))

    return (
        AddressFieldsPayload(
            country=country, state=state, city=city, address=address, postal_code=postal_code
        ),
        errors,
    )


def parse_create_address_request(raw_body: Any) -> CreateAddressRequest:
    """Parsea el cuerpo de `POST /customers/{id}/addresses`."""
    payload = _require_json_object(raw_body)
    fields, errors = _parse_address_fields(payload)
    if errors:
        raise RequestParsingError(errors)
    return CreateAddressRequest(
        country=fields.country,
        state=fields.state,
        city=fields.city,
        address=fields.address,
        postal_code=fields.postal_code,
    )


def parse_update_address_request(raw_body: Any) -> UpdateAddressRequest:
    """Parsea el cuerpo de `PUT /customers/{id}/addresses/{address_id}`."""
    payload = _require_json_object(raw_body)
    fields, errors = _parse_address_fields(payload)
    if errors:
        raise RequestParsingError(errors)
    return UpdateAddressRequest(
        country=fields.country,
        state=fields.state,
        city=fields.city,
        address=fields.address,
        postal_code=fields.postal_code,
    )


# --- Clientes (`CustomerCreateRequest`/`CustomerUpdateRequest`, `plan.md` §2.2) --


def _parse_customer_fields(
    payload: dict[str, Any],
) -> tuple[str, str, int, str, list[FieldError]]:
    errors: list[FieldError] = []

    name, error = _parse_and_validate_str(payload, "name", "VAL-003", Name.validate)
    if error is not None:
        errors.append(error)

    identification, error = _parse_and_validate_str(
        payload, "identification", "VAL-004", Identification.validate
    )
    if error is not None:
        errors.append(error)

    age, error = _parse_and_validate_int(payload, "age", "VAL-005", Age.validate)
    if error is not None:
        errors.append(error)

    email, error = _parse_and_validate_str(payload, "email", "VAL-001", Email.validate)
    if error is not None:
        errors.append(error)

    return name, identification, age, email, errors


def _parse_embedded_addresses(
    payload: dict[str, Any],
) -> tuple[list[AddressFieldsPayload], list[FieldError]]:
    raw_addresses = payload.get("addresses", [])
    if raw_addresses is None:
        raw_addresses = []
    if not isinstance(raw_addresses, list):
        return [], [
            FieldError(
                code="VAL-009",
                field="addresses",
                message="El campo 'addresses' debe ser una lista.",
            )
        ]

    errors: list[FieldError] = []
    addresses: list[AddressFieldsPayload] = []
    for index, item in enumerate(raw_addresses):
        prefix = f"addresses[{index}]."
        if not isinstance(item, dict):
            errors.append(
                FieldError(
                    code="VAL-009",
                    field=f"addresses[{index}]",
                    message="Cada dirección debe ser un objeto JSON.",
                )
            )
            continue
        fields, address_errors = _parse_address_fields(item, field_prefix=prefix)
        addresses.append(fields)
        errors.extend(address_errors)
    return addresses, errors


def parse_customer_create_request(raw_body: Any) -> CreateCustomerRequest:
    """Parsea el cuerpo de `POST /customers` (incluye `addresses` embebidas)."""
    payload = _require_json_object(raw_body)
    name, identification, age, email, errors = _parse_customer_fields(payload)
    addresses, address_errors = _parse_embedded_addresses(payload)
    errors.extend(address_errors)
    if errors:
        raise RequestParsingError(errors)
    return CreateCustomerRequest(
        name=name,
        identification=identification,
        age=age,
        email=email,
        addresses=addresses,
    )


def parse_customer_update_request(raw_body: Any) -> UpdateCustomerRequest:
    """Parsea el cuerpo de `PUT /customers/{id}` (sin `addresses`, `plan.md` §2.2)."""
    payload = _require_json_object(raw_body)
    name, identification, age, email, errors = _parse_customer_fields(payload)
    if errors:
        raise RequestParsingError(errors)
    return UpdateCustomerRequest(name=name, identification=identification, age=age, email=email)
