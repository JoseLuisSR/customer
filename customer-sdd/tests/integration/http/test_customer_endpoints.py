"""Pruebas de integración HTTP end-to-end de los endpoints de `Customer`.

Referencias: `specs/customers/implementation-plan.md` §8.1, `specs/customers/
plan.md` §2.2/§2.4/§6.2, `specs/customers/spec.md` §12/§13/§15.

Cubre los escenarios funcionales 1, 2, 5 y 7 (`spec.md` §12) y los criterios
de aceptación CA-001 a CA-005 y CA-008 (`spec.md` §15), verificando en cada
caso el sobre de resultado completo (`success`, `operation`, `entity`,
`entity_status`, `message`, `data`, `errors`) y el código HTTP exacto de
`plan.md` §2.4, incluyendo el código provisional `ERR-008` (identificación
duplicada).
"""

from __future__ import annotations

import uuid
from typing import Any, NoReturn

from flask import Flask
from flask.testing import FlaskClient

from customers.infrastructure.http.error_handlers import register_error_handlers

_BASE = "/api/v1/customers"


def _customer_payload(
    *,
    name: str = "Ana Pérez",
    identification: str = "ID-0001",
    age: int = 30,
    email: str = "ana@example.com",
    addresses: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": name,
        "identification": identification,
        "age": age,
        "email": email,
    }
    if addresses is not None:
        payload["addresses"] = addresses
    return payload


def _address_payload(*, postal_code: str = "110111") -> dict[str, Any]:
    return {
        "country": "Colombia",
        "state": "Bogotá D.C.",
        "city": "Bogotá",
        "address": "Calle 123 #45-67",
        "postal_code": postal_code,
    }


def _assert_envelope_keys(body: dict[str, Any]) -> None:
    assert set(body.keys()) == {
        "success",
        "operation",
        "entity",
        "entity_status",
        "message",
        "data",
        "errors",
    }


# --- Escenario 1 / CA-001: creación exitosa -------------------------------


def test_create_customer_success_returns_201_and_full_envelope(client: FlaskClient) -> None:
    response = client.post(_BASE, json=_customer_payload())

    assert response.status_code == 201
    body = response.get_json()
    _assert_envelope_keys(body)
    assert body["success"] is True
    assert body["operation"] == "create"
    assert body["entity"] == "customer"
    assert body["entity_status"] == "ACTIVE"
    assert body["errors"] is None
    assert body["data"]["email"] == "ana@example.com"
    assert body["data"]["created_at"] is not None
    assert body["data"]["updated_at"] is not None
    assert uuid.UUID(body["data"]["id"])


def test_create_customer_with_embedded_addresses_success(client: FlaskClient) -> None:
    payload = _customer_payload(
        addresses=[_address_payload(), _address_payload(postal_code="110222")]
    )

    response = client.post(_BASE, json=payload)

    assert response.status_code == 201
    body = response.get_json()
    assert len(body["data"]["addresses"]) == 2
    assert all(a["status"] == "ACTIVE" for a in body["data"]["addresses"])


# --- Escenario 2 / CA-002: correo e identificación duplicados -------------


def test_create_customer_rejects_duplicate_email(client: FlaskClient) -> None:
    client.post(_BASE, json=_customer_payload(identification="ID-0001", email="dup@example.com"))

    response = client.post(
        _BASE, json=_customer_payload(identification="ID-0002", email="dup@example.com")
    )

    assert response.status_code == 409
    body = response.get_json()
    assert body["success"] is False
    assert body["errors"][0]["code"] == "ERR-002"


def test_create_customer_rejects_duplicate_identification(client: FlaskClient) -> None:
    client.post(_BASE, json=_customer_payload(identification="ID-DUP", email="uno@example.com"))

    response = client.post(
        _BASE, json=_customer_payload(identification="ID-DUP", email="dos@example.com")
    )

    assert response.status_code == 409
    body = response.get_json()
    assert body["success"] is False
    assert body["errors"][0]["code"] == "ERR-008"


