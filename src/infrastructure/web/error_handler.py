from http import HTTPStatus

from flask import Flask, jsonify

from src.exception.customer_exception import (
    CustomerNotFoundException,
    InvalidUUIDException,
)


def handle_customer_not_found(exception: CustomerNotFoundException):
    return jsonify(
        {
            "error": {
                "code": "USER_NOT_FOUND",
                "message": str(exception),
                "customer_id": str(exception.id),
            }
        }
    ), HTTPStatus.NOT_FOUND


def handle_invalid_uuid(exception: InvalidUUIDException):
    return jsonify(
        {
            "error": {
                "code": "INVALID_UUID",
                "message": str(exception),
                "uuid": str(exception.value),
            }
        }
    ), HTTPStatus.BAD_REQUEST


def register_exception_handlers(app: Flask) -> None:

    app.register_error_handler(CustomerNotFoundException, handle_customer_not_found)
    app.register_error_handler(InvalidUUIDException, handle_invalid_uuid)
