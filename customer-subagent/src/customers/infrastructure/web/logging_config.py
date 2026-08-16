from __future__ import annotations

import logging

from customers.infrastructure.config.settings import Settings


def configure_logging(settings: Settings) -> None:
    level = logging.DEBUG if settings.flask_env == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
