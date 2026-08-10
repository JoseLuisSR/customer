from http import HTTPStatus

from flask import Flask, jsonify

from src.infrastructure.logging.config import configure_logging
from src.infrastructure.persistence.config import Config
from src.infrastructure.persistence.database import db
from src.infrastructure.web.customer_routes import customer_bp
from src.infrastructure.web.error_handler import register_exception_handlers
from src.infrastructure.web.request_logging import register_request_logging


def create_app() -> Flask:
    configure_logging()
    app: Flask = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), HTTPStatus.OK

    app.register_blueprint(customer_bp)
    app.config.from_object(Config)
    db.init_app(app)
    register_exception_handlers(app)
    register_request_logging(app)
    return app
