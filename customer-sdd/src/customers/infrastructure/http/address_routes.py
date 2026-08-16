"""`Blueprint` HTTP de los endpoints de `Address` (`specs/customers/plan.md` §2.3).

Mismo patrón que `customer_routes.py`: fábricas de casos de uso inyectadas
vía `AddressUseCaseFactories`, nunca instanciadas dentro de la función de
ruta. No depende de `customer_routes.py`: cada caso de uso de `address/*`
ya valida por sí mismo la existencia del cliente (VAL-006).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from flask import Blueprint, Response, jsonify, request

from customers.application.address.create_address import CreateAddress
from customers.application.address.delete_address import DeleteAddress
from customers.application.address.list_addresses import ListAddresses
from customers.application.address.update_address import UpdateAddress
from customers.infrastructure.http.error_handlers import envelope_response
from customers.infrastructure.http.schemas import (
    parse_address_id,
    parse_create_address_request,
    parse_customer_id,
    parse_update_address_request,
)


@dataclass(frozen=True, slots=True)
class AddressUseCaseFactories:
    """Fábricas que construyen, por invocación, una instancia fresca de cada
    caso de uso de `Address` ligada a la sesión de la request en curso.
    """

    create_address: Callable[[], CreateAddress]
    list_addresses: Callable[[], ListAddresses]
    update_address: Callable[[], UpdateAddress]
    delete_address: Callable[[], DeleteAddress]


def create_address_blueprint(use_cases: AddressUseCaseFactories) -> Blueprint:
    """Construye el `Blueprint` de `Address`, inyectando `use_cases`."""
    blueprint = Blueprint("addresses", __name__)

    @blueprint.post("/customers/<customer_id>/addresses")
    def create_address(customer_id: str) -> tuple[Response, int]:
        customer_id_vo = parse_customer_id(customer_id)
        request_dto = parse_create_address_request(request.get_json(silent=True))
        result = use_cases.create_address().execute(customer_id_vo, request_dto)
        body, status = envelope_response(result, success_status=201)
        return jsonify(body), status

    @blueprint.get("/customers/<customer_id>/addresses")
    def list_addresses(customer_id: str) -> tuple[Response, int]:
        customer_id_vo = parse_customer_id(customer_id)
        result = use_cases.list_addresses().execute(customer_id_vo)
        body, status = envelope_response(result, success_status=200)
        return jsonify(body), status

    @blueprint.put("/customers/<customer_id>/addresses/<address_id>")
    def update_address(customer_id: str, address_id: str) -> tuple[Response, int]:
        customer_id_vo = parse_customer_id(customer_id)
        address_id_vo = parse_address_id(address_id)
        request_dto = parse_update_address_request(request.get_json(silent=True))
        result = use_cases.update_address().execute(customer_id_vo, address_id_vo, request_dto)
        body, status = envelope_response(result, success_status=200)
        return jsonify(body), status

    @blueprint.delete("/customers/<customer_id>/addresses/<address_id>")
    def delete_address(customer_id: str, address_id: str) -> tuple[Response, int]:
        customer_id_vo = parse_customer_id(customer_id)
        address_id_vo = parse_address_id(address_id)
        result = use_cases.delete_address().execute(customer_id_vo, address_id_vo)
        body, status = envelope_response(result, success_status=200)
        return jsonify(body), status

    return blueprint
