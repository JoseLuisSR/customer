"""Pruebas de integración HTTP end-to-end de los endpoints de `Address`.

Referencias: `specs/customers/implementation-plan.md` §8.1, `specs/customers/
plan.md` §2.3/§2.4/§6.2, `specs/customers/spec.md` §12/§13/§15.

Cubre los escenarios funcionales 3, 4 y 6 (`spec.md` §12) y los criterios de
aceptación CA-006, CA-007 y CA-008 (`spec.md` §15), verificando en cada caso
el sobre de resultado completo y el código HTTP exacto de `plan.md` §2.4.
"""

from __future__ import annotations

import uuid
from typing import Any

from flask.testing import FlaskClient

_CUSTOMERS = "/api/v1/customers"


def _customer_payload(
    *, identification: str = "ID-ADDR-0001", email: str = "cliente@example.com"
) -> dict[str, Any]:
    return {
        "name": "Cliente de Prueba",
        "identification": identification,
        "age": 40,
        "email": email,
    }


def _address_payload(*, postal_code: str = "110111") -> dict[str, Any]:
    return {
        "country": "Colombia",
        "state": "Bogotá D.C.",
        "city": "Bogotá",
        "address": "Calle 123 #45-67",
        "postal_code": postal_code,
    }


def _create_customer(client: FlaskClient, **kwargs: Any) -> str:
    response = client.post(_CUSTOMERS, json=_customer_payload(**kwargs))
    return str(response.get_json()["data"]["id"])


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


# --- Escenario 3 / CA-006: creación exitosa de dirección --------------------


def test_create_address_success(client: FlaskClient) -> None:
    customer_id = _create_customer(client)

    response = client.post(f"{_CUSTOMERS}/{customer_id}/addresses", json=_address_payload())

    assert response.status_code == 201
    body = response.get_json()
    _assert_envelope_keys(body)
    assert body["success"] is True
    assert body["operation"] == "create"
    assert body["entity"] == "address"
    assert body["entity_status"] == "ACTIVE"
    assert body["data"]["customer_id"] == customer_id
    assert uuid.UUID(body["data"]["id"])


def test_create_address_returns_404_for_unknown_customer(client: FlaskClient) -> None:
    response = client.post(f"{_CUSTOMERS}/{uuid.uuid4()}/addresses", json=_address_payload())

    assert response.status_code == 404
    assert response.get_json()["errors"][0]["code"] == "ERR-003"


def test_create_address_rejects_invalid_payload_with_one_error_per_field(
    client: FlaskClient,
) -> None:
    customer_id = _create_customer(client)

    response = client.post(
        f"{_CUSTOMERS}/{customer_id}/addresses",
        json={"country": "", "state": "", "city": "", "address": "", "postal_code": ""},
    )

    assert response.status_code == 400
    body = response.get_json()
    fields_with_errors = {error["field"] for error in body["errors"]}
    assert fields_with_errors == {"country", "state", "city", "address", "postal_code"}


# --- Escenario 4 / CA-007: rechazo de la sexta dirección --------------------


def test_create_address_rejects_sixth_active_address(client: FlaskClient) -> None:
    customer_id = _create_customer(client)
    for i in range(5):
        response = client.post(
            f"{_CUSTOMERS}/{customer_id}/addresses", json=_address_payload(postal_code=f"11000{i}")
        )
        assert response.status_code == 201

    sixth = client.post(
        f"{_CUSTOMERS}/{customer_id}/addresses", json=_address_payload(postal_code="999999")
    )

    assert sixth.status_code == 409
    assert sixth.get_json()["errors"][0]["code"] == "ERR-005"

    listing = client.get(f"{_CUSTOMERS}/{customer_id}/addresses")
    assert len(listing.get_json()["data"]["items"]) == 5


# --- RF-007 / CA-008: listado de direcciones --------------------------------


def test_list_addresses_returns_only_addresses_of_requested_customer(
    client: FlaskClient,
) -> None:
    first_customer = _create_customer(client, identification="ID-A", email="a@example.com")
    second_customer = _create_customer(client, identification="ID-B", email="b@example.com")
    client.post(f"{_CUSTOMERS}/{first_customer}/addresses", json=_address_payload())
    client.post(
        f"{_CUSTOMERS}/{second_customer}/addresses", json=_address_payload(postal_code="220000")
    )

    response = client.get(f"{_CUSTOMERS}/{first_customer}/addresses")

    assert response.status_code == 200
    body = response.get_json()
    assert body["operation"] == "list"
    assert len(body["data"]["items"]) == 1
    assert body["data"]["items"][0]["customer_id"] == first_customer


