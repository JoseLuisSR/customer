from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request

from customers.application.use_cases.create_address import CreateAddressUseCase
from customers.application.use_cases.delete_address import DeleteAddressUseCase
from customers.application.use_cases.get_address import GetAddressUseCase
from customers.application.use_cases.list_addresses import ListAddressesUseCase
from customers.application.use_cases.update_address import UpdateAddressUseCase
from customers.infrastructure.persistence.repositories import (
    SQLAlchemyAddressRepository,
    SQLAlchemyCustomerRepository,
)
from customers.infrastructure.web.schemas.address_schema import (
    parse_create_address_request,
    parse_update_address_request,
    serialize_address,
)

addresses_blueprint = Blueprint(
    "addresses", __name__, url_prefix="/customers/<int:customer_id>/addresses"
)


def _get_repositories() -> tuple[
    SQLAlchemyCustomerRepository, SQLAlchemyAddressRepository
]:
    if "db_session" not in g:
        session_factory = current_app.config["SESSION_FACTORY"]
        g.db_session = session_factory()
    session = g.db_session
    return SQLAlchemyCustomerRepository(session), SQLAlchemyAddressRepository(session)


@addresses_blueprint.post("")
def create_address(customer_id: int):
    customer_repository, address_repository = _get_repositories()
    input_dto = parse_create_address_request(customer_id, request.get_json(silent=True))
    output = CreateAddressUseCase(customer_repository, address_repository).execute(
        input_dto
    )
    return jsonify(serialize_address(output)), 201


@addresses_blueprint.get("")
def list_addresses(customer_id: int):
    customer_repository, address_repository = _get_repositories()
    outputs = ListAddressesUseCase(customer_repository, address_repository).execute(
        customer_id
    )
    return jsonify([serialize_address(output) for output in outputs]), 200


@addresses_blueprint.get("/<int:address_id>")
def get_address(customer_id: int, address_id: int):
    customer_repository, address_repository = _get_repositories()
    output = GetAddressUseCase(customer_repository, address_repository).execute(
        customer_id, address_id
    )
    return jsonify(serialize_address(output)), 200


@addresses_blueprint.patch("/<int:address_id>")
def update_address(customer_id: int, address_id: int):
    customer_repository, address_repository = _get_repositories()
    input_dto = parse_update_address_request(
        customer_id, address_id, request.get_json(silent=True)
    )
    output = UpdateAddressUseCase(customer_repository, address_repository).execute(
        input_dto
    )
    return jsonify(serialize_address(output)), 200


@addresses_blueprint.delete("/<int:address_id>")
def delete_address(customer_id: int, address_id: int):
    customer_repository, address_repository = _get_repositories()
    DeleteAddressUseCase(customer_repository, address_repository).execute(
        customer_id, address_id
    )
    return jsonify({}), 200
