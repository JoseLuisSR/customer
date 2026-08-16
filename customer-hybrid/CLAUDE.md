# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Dependency management is via `uv` (see `pyproject.toml`).

```bash
uv sync                          # install dependencies

# Run the app
docker compose up --build        # postgres -> migrate -> app (full stack)
uv run python main.py            # local dev server (needs Postgres reachable per .env)

# Lint / format / type-check
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/

# Tests
uv run pytest tests/domain tests/application   # fast subset, no DB
uv run pytest                                  # full suite, needs real Postgres (see below)
uv run pytest tests/domain/test_address.py::TestAddressCreate::test_generates_a_uuid_id  # single test

# Database migrations (Flask-Migrate / Alembic, see migrations/)
docker compose up -d postgres
FLASK_APP=main:app POSTGRES_HOST=localhost uv run flask db migrate -m "message"
FLASK_APP=main:app POSTGRES_HOST=localhost uv run flask db upgrade
```

Before running anything against a real Postgres (full test suite, `flask db
migrate`/`upgrade` from the host), start it with `docker compose up -d
postgres` and export `POSTGRES_HOST=localhost` — the value in `.env`
(`postgres`) is the Docker Compose network hostname and only resolves
inside the compose network.

There is **no `db.create_all()`** anywhere in the app. Tables only exist
through migrations in `migrations/versions/`. Autogenerate (`flask db
migrate`) does not always get constraints right (`ondelete`, indexes) —
always check the generated script against the SQLAlchemy model before
committing it.

## Architecture

Hexagonal architecture (ports & adapters), with two parallel features —
`Customer` and `Address` (nested under a customer, max 5 per customer,
`ON DELETE CASCADE`) — that follow the exact same layering. When adding a
new entity, replicate this structure end to end rather than improvising a
new one:

```
src/domain/<entity>.py                                  # pure entity, no framework imports
src/exception/<entity>_exception.py                      # domain exceptions
src/application/dto/<entity>_dto.py                      # Pydantic request/response models
src/application/repository/<entity>_repository.py        # ABC port, works with the domain entity
src/application/services/<entity>_service.py             # use cases, injected with the port
src/infrastructure/persistence/<entity>_model.py          # SQLAlchemy Mapped model
src/infrastructure/persistence/database_<entity>_repository.py  # port implementation
src/infrastructure/web/<entity>_routes.py                 # Flask Blueprint
```

Key conventions, consistent across `Customer` and `Address`:

- **Domain entities** use name-mangled private attributes, a `create()`
  classmethod (generates a new `uuid4`) and a `restore()` classmethod
  (reconstructs from persistence with a given id). `id` (and `customer_id`
  on `Address`) is read-only — no setter. Other fields expose a
  `@property` + setter pair.
- **Services always return DTOs**, never domain entities, and receive
  their repository port through the constructor. There is no DI
  container: each `*_routes.py` module instantiates its concrete
  `Database*Repository` and `*Service` once at import time (module-level
  singletons).
- **Routes are thin**: parse UUIDs (`src/infrastructure/web/uuid_parser.py`,
  shared by both blueprints), validate the body with a Pydantic DTO,
  delegate to the service, serialize the response. No `try/except` in
  route handlers — domain exceptions propagate and are translated to HTTP
  responses centrally in `src/infrastructure/web/error_handler.py`
  (`register_exception_handlers`, one handler function + one
  `app.register_error_handler` call per exception type).
- **Repositories** catch `SQLAlchemyError`/`IntegrityError`, roll back,
  log via `logger.error(..., extra={"operation": ..., "sql_alchemy_error":
  ...})`, and re-raise as a domain exception (`PersistenceUnavailableError`
  for generic failures, or a specific one like `CustomerNotFoundError`/
  `AddressNotFoundError` for FK violations / missing rows).
- **`Address` DTOs use Pydantic aliasing**: the JSON contract uses
  `postal-code` (hyphen) while the domain/DB use `postal_code`. DTOs set
  `Field(alias="postal-code")` + `ConfigDict(populate_by_name=True)`, and
  routes must serialize with `.model_dump(by_alias=True)`. `Customer`
  DTOs have no aliasing and use plain `.model_dump()`.
- Address is the only entity with a `PATCH` endpoint (partial update) and
  upsert semantics on `PUT` (creates with `201` if the id doesn't exist,
  replaces with `200` if it does); `Customer`'s `PUT` is a strict
  replace-or-404.

### Known pre-existing inconsistencies (don't "fix" silently while working on unrelated code)

- `database_customer_repository.py` has a debug `print()` in
  `_handle_error` and raises a bare `SQLAlchemyError` in `get_all`
  instead of `PersistenceUnavailableError` like every other method. The
  `Address` repository does not replicate either of these.
- `error_handler.py` maps `CustomerNotFoundError` to the JSON error code
  `USER_NOT_FOUND` (not `CUSTOMER_NOT_FOUND`).
- `customer_bp = Blueprint("cusromer", ...)` — the blueprint's internal
  name is misspelled; it doesn't affect the URL prefix or routes.
- `mypy src/` reports a pre-existing `Name "db.Model" is not defined` on
  both `customer_model.py` and `address_model.py` (Flask-SQLAlchemy's
  dynamic base class isn't resolvable by mypy without extra config).

## Tests

`tests/` mirrors `src/`. Domain, DTO, and service tests (service tests
mock the repository port with `pytest-mock`) need no database. Persistence
and web-route tests run against the **real Postgres** from
`docker-compose.yaml` (not SQLite, not testcontainers) so that
Postgres-specific behavior (`Uuid` type, `ON DELETE CASCADE`) is actually
exercised — routes and repositories are instantiated as module-level
singletons with no DI seam to swap in a fake. `tests/conftest.py` builds
the app once per session, runs `flask_migrate.upgrade()`, and exposes a
`customer_id` fixture that creates/deletes a real customer per test
(cascade delete cleans up any addresses).
