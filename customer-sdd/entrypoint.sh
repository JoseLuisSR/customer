#!/bin/sh
set -e

# Aplica las migraciones pendientes antes de levantar la aplicación.
# `migrations/env.py` (Fase 3) lee DATABASE_URL desde el entorno.
uv run alembic upgrade head

# Referencia hacia adelante intencional: `main:app` (objeto `app = create_app()`)
# se implementa en la Fase 4. Hasta entonces este entrypoint no puede
# levantar el servidor con éxito, pero su forma final queda fijada aquí.
exec uv run gunicorn --bind 0.0.0.0:8000 main:app