def test_list_addresses_returns_404_for_unknown_customer(client: FlaskClient) -> None:
    response = client.get(f"{_CUSTOMERS}/{uuid.uuid4()}/addresses")

    assert response.status_code == 404
    assert response.get_json()["errors"][0]["code"] == "ERR-003"


# --- Actualización de dirección ---------------------------------------------


def test_update_address_success(client: FlaskClient) -> None:
    customer_id = _create_customer(client)
    created = client.post(
        f"{_CUSTOMERS}/{customer_id}/addresses", json=_address_payload()
    ).get_json()
    address_id = created["data"]["id"]

    response = client.put(
        f"{_CUSTOMERS}/{customer_id}/addresses/{address_id}",
        json=_address_payload(postal_code="999888"),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["operation"] == "update"
    assert body["data"]["postal_code"] == "999888"


def test_update_address_returns_404_for_unknown_address(client: FlaskClient) -> None:
    customer_id = _create_customer(client)

    response = client.put(
        f"{_CUSTOMERS}/{customer_id}/addresses/{uuid.uuid4()}", json=_address_payload()
    )

    assert response.status_code == 404
    assert response.get_json()["errors"][0]["code"] == "ERR-004"


# --- Escenario 6: dirección ajena a otro cliente ----------------------------


def test_update_address_rejects_address_belonging_to_another_customer(
    client: FlaskClient,
) -> None:
    owner = _create_customer(client, identification="ID-OWNER", email="owner@example.com")
    other = _create_customer(client, identification="ID-OTHER", email="other@example.com")
    created = client.post(f"{_CUSTOMERS}/{owner}/addresses", json=_address_payload()).get_json()
    address_id = created["data"]["id"]

    response = client.put(
        f"{_CUSTOMERS}/{other}/addresses/{address_id}", json=_address_payload(postal_code="1")
    )

    assert response.status_code == 404
    assert response.get_json()["errors"][0]["code"] == "ERR-006"


def test_delete_address_rejects_address_belonging_to_another_customer(
    client: FlaskClient,
) -> None:
    owner = _create_customer(client, identification="ID-OWNER-2", email="owner2@example.com")
    other = _create_customer(client, identification="ID-OTHER-2", email="other2@example.com")
    created = client.post(f"{_CUSTOMERS}/{owner}/addresses", json=_address_payload()).get_json()
    address_id = created["data"]["id"]

    response = client.delete(f"{_CUSTOMERS}/{other}/addresses/{address_id}")

    assert response.status_code == 404
    assert response.get_json()["errors"][0]["code"] == "ERR-006"


# --- Eliminación de dirección ------------------------------------------------


def test_delete_address_success(client: FlaskClient) -> None:
    customer_id = _create_customer(client)
    created = client.post(
        f"{_CUSTOMERS}/{customer_id}/addresses", json=_address_payload()
    ).get_json()
    address_id = created["data"]["id"]

    response = client.delete(f"{_CUSTOMERS}/{customer_id}/addresses/{address_id}")

    assert response.status_code == 200
    body = response.get_json()
    assert body["operation"] == "delete"
    assert body["entity_status"] == "DELETED"

    listing = client.get(f"{_CUSTOMERS}/{customer_id}/addresses")
    assert listing.get_json()["data"]["items"] == []


def test_delete_address_returns_404_for_unknown_address(client: FlaskClient) -> None:
    customer_id = _create_customer(client)

    response = client.delete(f"{_CUSTOMERS}/{customer_id}/addresses/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.get_json()["errors"][0]["code"] == "ERR-004"


def test_delete_address_twice_returns_404_on_second_attempt(client: FlaskClient) -> None:
    customer_id = _create_customer(client)
    created = client.post(
        f"{_CUSTOMERS}/{customer_id}/addresses", json=_address_payload()
    ).get_json()
    address_id = created["data"]["id"]
    client.delete(f"{_CUSTOMERS}/{customer_id}/addresses/{address_id}")

    second_delete = client.delete(f"{_CUSTOMERS}/{customer_id}/addresses/{address_id}")

    assert second_delete.status_code == 404
    assert second_delete.get_json()["errors"][0]["code"] == "ERR-004"


# --- Identificador de ruta malformado ---------------------------------------


def test_invalid_address_id_in_path_returns_400(client: FlaskClient) -> None:
    customer_id = _create_customer(client)

    response = client.put(
        f"{_CUSTOMERS}/{customer_id}/addresses/not-a-uuid", json=_address_payload()
    )

    assert response.status_code == 400
    assert response.get_json()["errors"][0]["code"] == "ERR-001"
