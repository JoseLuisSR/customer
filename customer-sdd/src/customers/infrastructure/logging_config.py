"""Configuración de logging estándar de la aplicación.

Nivel controlado por `LOG_LEVEL` (`infrastructure/config.py`). Ningún
mensaje de log de esta capa debe incluir datos sensibles (contraseñas,
tokens, cadenas de conexión completas, cuerpos crudos de request).
"""

from __future__ import annotations

import logging

from customers.infrastructure.config import get_config

_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

_APP_LOGGER_NAME = "customers"


def configure_logging() -> None:
    """Configura el logging raíz del proceso según `LOG_LEVEL`.

    Idempotente: puede llamarse varias veces (p. ej. en tests) sin duplicar
    handlers, gracias a `force=True`.
    """
    config = get_config()
    level = logging.getLevelNamesMapping().get(config.log_level, logging.INFO)
    logging.basicConfig(level=level, format=_LOG_FORMAT, datefmt=_DATE_FORMAT, force=True)
    logging.getLogger(_APP_LOGGER_NAME).setLevel(level)
