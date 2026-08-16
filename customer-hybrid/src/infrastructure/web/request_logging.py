# adapters/inbound/flask/request_logging.py

import logging
import time
import uuid

from flask import Flask, g, request

logger = logging.getLogger(__name__)


def register_request_logging(app: Flask) -> None:

    @app.before_request
    def start_request() -> None:
        g.request_id = request.headers.get(
            "X-Request-ID",
            str(uuid.uuid4()),
        )
        g.started_at = time.perf_counter()

    @app.after_request
    def finish_request(response):
        duration_ms = (time.perf_counter() - g.started_at) * 1000

        logger.info(
            "HTTP request completed: request_id=%s method=%s "
            "path=%s status=%s duration_ms=%.2f",
            g.request_id,
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )

        response.headers["X-Request-ID"] = g.request_id
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception(
            "Unexpected error request_id=%s method=%s path=%s",
            getattr(g, "request_id", "unknown"),
            request.method,
            request.path,
        )

        return {
            "error": "Internal server error",
            "request_id": getattr(g, "request_id", None),
        }, 500
