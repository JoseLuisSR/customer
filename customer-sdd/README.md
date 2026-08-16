# customers

REST API for managing customers and addresses (`API-CUSTOMERS-001`).
It uses a hexagonal architecture (domain / application / infrastructure)
based on Flask, SQLAlchemy, and PostgreSQL. See the functional specification
in `specs/customers/spec.md`, the technical specification in
`specs/customers/plan.md`, and the implementation plan in
`specs/customers/implementation-plan.md`.

## Requirements

- Python 3.13.5 (see `.python-version`)
- [`uv`](https://docs.astral.sh/uv/) for dependency management
- Docker and Docker Compose to run the full stack (PostgreSQL + API)

## Installation

```bash
uv sync
```

This installs the runtime dependencies and the development tools (`pytest`,
`ruff`, `mypy`) declared in `pyproject.toml`.

## Environment variables

Copy `.env.example` as a reference for the minimum variables
(`DATABASE_URL`, `FLASK_ENV`, `LOG_LEVEL`). They are read directly from
`os.environ` (without `python-dotenv`); export them in your shell or define
them in `docker-compose.yml`.

## Start the stack with Docker Compose

```bash
docker-compose up --build
```

This starts `db` (development PostgreSQL), `db_test` (PostgreSQL only for
integration tests, port `5433`), and `api` (Flask via `gunicorn`, port
`8000`). The image `entrypoint.sh` runs Alembic migrations (`alembic upgrade
head`) before starting the server.

## Test the web services

With the stack running (`docker-compose up --build`, service `api` at
`http://localhost:8000`) or the app running locally (`python main.py`, port
`8000`, using your own `DATABASE_URL`), all endpoints are under the prefix:

```
http://localhost:8000/api/v1
```

All responses — success or error — use the same result envelope
(`specs/customers/plan.md` §2.1):

```json
{
  "success": true,
  "operation": "create | read | list | update | delete",
  "entity": "customer | address",
  "entity_status": "ACTIVE | DELETED | null",
  "message": "string",
  "data": { },
  "errors": null
}
```

### Endpoints — Customer

| Method | URL | Purpose | Success code |
|---|---|---|---|
| `POST` | `/api/v1/customers` | Create a customer (with optional embedded addresses) | 201 |
| `GET` | `/api/v1/customers/{customer_id}` | Get a customer and their addresses | 200 |
| `GET` | `/api/v1/customers?page=1&page_size=20` | List customers (paginated) | 200 |
| `PUT` | `/api/v1/customers/{customer_id}` | Update a customer (full replacement) | 200 |
| `DELETE` | `/api/v1/customers/{customer_id}` | Delete a customer (soft delete, includes their addresses) | 200 |

**Create customer**

```bash
curl -X POST http://localhost:8000/api/v1/customers \
  -H "Content-Type: application/json" \
  -d '{
        "name": "Ada Lovelace",
        "identification": "CC-123456",
        "age": 30,
        "email": "ada@example.com",
        "addresses": [
          {
            "country": "Colombia",
            "state": "Antioquia",
            "city": "Medellín",
            "address": "Calle 10 # 20-30",
            "postal_code": "050001"
          }
        ]
      }'
```

Response `201 Created`:

```json
{
  "success": true,
  "operation": "create",
  "entity": "customer",
  "entity_status": "ACTIVE",
  "message": "Customer created successfully.",
  "data": {
    "id": "b3f1e2a0-...-uuid",
    "name": "Ada Lovelace",
    "identification": "CC-123456",
    "age": 30,
    "email": "ada@example.com",
    "status": "ACTIVE",
    "created_at": "2026-07-27T12:00:00+00:00",
    "updated_at": "2026-07-27T12:00:00+00:00",
    "addresses": [
      { "id": "a9c2...-uuid", "country": "Colombia", "state": "Antioquia", "city": "Medellín", "address": "Calle 10 # 20-30", "postal_code": "050001", "status": "ACTIVE" }
    ]
  },
  "errors": null
}
```

`addresses` is optional (0 to 5 elements). If the payload has more than five,
the operation is rejected completely — neither the customer nor any address is
created — with `409 Conflict` (`ERR-005`).

**Get customer**

```bash
curl http://localhost:8000/api/v1/customers/b3f1e2a0-...-uuid
```

`200 OK` with the customer and their active embedded addresses; `404 Not
Found` (`ERR-003`) if it does not exist or was already deleted.

**List customers**

```bash
curl "http://localhost:8000/api/v1/customers?page=1&page_size=20"
```

`200 OK`, `data`:

```json
{ "items": [ { "id": "...", "name": "...", "...": "..." } ], "page": 1, "page_size": 20, "total": 1 }
```

`page_size` defaults to 20 and has a maximum of 100. The listed customers do
not include embedded `addresses` (use `GET /customers/{id}` for full details).

**Update customer** (full replacement — all four fields are required;
`addresses` is not sent here, and it is managed by the `Address` endpoints)

```bash
curl -X PUT http://localhost:8000/api/v1/customers/b3f1e2a0-...-uuid \
  -H "Content-Type: application/json" \
  -d '{
        "name": "Ada Lovelace",
        "identification": "CC-123456",
        "age": 31,
        "email": "ada.lovelace@example.com"
      }'
```

`200 OK` on success; `409 Conflict` with `ERR-002` (email already used by
another customer) or `ERR-008` (identification already used by another
customer; see the note about `ERR-008` below).

**Delete customer**

```bash
curl -X DELETE http://localhost:8000/api/v1/customers/b3f1e2a0-...-uuid
```

`200 OK` with `entity_status: "DELETED"` (never `204`: the result envelope is
required in every response). It also marks all customer addresses as
`DELETED`, without leaving orphan records.

### Endpoints — Address

| Method | URL | Purpose | Success code |
|---|---|---|---|
| `POST` | `/api/v1/customers/{customer_id}/addresses` | Create an address | 201 |
| `GET` | `/api/v1/customers/{customer_id}/addresses` | List customer addresses | 200 |
| `PUT` | `/api/v1/customers/{customer_id}/addresses/{address_id}` | Update an address | 200 |
| `DELETE` | `/api/v1/customers/{customer_id}/addresses/{address_id}` | Delete an address | 200 |

**Create address**

```bash
curl -X POST http://localhost:8000/api/v1/customers/b3f1e2a0-...-uuid/addresses \
  -H "Content-Type: application/json" \
  -d '{
        "country": "Colombia",
        "state": "Cundinamarca",
        "city": "Bogotá",
        "address": "Cra 7 # 45-10",
        "postal_code": "110111"
      }'
```

`201 Created` on success. `404 Not Found` (`ERR-003`) if the customer does
not exist; `409 Conflict` (`ERR-005`) if the customer already has five active
addresses.

**List addresses**

```bash
curl http://localhost:8000/api/v1/customers/b3f1e2a0-...-uuid/addresses
```

**Update address**

```bash
curl -X PUT http://localhost:8000/api/v1/customers/b3f1e2a0-...-uuid/addresses/a9c2...-uuid \
  -H "Content-Type: application/json" \
  -d '{
        "country": "Colombia",
        "state": "Cundinamarca",
        "city": "Bogotá",
        "address": "Cra 7 # 45-10, Apto 501",
        "postal_code": "110111"
      }'
```

`404 Not Found` (`ERR-006`) if the address does not belong to the
`customer_id` in the URL.

**Delete address**

```bash
curl -X DELETE http://localhost:8000/api/v1/customers/b3f1e2a0-...-uuid/addresses/a9c2...-uuid
```

### Common errors

| Code | Situation | HTTP |
|---|---|---|
| `VAL-001`/`VAL-003`/`VAL-004`/`VAL-005`/`VAL-009` | Required field missing, wrong type, or invalid value | 400 |
| `ERR-001` | Request body is not valid JSON | 400 |
| `ERR-002` | Email already registered by another customer | 409 |
| `ERR-003` | Customer does not exist (or was already deleted) | 404 |
| `ERR-004` | Address does not exist (or was already deleted) | 404 |
| `ERR-005` | The customer already has five active addresses | 409 |
| `ERR-006` | The address does not belong to the indicated customer | 404 |
| `ERR-007` | Unhandled internal error | 500 |
| `ERR-008`* | Identification already registered by another customer | 409 |
| — | Route or HTTP method does not exist | 404 / 405 |

\* `ERR-008` (and its validation `VAL-011`) are provisional technical codes
for `identification` uniqueness: `specs/customers/spec.md` does not yet include
them as part of the functional contract (see `specs/customers/plan.md` §2.4 and
§7.1).

Example of an error with several invalid fields at the same time (all are
reported, not only the first one):

```json
{
  "success": false,
  "operation": "create",
  "entity": "customer",
  "entity_status": null,
  "message": "The request body or parameters are invalid.",
  "data": null,
  "errors": [
    { "code": "VAL-003", "field": "name", "message": "The field 'name' is required." },
    { "code": "VAL-005", "field": "age", "message": "The field 'age' must be an integer." }
  ]
}
```

## Tests

```bash
# Unit tests (without external infrastructure)
uv run pytest tests/unit

# Integration tests (requires db_test running)
docker-compose up -d db_test
uv run pytest tests/integration
```

## Linters and typing

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

## Migrations (Alembic)

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description_in_snake_case"
```

`DATABASE_URL` must be defined in the environment; `alembic.ini` does not
contain a hardcoded URL (it is injected dynamically from `migrations/env.py`).
