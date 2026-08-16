FROM python:3.13-slim

# uv se instala copiando el binario oficial desde su imagen distroless
# (evita pip install de uv dentro de la imagen final).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Se copian primero los manifiestos para aprovechar la cache de capas de Docker.
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini ./alembic.ini
COPY main.py ./main.py
COPY entrypoint.sh ./entrypoint.sh
# README.md se copia porque `pyproject.toml` lo declara como `readme` y
# hatchling valida su existencia al instalar el proyecto (`uv sync` sin
# `--no-install-project`); sin este archivo el build falla en el segundo
# `uv sync` de esta imagen.
COPY README.md ./README.md

RUN uv sync --frozen --no-dev \
    && chmod +x ./entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
