import uuid
from http import HTTPStatus

from flask import Blueprint, Response, request

from src.application.dto.address_dto import AddressPatchRqst, AddressRqst
from src.application.repository.address_repository import AddressRepository
from src.application.services.address_service import AddressService
from src.infrastructure.persistence.database_address_repository import (
    DatabaseAddressRepository,
)
from src.infrastructure.web.uuid_parser import parse_uuid

address_bp = Blueprint(
    "address",
    __name__,
    url_prefix="/api/v1/customers/<string:customer_id>/addresses",
)
address_repository: AddressRepository = DatabaseAddressRepository()
address_service = AddressService(address_repository)


@address_bp.post("")
def create(customer_id: str):
    customer_uuid: uuid.UUID = parse_uuid(customer_id)
    address_rqst = AddressRqst.model_validate(request.get_json())
    address_rsps = address_service.create(customer_uuid, address_rqst)
    return address_rsps.model_dump(by_alias=True), HTTPStatus.CREATED


@address_bp.get("/all")
def get_all(customer_id: str):
    customer_uuid: uuid.UUID = parse_uuid(customer_id)
    responses = address_service.get_all(customer_uuid)
    return [response.model_dump(by_alias=True) for response in responses], HTTPStatus.OK


@address_bp.get("/<string:address_id>")
def get_by_id(customer_id: str, address_id: str):
    customer_uuid: uuid.UUID = parse_uuid(customer_id)
    address_uuid: uuid.UUID = parse_uuid(address_id)
    address_rsps = address_service.get_by_id(customer_uuid, address_uuid)
    return address_rsps.model_dump(by_alias=True), HTTPStatus.OK


@address_bp.patch("/<string:address_id>")
def update_partial(customer_id: str, address_id: str):
    customer_uuid: uuid.UUID = parse_uuid(customer_id)
    address_uuid: uuid.UUID = parse_uuid(address_id)
    address_patch_rqst = AddressPatchRqst.model_validate(request.get_json())
    address_rsps = address_service.update_partial(
        customer_uuid, address_uuid, address_patch_rqst
    )
    return address_rsps.model_dump(by_alias=True), HTTPStatus.OK


@address_bp.put("/<string:address_id>")
def replace(customer_id: str, address_id: str):
    customer_uuid: uuid.UUID = parse_uuid(customer_id)
    address_uuid: uuid.UUID = parse_uuid(address_id)
    address_rqst = AddressRqst.model_validate(request.get_json())
    address_rsps, created = address_service.replace(
        customer_uuid, address_uuid, address_rqst
    )
    status = HTTPStatus.CREATED if created else HTTPStatus.OK
    return address_rsps.model_dump(by_alias=True), status


@address_bp.delete("/<string:address_id>")
def delete_by_id(customer_id: str, address_id: str):
    customer_uuid: uuid.UUID = parse_uuid(customer_id)
    address_uuid: uuid.UUID = parse_uuid(address_id)
    address_service.delete_by_id(customer_uuid, address_uuid)
    return Response(status=HTTPStatus.NO_CONTENT)
