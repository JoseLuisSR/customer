"""Manejadores de error HTTP centralizados (`specs/customers/plan.md` §2.4).

Traduce a HTTP:

- `RequestParsingError` (`schemas.py`): forma/tipo inválido del JSON de
  entrada o de un identificador de ruta -> `ERR-001`/400.
- `DuplicateEmailError`/`DuplicateIdentificationError`: las únicas
  excepciones de dominio que pueden escapar de los adaptadores de
  persistencia (condición de carrera entre la verificación de unicidad en
  la capa de aplicación y el `flush()` real, ver `infrastructure/
  persistence/customer_repository.py`) -> `ERR-002`/`ERR-008`, 409.
- `werkzeug.HTTPException` (ruta inexistente, método no permitido, etc.):
  se conserva su código HTTP original, pero se envuelve en el mismo sobre
  de resultado (RN-006 exige el sobre "en todas las respuestas").
- Cualquier otra excepción no controlada -> `ERR-007`/500, con el detalle
  completo solo en logs (nunca en la respuesta al cliente).

También expone `status_for_result`/`envelope_response`, usados por
`customer_routes.py`/`address_routes.py` para traducir el `OperationResult`
de un caso de uso exitoso (o fallido por una regla de negocio normal, sin
excepción) al mismo mapeo de códigos de esta sección, evitando duplicar la
tabla `plan.md` §2.4 en dos lugares.
"""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import HTTPException

from customers.application.error_codes import ERR_DUPLICATE_EMAIL, ERR_DUPLICATE_IDENTIFICATION
from customers.application.operation_result import Entity, Operation, OperationResult
from customers.domain.customer.exceptions import DuplicateEmailError, DuplicateIdentificationError
from customers.domain.shared.validation import FieldError
from customers.infrastructure.http.response_envelope import build_envelope
from customers.infrastructure.http.schemas import RequestParsingError

logger = logging.getLogger(__name__)

# Mapeo completo de `plan.md` §2.4. Los códigos `VAL-00X` (producidos por
# los value objects de dominio) se agrupan bajo la categoría funcional
# ERR-001 (400): "Datos obligatorios inválidos/ausentes".
_STATUS_BY_EXACT_CODE: dict[str, int] = {
    "ERR-001": 400,
    "ERR-002": 409,
    "ERR-003": 404,
    "ERR-004": 404,
    "ERR-005": 409,
    "ERR-006": 404,
    "ERR-007": 500,
    "ERR-008": 409,  # provisional, ver domain/customer/exceptions.py::DuplicateIdentificationError
}


def status_for_code(code: str) -> int:
    """Resuelve el código HTTP para un código funcional `VAL-00X`/`ERR-00X`."""
    if code.startswith("VAL-"):
        return 400
    return _STATUS_BY_EXACT_CODE.get(code, 500)


def status_for_result(result: OperationResult, *, success_status: int = 200) -> int:
    """Resuelve el código HTTP de una respuesta a partir de su `OperationResult`.

    En éxito, usa `success_status` (201 para creación, 200 para el resto,
    decidido por la ruta). En fallo, usa el código del primer `FieldError`
    de `result.errors` (en la práctica, cada `OperationResult.fail(...)` de
    la capa de aplicación construye `errors` con una única categoría de
    código a la vez: o bien varios `VAL-00X` de campo, o bien un único
    `ERR-00X` de regla de negocio, nunca una mezcla).
    """
    if result.success:
        return success_status
    if not result.errors:
        return 500
    return status_for_code(result.errors[0].code)


def envelope_response(
    result: OperationResult, *, success_status: int = 200
) -> tuple[dict[str, Any], int]:
    """Construye `(sobre_json, status_http)` para cualquier `OperationResult`."""
    return build_envelope(result), status_for_result(result, success_status=success_status)


def _infer_operation() -> Operation:
    """Infiere la `Operation` de la request en curso, para envolver
    excepciones que no llevan asociado un `OperationResult` ya construido
    por un caso de uso (p. ej. errores de forma del JSON o condiciones de
    carrera de unicidad).
    """
    method = request.method
    if method == "POST":
        return Operation.CREATE
    if method == "PUT":
        return Operation.UPDATE
    if method == "DELETE":
        return Operation.DELETE
    path = request.path.rstrip("/")
    if path.endswith("/customers") or path.endswith("/addresses"):
        return Operation.LIST
    return Operation.READ


def _infer_entity() -> Entity:
    return Entity.ADDRESS if "/addresses" in request.path else Entity.CUSTOMER


def register_error_handlers(app: Flask) -> None:
    """Registra los manejadores de excepción no controlada de Flask."""

    @app.errorhandler(RequestParsingError)
    def _handle_request_parsing_error(exc: RequestParsingError) -> tuple[Response, int]:
        result = OperationResult.fail(
            operation=_infer_operation(),
            entity=_infer_entity(),
            message="El cuerpo o los parámetros de la petición no son válidos.",
            errors=exc.errors,
        )
        body, status = envelope_response(result)
        return jsonify(body), status

    @app.errorhandler(DuplicateEmailError)
    def _handle_duplicate_email(exc: DuplicateEmailError) -> tuple[Response, int]:
        logger.warning(
            "Correo duplicado detectado al persistir (condición de carrera): %s %s.",
            request.method,
            request.path,
        )
        result = OperationResult.fail(
            operation=_infer_operation(),
            entity=Entity.CUSTOMER,
            message=str(exc),
            errors=[FieldError(code=ERR_DUPLICATE_EMAIL, field="email", message=str(exc))],
        )
        body, status = envelope_response(result)
        return jsonify(body), status

    @app.errorhandler(DuplicateIdentificationError)
    def _handle_duplicate_identification(
        exc: DuplicateIdentificationError,
    ) -> tuple[Response, int]:
        logger.warning(
            "Identificación duplicada detectada al persistir (condición de carrera): %s %s.",
            request.method,
            request.path,
        )
        result = OperationResult.fail(
            operation=_infer_operation(),
            entity=Entity.CUSTOMER,
            message=str(exc),
            errors=[
                FieldError(
                    code=ERR_DUPLICATE_IDENTIFICATION, field="identification", message=str(exc)
                )
            ],
        )
        body, status = envelope_response(result)
        return jsonify(body), status

    @app.errorhandler(HTTPException)
    def _handle_http_exception(exc: HTTPException) -> tuple[Response, int]:
        # Errores del propio framework (404 de ruta inexistente, 405 método
        # no permitido, etc.): no forman parte del catálogo VAL-00X/ERR-00X
        # de `plan.md` §2.4, pero igualmente deben usar el sobre de
        # resultado (RN-006: "todas las respuestas").
        result = OperationResult.fail(
            operation=_infer_operation(),
            entity=_infer_entity(),
            message=exc.description or exc.name or "Error HTTP.",
            errors=[],
        )
        body = build_envelope(result)
        return jsonify(body), exc.code or 500

    @app.errorhandler(Exception)
    def _handle_unexpected_error(exc: Exception) -> tuple[Response, int]:
        logger.exception("Error no controlado al procesar %s %s.", request.method, request.path)
        result = OperationResult.fail(
            operation=_infer_operation(),
            entity=_infer_entity(),
            message="Ocurrió un error inesperado. Intente nuevamente más tarde.",
            errors=[FieldError(code="ERR-007", field=None, message="Error interno del servidor.")],
        )
        body, status = envelope_response(result)
        return jsonify(body), status
