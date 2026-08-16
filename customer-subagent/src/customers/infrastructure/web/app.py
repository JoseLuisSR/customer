from __future__ import annotations

from flask import Flask, g

from customers.infrastructure.config.settings import Settings
from customers.infrastructure.persistence.database import (
    create_session_factory,
    create_sqlalchemy_engine,
)
from customers.infrastructure.web.blueprints.addresses_blueprint import (
    addresses_blueprint,
)
from customers.infrastructure.web.blueprints.customers_blueprint import (
    customers_blueprint,
)
from customers.infrastructure.web.error_handlers import register_error_handlers
from customers.infrastructure.web.logging_config import configure_logging


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or Settings.from_env()
    configure_logging(settings)

    app = Flask(__name__)
    engine = create_sqlalchemy_engine(settings.database_url)
    app.config["SESSION_FACTORY"] = create_session_factory(engine)

    @app.teardown_appcontext
    def close_db_session(exception: BaseException | None = None) -> None:
        session = g.pop("db_session", None)
        if session is not None:
            session.close()

    app.register_blueprint(customers_blueprint)
    app.register_blueprint(addresses_blueprint)
    register_error_handlers(app)

    return app
