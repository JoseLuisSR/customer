"""Pruebas de concurrencia real contra Postgres (casos límite `spec.md` §16).

Referencias: `specs/customers/implementation-plan.md` §8.1, `specs/customers/
plan.md` §1.4/§6.2.

Usa `concurrent.futures.ThreadPoolExecutor` (librería estándar) para
disparar pares de requests HTTP verdaderamente concurrentes contra la app
completa (`client`, `app.test_client()`), verificando que exactamente una
de las dos operaciones concurrentes tiene éxito en cada caso:

1. Dos altas de cliente simultáneas con el mismo `email`.
2. Dos altas de cliente simultáneas con la misma `identification`.
3. Dos altas de dirección simultáneas que compiten por la 5ª/6ª dirección
   de un mismo cliente.

`db.get_session()` es un `scoped_session` cuyo ámbito por defecto es el
hilo actual (`threading.get_ident`), así que cada hilo de este módulo
obtiene su propia `Session`/conexión real, permitiendo ejercitar las
protecciones de concurrencia documentadas en `plan.md` §1.4 (constraints
`UNIQUE` atómicas para email/identification, bloqueo pesimista
`SELECT ... FOR UPDATE` para el límite de direcciones).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from flask.testing import FlaskClient

_CUSTOMERS = "/api/v1/customers"


def _customer_payload(*, identification: str, email: str) -> dict[str, Any]:
    return {
        "name": "Cliente Concurrente",
        "identification": identification,
        "age": 35,
        "email": email,
    }


def _address_payload(*, postal_code: str) -> dict[str, Any]:
    return {
        "country": "Colombia",
        "state": "Bogotá D.C.",
        "city": "Bogotá",
        "address": "Calle 123 #45-67",
        "postal_code": postal_code,
    }


def test_concurrent_customer_creation_with_same_email_only_one_succeeds(
    client: FlaskClient,
) -> None:
    payloads = [
        _customer_payload(identification="ID-CONC-EMAIL-1", email="mismo@example.com"),
        _customer_payload(identification="ID-CONC-EMAIL-2", email="mismo@example.com"),
    ]

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(lambda payload: client.post(_CUSTOMERS, json=payload), payloads)
        )

    statuses = sorted(response.status_code for response in responses)
    assert statuses == [201, 409]

    failed = next(r for r in responses if r.status_code == 409)
    assert failed.get_json()["errors"][0]["code"] == "ERR-002"

    listing = client.get(_CUSTOMERS)
    assert listing.get_json()["data"]["total"] == 1


def test_concurrent_customer_creation_with_same_identification_only_one_succeeds(
    client: FlaskClient,
) -> None:
    payloads = [
        _customer_payload(identification="ID-CONC-DUP", email="uno-conc@example.com"),
        _customer_payload(identification="ID-CONC-DUP", email="dos-conc@example.com"),
    ]

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(lambda payload: client.post(_CUSTOMERS, json=payload), payloads)
        )

    statuses = sorted(response.status_code for response in responses)
    assert statuses == [201, 409]

    failed = next(r for r in responses if r.status_code == 409)
    assert failed.get_json()["errors"][0]["code"] == "ERR-008"

    listing = client.get(_CUSTOMERS)
    assert listing.get_json()["data"]["total"] == 1


def test_concurrent_address_creation_competing_for_sixth_slot_only_one_succeeds(
    client: FlaskClient,
) -> None:
    created = client.post(
        _CUSTOMERS,
        json=_customer_payload(identification="ID-CONC-ADDR", email="conc-addr@example.com"),
    ).get_json()
    customer_id = created["data"]["id"]

    for i in range(4):
        response = client.post(
            f"{_CUSTOMERS}/{customer_id}/addresses",
            json=_address_payload(postal_code=f"40000{i}"),
        )
        assert response.status_code == 201

    competing_payloads = [
        _address_payload(postal_code="500005"),
        _address_payload(postal_code="500006"),
    ]

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(
                lambda payload: client.post(f"{_CUSTOMERS}/{customer_id}/addresses", json=payload),
                competing_payloads,
            )
        )

    statuses = sorted(response.status_code for response in responses)
    assert statuses == [201, 409]

    failed = next(r for r in responses if r.status_code == 409)
    assert failed.get_json()["errors"][0]["code"] == "ERR-005"

    listing = client.get(f"{_CUSTOMERS}/{customer_id}/addresses")
    assert len(listing.get_json()["data"]["items"]) == 5
