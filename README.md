# Customers

A Flask API to manage customers and their addresses. It uses a hexagonal
architecture (domain / application / infrastructure), SQLAlchemy 2.0, and
Pydantic.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- Docker and Docker Compose

## Configuration

Environment variables in `.env` (not versioned):

```
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=
```

## Running the project

```
docker compose up --build
```

This starts, in order: `postgres` (with a healthcheck), `migrate` (applies
pending database migrations and then stops), and `app` (starts only if
`migrate` finished successfully).

## Database migrations

The database schema is versioned with [Flask-Migrate](https://flask-migrate.readthedocs.io/)
(Alembic) in `migrations/`. **There is no `db.create_all()`**: tables are
only created or updated through migrations.

### Applying migrations

When you run `docker compose up`, the `migrate` service runs `flask db
upgrade` automatically before `app` starts. No manual step is needed.

### Creating a new migration

When you add or change a model in `src/infrastructure/persistence/`:

1. Start only the database: `docker compose up -d postgres`.
2. Generate the migration against that database, from your host machine:
   ```
   FLASK_APP=main:app POSTGRES_HOST=localhost uv run flask db migrate -m "descriptive message"
   ```
3. **Check the generated file by hand** in `migrations/versions/` — Alembic's
   autogenerate does not always detect constraints correctly (`ondelete`,
   indexes, types), so make sure the DDL matches the SQLAlchemy model
   exactly.
4. Apply it locally to test it: `FLASK_APP=main:app POSTGRES_HOST=localhost uv run flask db upgrade`.
5. Commit the migration file together with the model change.

### Adding a new entity

When you add a new entity (domain, DTOs, repository port, service,
persistence model, and routes, following the same pattern already used by
`Customer` and `Address`), the last step is to create and check its
migration as explained above, before marking the feature as done.

## Tests

The test suite lives in `tests/`, and it mirrors `src/` (`tests/domain/`,
`tests/application/dto/`, `tests/application/services/`,
`tests/infrastructure/persistence/`, `tests/infrastructure/web/`).

### Fast tests, no database needed

The tests in `tests/domain/` and `tests/application/` (DTOs and services,
the last one using `pytest-mock`) do not touch the database:

```
uv run pytest tests/domain tests/application
```

### Full suite, with a real Postgres database

The tests in `tests/infrastructure/` (persistence and web routes) use the
same Postgres database from `docker-compose.yaml`, not SQLite or
testcontainers, so they behave like Postgres in real use (`Uuid` type,
`ON DELETE CASCADE`). Before running them:

1. Start only the database: `docker compose up -d postgres`.
2. Apply migrations if needed:
   `FLASK_APP=main:app POSTGRES_HOST=localhost uv run flask db upgrade`.
3. Run the full suite (the session fixture in `tests/conftest.py` sets
   `POSTGRES_HOST=localhost` by default, since the tests run on your host
   machine, outside the `docker-compose` network):
   ```
   uv run pytest
   ```

Every test that uses the database creates its own `customer` and deletes it
at the end (cascade delete takes care of its `addresses`), so the suite does
not leave extra rows behind and does not depend on test order.
