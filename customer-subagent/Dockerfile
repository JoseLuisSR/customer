# syntax=docker/dockerfile:1

FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.8.12 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Instala las dependencias primero (capa cacheable independiente del código).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copia el resto del proyecto e instala el propio paquete "customers".
COPY . .
RUN uv sync --frozen --no-dev


FROM python:3.13-slim AS runtime

RUN groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /app app

WORKDIR /app

COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER app

EXPOSE 5000

CMD ["flask", "--app", "customers.infrastructure.web.app:create_app", "run", "--host=0.0.0.0", "--port=5000"]
