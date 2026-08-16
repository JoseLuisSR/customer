"""Application factory de Flask (`specs/customers/plan.md` §4/§5.2).

`create_app()` ensambla la aplicación HTTP completa: registra los
`Blueprint` de `Customer`/`Address` bajo `/api/v1`, los manejadores de
error centralizados (`error_handlers.py`) y conecta el ciclo de vida de la
sesión de SQLAlchemy con el ciclo de vida de cada request.

**Inyección de dependencias:** los casos de uso (Fase 2) se inyectan en
los blueprints (Fase 4) a través de fábricas de un solo uso
(`CustomerUseCaseFactories`/`AddressUseCaseFactories`, ver
`customer_routes.py`/`address_routes.py`). Cada fábrica construye, en el
momento de invocarla dentro de una función de ruta, una instancia fresca
del caso de uso ligada a `db.get_session()` -que devuelve la sesión
`scoped_session` asociada al hilo/scope de la request en curso, la misma
en todas las llamadas dentro de una misma request-, para que operaciones
que tocan ambos repositorios (p. ej. `CreateCustomer` con direcciones
embebidas) queden en una única transacción atómica.
"""

from __future__ import annotations

import logging

from flask import Flask

from customers.application.address.create_address import CreateAddress
from customers.application.address.delete_address import DeleteAddress
from customers.application.address.list_addresses import ListAddresses
from customers.application.address.update_address import UpdateAddress
from customers.application.customer.create_customer import CreateCustomer
from customers.application.customer.delete_customer import DeleteCustomer
from customers.application.customer.get_customer import GetCustomer
from customers.application.customer.list_customers import ListCustomers
from customers.application.customer.update_customer import UpdateCustomer
from customers.domain.address.repository import AddressRepository
from customers.domain.customer.repository import CustomerRepository
from customers.infrastructure.config import get_config
from customers.infrastructure.http.address_routes import (
    AddressUseCaseFactories,
    create_address_blueprint,
)
from customers.infrastructure.http.customer_routes import (
    CustomerUseCaseFactories,
    create_customer_blueprint,
)
from customers.infrastructure.http.error_handlers import register_error_handlers
from customers.infrastructure.logging_config import configure_logging
from customers.infrastructure.persistence import db
from customers.infrastructure.persistence.address_repository import SqlAlchemyAddressRepository
from customers.infrastructure.persistence.customer_repository import SqlAlchemyCustomerRepository

logger = logging.getLogger(__name__)

_API_PREFIX = "/api/v1"


def create_app() -> Flask:
    """Construye y configura la aplicación Flask (destino de `gunicorn main:app`)."""
    configure_logging()
    get_config()  # falla rápido si DATABASE_URL/LOG_LEVEL no son válidos
    db.init_engine()

    app = Flask(__name__)

    def build_customer_repository() -> CustomerRepository:
        return SqlAlchemyCustomerRepository(db.get_session())

    def build_address_repository() -> AddressRepository:
        return SqlAlchemyAddressRepository(db.get_session())

    customer_use_cases = CustomerUseCaseFactories(
        create_customer=lambda: CreateCustomer(
            build_customer_repository(), build_address_repository()
        ),
        get_customer=lambda: GetCustomer(build_customer_repository(), build_address_repository()),
        list_customers=lambda: ListCustomers(build_customer_repository()),
        update_customer=lambda: UpdateCustomer(
            build_customer_repository(), build_address_repository()
        ),
        delete_customer=lambda: DeleteCustomer(
            build_customer_repository(), build_address_repository()
        ),
    )
    address_use_cases = AddressUseCaseFactories(
        create_address=lambda: CreateAddress(
            build_customer_repository(), build_address_repository()
        ),
        list_addresses=lambda: ListAddresses(
            build_customer_repository(), build_address_repository()
        ),
        update_address=lambda: UpdateAddress(
            build_customer_repository(), build_address_repository()
        ),
        delete_address=lambda: DeleteAddress(
            build_customer_repository(), build_address_repository()
        ),
    )

    app.register_blueprint(create_customer_blueprint(customer_use_cases), url_prefix=_API_PREFIX)
    app.register_blueprint(create_address_blueprint(address_use_cases), url_prefix=_API_PREFIX)
    register_error_handlers(app)

    @app.teardown_appcontext
    def _teardown_session(exception: BaseException | None) -> None:
        """Cierra el ciclo de vida transaccional de la sesión al final de cada request.

        Intenta `commit()` (cubre tanto el camino exitoso como una
        respuesta de negocio fallida pero controlada,
        `OperationResult.success = False`, que no deja cambios pendientes
        en la sesión). Si el `commit()` falla (p. ej. una excepción no
        controlada dejó la sesión con una transacción abortada) o Flask
        reporta una excepción, hace `rollback()` en su lugar.
        `remove_session()` siempre libera al final la sesión ligada al
        hilo/scope actual, evitando fugas entre requests.
        """
        session = db.get_session()
        try:
            if exception is None:
                session.commit()
            else:
                session.rollback()
        except Exception:
            logger.exception("Error al finalizar la sesión de la request; se revierte.")
            session.rollback()
        finally:
            db.remove_session()

    logger.info("Aplicación Flask inicializada (Config: FLASK_ENV=%s).", get_config().flask_env)
    return app