def test_create_customer_rejects_invalid_payload_with_one_error_per_field(
    client: FlaskClient,
) -> None:
    response = client.post(
        _BASE,
        json={"name": "", "identification": "", "age": -1, "email": "no-es-un-correo"},
    )

    assert response.status_code == 400
    body = response.get_json()
    assert body["success"] is False
    fields_with_errors = {error["field"] for error in body["errors"]}
    assert {"name", "identification", "age", "email"} <= fields_with_errors


def test_create_customer_rejects_more_than_five_addresses_creates_nothing(
    client: FlaskClient,
) -> None:
    payload = _customer_payload(
        identification="ID-6ADDR",
        email="seis@example.com",
        addresses=[_address_payload(postal_code=f"11000{i}") for i in range(6)],
    )

    response = client.post(_BASE, json=payload)

    assert response.status_code == 409
    body = response.get_json()
    assert body["errors"][0]["code"] == "ERR-005"

    listing = client.get(_BASE)
    assert listing.get_json()["data"]["total"] == 0


# --- CA-003: consulta de cliente -------------------------------------------


def test_get_customer_returns_customer_with_addresses(client: FlaskClient) -> None:
    created = client.post(_BASE, json=_customer_payload(addresses=[_address_payload()])).get_json()
    customer_id = created["data"]["id"]

    response = client.get(f"{_BASE}/{customer_id}")

    assert response.status_code == 200
    body = response.get_json()
    assert body["operation"] == "read"
    assert body["data"]["id"] == customer_id
    assert len(body["data"]["addresses"]) == 1


# --- Escenario 5: consultar cliente inexistente ----------------------------


def test_get_customer_returns_404_for_unknown_customer(client: FlaskClient) -> None:
    response = client.get(f"{_BASE}/{uuid.uuid4()}")

    assert response.status_code == 404
    body = response.get_json()
    assert body["success"] is False
    assert body["errors"][0]["code"] == "ERR-003"


def test_get_customer_returns_404_for_already_deleted_customer(client: FlaskClient) -> None:
    created = client.post(_BASE, json=_customer_payload()).get_json()
    customer_id = created["data"]["id"]
    client.delete(f"{_BASE}/{customer_id}")

    response = client.get(f"{_BASE}/{customer_id}")

    assert response.status_code == 404
    assert response.get_json()["errors"][0]["code"] == "ERR-003"


def test_get_customer_returns_400_for_malformed_id(client: FlaskClient) -> None:
    response = client.get(f"{_BASE}/not-a-uuid")

    assert response.status_code == 400
    assert response.get_json()["errors"][0]["code"] == "ERR-001"


# --- CA-008: listado ---------------------------------------------------


def test_list_customers_returns_paginated_items_without_addresses(client: FlaskClient) -> None:
    for i in range(3):
        client.post(
            _BASE,
            json=_customer_payload(identification=f"ID-LIST-{i}", email=f"list{i}@example.com"),
        )

    response = client.get(_BASE, query_string={"page": 1, "page_size": 2})

    assert response.status_code == 200
    body = response.get_json()
    assert body["operation"] == "list"
    assert body["entity_status"] is None
    assert body["data"]["page"] == 1
    assert body["data"]["page_size"] == 2
    assert body["data"]["total"] == 3
    assert len(body["data"]["items"]) == 2
    assert "addresses" not in body["data"]["items"][0]


# --- CA-004: actualización de cliente ---------------------------------------


