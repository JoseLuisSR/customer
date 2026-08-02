import uuid
from http import HTTPStatus

from flask import Blueprint, Response, request

from src.application.dto.customer_dto import CustomerRqst
from src.application.repository.customer_repository import CustomerRepository
from src.application.services.customer_service import CustomerService
from src.exception.customer_exception import InvalidUUIDException
from src.infrastructure.persistence.database_customer_repository import (
    DatabaseCustomerRepository,
)

customer_bp = Blueprint("cusromer", __name__, url_prefix="/api/v1/customers")
customer_repository: CustomerRepository = DatabaseCustomerRepository()
customer_service = CustomerService(customer_repository)


@customer_bp.post("")
def create():
    customer_rqst = CustomerRqst.model_validate(request.get_json())
    customer_rsps = customer_service.create(customer_rqst)
    return customer_rsps.model_dump(), 201


@customer_bp.get("/<string:value>")
def get_by_id(value: str):
    customer_id: uuid.UUID = parse_uuid(value)
    return customer_service.get_by_id(customer_id).model_dump(), 200


@customer_bp.get("/all")
def get_all():
    responses = customer_service.get_all()
    return [response.model_dump() for response in responses], HTTPStatus.OK


@customer_bp.delete("/<string:value>")
def delete_by_id(value: str):
    customer_id: uuid.UUID = parse_uuid(value)
    customer_service.delete_by_id(customer_id)
    return Response(status=HTTPStatus.NO_CONTENT)


def parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError, TypeError) as error:
        raise InvalidUUIDException(value) from error
