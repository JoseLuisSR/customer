from flask import Flask

from src.infrastructure.persistence.config import Config
from src.infrastructure.persistence.database import db
from src.infrastructure.web.customer_routes import customer_bp
from src.infrastructure.web.error_handler import register_exception_handlers


def create_app() -> Flask:
    app: Flask = Flask(__name__)
    app.register_blueprint(customer_bp)
    app.config.from_object(Config)
    db.init_app(app)
    register_exception_handlers(app)
    return app
