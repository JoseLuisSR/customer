"""Configuración de la aplicación leída desde variables de entorno.

No se usa `python-dotenv` (decisión de `specs/customers/plan.md` §5.2 /
`specs/customers/implementation-plan.md` §2.1): las variables de entorno
deben ser inyectadas por el shell, `docker-compose` o el orquestador de
despliegue que corresponda. Ver `.env.example` para el formato esperado de
cada variable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

_DEFAULT_FLASK_ENV = "production"
_DEFAULT_LOG_LEVEL = "INFO"

_VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


class MissingConfigurationError(RuntimeError):
    """Falta una variable de entorno obligatoria para arrancar la aplicación."""


@dataclass(frozen=True, slots=True)
class Config:
    """Configuración mínima de la aplicación (`plan.md` §5.2)."""

    database_url: str
    flask_env: str
    log_level: str

    @property
    def is_testing(self) -> bool:
        """`True` cuando `FLASK_ENV=testing` (usado por los tests de integración)."""
        return self.flask_env == "testing"


def _load_config() -> Config:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise MissingConfigurationError(
            "La variable de entorno DATABASE_URL es obligatoria y no fue definida. "
            "Ver .env.example para el formato esperado."
        )

    log_level = os.environ.get("LOG_LEVEL", _DEFAULT_LOG_LEVEL).upper()
    if log_level not in _VALID_LOG_LEVELS:
        raise MissingConfigurationError(
            f"LOG_LEVEL='{log_level}' no es válido. Valores permitidos: "
            f"{', '.join(sorted(_VALID_LOG_LEVELS))}."
        )

    return Config(
        database_url=database_url,
        flask_env=os.environ.get("FLASK_ENV", _DEFAULT_FLASK_ENV),
        log_level=log_level,
    )


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Devuelve la configuración de la aplicación, memoizada por proceso.

    En tests que necesiten variar variables de entorno entre casos, llamar
    a `get_config.cache_clear()` tras modificar `os.environ`.
    """
    return _load_config()
