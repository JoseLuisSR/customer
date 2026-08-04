from http import HTTPStatus

from flask import Flask, jsonify

from src.exception.customer_exception import (
    CustomerNotFoundError,
    CustomerWithIDAlreadyExistsError,
    InvalidUUIDError,
    PersistenceUnavailableError,
)


def handle_customer_not_found_error(exception: CustomerNotFoundError):
    return jsonify(
        {
            "error": {
                "code": "USER_NOT_FOUND",
                "message": str(exception),
                "customer_id": str(exception.id),
            }
        }
    ), HTTPStatus.NOT_FOUND


def handle_invalid_uuid_error(exception: InvalidUUIDError):
    return jsonify(
        {
            "error": {
                "code": "INVALID_UUID",
                "message": str(exception),
                "uuid": str(exception.value),
            }
        }
    ), HTTPStatus.BAD_REQUEST


def handle_customer_with_uuid_already_exists_error(
    exception: CustomerWithIDAlreadyExistsError,
):
    return jsonify(
        {
            "error": {
                "code": "CUSTOMER_WITH_ID_ALREADY_EXISTS",
                "message": str(exception),
                "uuid": str(exception.id),
            }
        }
    ), HTTPStatus.CONFLICT


def handle_persistence_unavailable_error(exception: PersistenceUnavailableError):
    return jsonify(
        {"error": {"code": "SERVICE_UNAVAILABLE", "message": str(exception)}}
    ), HTTPStatus.SERVICE_UNAVAILABLE


def register_exception_handlers(app: Flask) -> None:

    app.register_error_handler(CustomerNotFoundError, handle_customer_not_found_error)
    app.register_error_handler(InvalidUUIDError, handle_invalid_uuid_error)
    app.register_error_handler(
        CustomerWithIDAlreadyExistsError, handle_customer_with_uuid_already_exists_error
    )
    app.register_error_handler(
        PersistenceUnavailableError, handle_persistence_unavailable_error
    )