def test_update_customer_success(client: FlaskClient) -> None:
    created = client.post(_BASE, json=_customer_payload()).get_json()
    customer_id = created["data"]["id"]

    response = client.put(
        f"{_BASE}/{customer_id}",
        json=_customer_payload(name="Ana Actualizada", email="ana.nueva@example.com"),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["operation"] == "update"
    assert body["data"]["name"] == "Ana Actualizada"
    assert body["data"]["email"] == "ana.nueva@example.com"


def test_update_customer_without_changing_email_does_not_trigger_false_duplicate(
    client: FlaskClient,
) -> None:
    created = client.post(_BASE, json=_customer_payload()).get_json()
    customer_id = created["data"]["id"]

    response = client.put(f"{_BASE}/{customer_id}", json=_customer_payload(age=31))

    assert response.status_code == 200
    assert response.get_json()["data"]["age"] == 31


def test_update_customer_rejects_email_belonging_to_another_customer(
    client: FlaskClient,
) -> None:
    client.post(_BASE, json=_customer_payload(identification="ID-A", email="a@example.com"))
    other = client.post(
        _BASE, json=_customer_payload(identification="ID-B", email="b@example.com")
    ).get_json()

    response = client.put(
        f"{_BASE}/{other['data']['id']}",
        json=_customer_payload(identification="ID-B", email="a@example.com"),
    )

    assert response.status_code == 409
    assert response.get_json()["errors"][0]["code"] == "ERR-002"


def test_update_customer_returns_404_for_unknown_customer(client: FlaskClient) -> None:
    response = client.put(f"{_BASE}/{uuid.uuid4()}", json=_customer_payload())

    assert response.status_code == 404
    assert response.get_json()["errors"][0]["code"] == "ERR-003"


# --- Escenario 7 / CA-005: eliminación de cliente ---------------------------


def test_delete_customer_cascades_to_addresses_without_orphaning_them(
    client: FlaskClient,
) -> None:
    created = client.post(
        _BASE,
        json=_customer_payload(
            addresses=[_address_payload(), _address_payload(postal_code="110222")]
        ),
    ).get_json()
    customer_id = created["data"]["id"]

    response = client.delete(f"{_BASE}/{customer_id}")

    assert response.status_code == 200
    body = response.get_json()
    assert body["operation"] == "delete"
    assert body["entity_status"] == "DELETED"
    assert all(a["status"] == "DELETED" for a in body["data"]["addresses"])

    addresses_response = client.get(f"{_BASE}/{customer_id}/addresses")
    assert addresses_response.status_code == 404


def test_delete_customer_returns_404_for_unknown_customer(client: FlaskClient) -> None:
    response = client.delete(f"{_BASE}/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.get_json()["errors"][0]["code"] == "ERR-003"


def test_delete_customer_twice_returns_404_on_second_attempt(client: FlaskClient) -> None:
    created = client.post(_BASE, json=_customer_payload()).get_json()
    customer_id = created["data"]["id"]
    client.delete(f"{_BASE}/{customer_id}")

    second_delete = client.delete(f"{_BASE}/{customer_id}")

    assert second_delete.status_code == 404
    assert second_delete.get_json()["errors"][0]["code"] == "ERR-003"


# --- Rutas/métodos inexistentes: el sobre debe aparecer igual (RN-006) -----


def test_unknown_route_returns_404_wrapped_in_envelope(client: FlaskClient) -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    body = response.get_json()
    _assert_envelope_keys(body)
    assert body["success"] is False


# --- ERR-007: error no controlado -> 500, con el mismo sobre ---------------


def test_unexpected_exception_returns_500_with_envelope() -> None:
    """Verifica el mapeo `ERR-007`/500 de `plan.md` §2.4 de forma determinista.

    Se registra el manejador de errores real (`error_handlers.py`) sobre
    una app Flask desechable con una ruta que fuerza una excepción no
    controlada, sin depender de simular una falla real de infraestructura.
    """
    app = Flask(__name__)
    register_error_handlers(app)

    @app.get("/api/v1/customers/boom")
    def _boom() -> NoReturn:
        raise RuntimeError("Fallo inesperado simulado.")

    test_client = app.test_client()

    response = test_client.get("/api/v1/customers/boom")

    assert response.status_code == 500
    body = response.get_json()
    _assert_envelope_keys(body)
    assert body["success"] is False
    assert body["errors"][0]["code"] == "ERR-007"
