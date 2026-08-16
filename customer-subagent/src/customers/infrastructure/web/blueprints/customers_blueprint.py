from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request

from customers.application.use_cases.create_customer import CreateCustomerUseCase
from customers.application.use_cases.delete_customer import DeleteCustomerUseCase
from customers.application.use_cases.get_customer import GetCustomerUseCase
from customers.application.use_cases.list_customers import ListCustomersUseCase
from customers.application.use_cases.update_customer import UpdateCustomerUseCase
from customers.infrastructure.persistence.repositories import (
    SQLAlchemyCustomerRepository,
)
from customers.infrastructure.web.schemas.customer_schema import (
    parse_create_customer_request,
    parse_update_customer_request,
    serialize_customer,
)

customers_blueprint = Blueprint("customers", __name__, url_prefix="/customers")


def _get_repository() -> SQLAlchemyCustomerRepository:
    if "db_session" not in g:
        session_factory = current_app.config["SESSION_FACTORY"]
        g.db_session = session_factory()
    return SQLAlchemyCustomerRepository(g.db_session)


@customers_blueprint.post("")
def create_customer():
    input_dto = parse_create_customer_request(request.get_json(silent=True))
    output = CreateCustomerUseCase(_get_repository()).execute(input_dto)
    return jsonify(serialize_customer(output)), 201


@customers_blueprint.get("/all")
def list_customers():
    outputs = ListCustomersUseCase(_get_repository()).execute()
    return jsonify([serialize_customer(output) for output in outputs]), 200


@customers_blueprint.get("/<int:customer_id>")
def get_customer(customer_id: int):
    output = GetCustomerUseCase(_get_repository()).execute(customer_id)
    return jsonify(serialize_customer(output)), 200


@customers_blueprint.patch("/<int:customer_id>")
def update_customer(customer_id: int):
    input_dto = parse_update_customer_request(
        customer_id, request.get_json(silent=True)
    )
    output = UpdateCustomerUseCase(_get_repository()).execute(input_dto)
    return jsonify(serialize_customer(output)), 200


@customers_blueprint.delete("/<int:customer_id>")
def delete_customer(customer_id: int):
    DeleteCustomerUseCase(_get_repository()).execute(customer_id)
    return jsonify({}), 200
