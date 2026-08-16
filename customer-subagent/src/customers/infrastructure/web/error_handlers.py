from __future__ import annotations

import logging

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from customers.domain.exceptions import (
    AddressAlreadyDeletedError,
    AddressNotFoundError,
    AddressValidationError,
    CustomerAlreadyDeletedError,
    CustomerEmailAlreadyExistsError,
    CustomerNotFoundError,
    CustomerValidationError,
)

logger = logging.getLogger(__name__)

# Los campos internos de Address no siempre coinciden con el nombre literal
# del contrato JSON (ver web/schemas/address_schema.py); se traducen aquí
# para que los mensajes de error sean consistentes con lo que el cliente
# envió, sin importar si el error se originó en el schema o en la entidad.
_ADDRESS_FIELD_API_NAMES = {
    "postal_code": "postalcode",
    "address_line": "address",
}


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(CustomerValidationError)
    def handle_validation_error(error: CustomerValidationError):
        return (
            jsonify(
                {"error": "validation failed", "details": {error.field: error.message}}
            ),
            400,
        )

    @app.errorhandler(CustomerNotFoundError)
    def handle_not_found_error(error: CustomerNotFoundError):
        return jsonify({"error": "customer not found"}), 404

    @app.errorhandler(CustomerAlreadyDeletedError)
    def handle_already_deleted_error(error: CustomerAlreadyDeletedError):
        return jsonify({"error": "customer not found"}), 404

    @app.errorhandler(CustomerEmailAlreadyExistsError)
    def handle_email_conflict_error(error: CustomerEmailAlreadyExistsError):
        return jsonify({"error": "email already exists"}), 409

    @app.errorhandler(AddressValidationError)
    def handle_address_validation_error(error: AddressValidationError):
        field = _ADDRESS_FIELD_API_NAMES.get(error.field, error.field)
        return (
            jsonify({"error": "validation failed", "details": {field: error.message}}),
            400,
        )

    @app.errorhandler(AddressNotFoundError)
    def handle_address_not_found_error(error: AddressNotFoundError):
        return jsonify({"error": "address not found"}), 404

    @app.errorhandler(AddressAlreadyDeletedError)
    def handle_address_already_deleted_error(error: AddressAlreadyDeletedError):
        return jsonify({"error": "address not found"}), 404

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        return error.get_response()

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        logger.exception(
            "unhandled error while processing %s %s", request.method, request.path
        )
        return jsonify({"error": "internal server error"}), 500
