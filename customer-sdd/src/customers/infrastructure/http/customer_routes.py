"""`Blueprint` HTTP de los endpoints de `Customer` (`specs/customers/plan.md` §2.2).

Cada función de ruta parsea el request con `schemas.py`, invoca el caso de
uso correspondiente -obtenido de las fábricas inyectadas en
`CustomerUseCaseFactories`, nunca instanciado directamente aquí- y
construye la respuesta con `response_envelope.py`/`error_handlers.py`.

Las fábricas (en vez de instancias ya construidas) permiten que cada
invocación obtenga un caso de uso ligado a la sesión de SQLAlchemy de la
request en curso (`infrastructure/flask_app.py` decide qué repositorios
concretos inyectar).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from flask import Blueprint, Response, jsonify, request

from customers.application.customer.create_customer import CreateCustomer
from customers.application.customer.delete_customer import DeleteCustomer
from customers.application.customer.get_customer import GetCustomer
from customers.application.customer.list_customers import ListCustomers
from customers.application.customer.update_customer import UpdateCustomer
from customers.infrastructure.http.error_handlers import envelope_response
from customers.infrastructure.http.schemas import (
    parse_customer_create_request,
    parse_customer_id,
    parse_customer_update_request,
    parse_list_customers_request,
)


@dataclass(frozen=True, slots=True)
class CustomerUseCaseFactories:
    """Fábricas que construyen, por invocación, una instancia fresca de cada
    caso de uso de `Customer` ligada a la sesión de la request en curso.
    """

    create_customer: Callable[[], CreateCustomer]
    get_customer: Callable[[], GetCustomer]
    list_customers: Callable[[], ListCustomers]
    update_customer: Callable[[], UpdateCustomer]
    delete_customer: Callable[[], DeleteCustomer]


def create_customer_blueprint(use_cases: CustomerUseCaseFactories) -> Blueprint:
    """Construye el `Blueprint` de `Customer`, inyectando `use_cases`."""
    blueprint = Blueprint("customers", __name__)

    @blueprint.post("/customers")
    def create_customer() -> tuple[Response, int]:
        request_dto = parse_customer_create_request(request.get_json(silent=True))
        result = use_cases.create_customer().execute(request_dto)
        body, status = envelope_response(result, success_status=201)
        return jsonify(body), status

    @blueprint.get("/customers/<customer_id>")
    def get_customer(customer_id: str) -> tuple[Response, int]:
        customer_id_vo = parse_customer_id(customer_id)
        result = use_cases.get_customer().execute(customer_id_vo)
        body, status = envelope_response(result, success_status=200)
        return jsonify(body), status

    @blueprint.get("/customers")
    def list_customers() -> tuple[Response, int]:
        request_dto = parse_list_customers_request(request.args)
        result = use_cases.list_customers().execute(request_dto)
        body, status = envelope_response(result, success_status=200)
        return jsonify(body), status

    @blueprint.put("/customers/<customer_id>")
    def update_customer(customer_id: str) -> tuple[Response, int]:
        customer_id_vo = parse_customer_id(customer_id)
        request_dto = parse_customer_update_request(request.get_json(silent=True))
        result = use_cases.update_customer().execute(customer_id_vo, request_dto)
        body, status = envelope_response(result, success_status=200)
        return jsonify(body), status

    @blueprint.delete("/customers/<customer_id>")
    def delete_customer(customer_id: str) -> tuple[Response, int]:
        customer_id_vo = parse_customer_id(customer_id)
        result = use_cases.delete_customer().execute(customer_id_vo)
        body, status = envelope_response(result, success_status=200)
        return jsonify(body), status

    return blueprint
