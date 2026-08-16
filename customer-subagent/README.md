# Customers

Customer API (Flask + SQLAlchemy + PostgreSQL). See [specs/customer-contracts.md](specs/customer-contracts.md)
for the contracts and [specs/implementation-plan.md](specs/implementation-plan.md) for the implementation plan.

## Start with Docker (recommended)

You need Docker.

```bash
cp .env.example .env   # change credentials if needed
docker compose up -d
```

This starts `db` (PostgreSQL), `db_test` (PostgreSQL for integration
tests), runs the Alembic migrations (the `migrate` service, one-off), and
then starts `api`.

The API is available at `http://localhost:8000` (the container listens on
port 5000 inside; on macOS, port 5000 on the host is often used by the
system's AirPlay receiver, so the API is published on 8000 instead).

```bash
curl http://localhost:8000/customers/all
```

To apply migrations by hand at any time:

```bash
docker compose run --rm migrate
```

## Local start (without Docker)

You need [uv](https://docs.astral.sh/uv/) and a reachable PostgreSQL
instance.

```bash
uv sync
export DATABASE_URL=postgresql+psycopg://customers:change-me@localhost:5432/customers
uv run alembic upgrade head
uv run flask --app customers.infrastructure.web.app:create_app run
```

## API usage examples

The examples use `http://localhost:8000` (Docker start). For a local start
without Docker, change the port to `5000`. The `id` values shown (`1`,
`2`...) are just examples: in PostgreSQL, a `BIGSERIAL` sequence **does
not go back** to a used value even if the `INSERT` fails (for example,
because of the duplicate email in the example below), so the real `id`
your database returns may be different — always use the `id` from the
previous response, not a fixed number.

### `POST /customers` — Create a customer

**Success**

```bash
curl -i -X POST http://localhost:8000/customers \
  -H 'Content-Type: application/json' \
  -d '{"name": "Ada Lovelace", "age": 30, "email": "ada@example.com"}'
```

```
HTTP/1.1 201 CREATED
{"id": 1, "name": "Ada Lovelace", "age": 30, "email": "ada@example.com"}
```

**Error — missing or invalid field (`400`)**

```bash
curl -i -X POST http://localhost:8000/customers \
  -H 'Content-Type: application/json' \
  -d '{"name": "Ada Lovelace", "age": 30}'
```

```
HTTP/1.1 400 BAD REQUEST
{"error": "validation failed", "details": {"email": "is required"}}
```

Other cases that also respond with `400` in the same way: `age` outside
`0..120`, `email` with an invalid format, empty `name`, or a missing/broken
JSON body (`{"details": {"body": "invalid or missing JSON body"}}`).

**Error — duplicate email (`409`)**

```bash
curl -i -X POST http://localhost:8000/customers \
  -H 'Content-Type: application/json' \
  -d '{"name": "Ada 2", "age": 31, "email": "ada@example.com"}'
```

```
HTTP/1.1 409 CONFLICT
{"error": "email already exists"}
```

### `GET /customers/all` — List all customers

```bash
curl -i http://localhost:8000/customers/all
```

```
HTTP/1.1 200 OK
[{"id": 1, "name": "Ada Lovelace", "age": 30, "email": "ada@example.com"}]
```

This endpoint has no error cases of its own (it always returns `200`,
with an empty list `[]` if there are no active customers); soft-deleted
customers do not show up.

### `GET /customers/:id` — Get a customer

**Success**

```bash
curl -i http://localhost:8000/customers/1
```

```
HTTP/1.1 200 OK
{"id": 1, "name": "Ada Lovelace", "age": 30, "email": "ada@example.com"}
```

**Error — not found or deleted (`404`)**

```bash
curl -i http://localhost:8000/customers/999
```

```
HTTP/1.1 404 NOT FOUND
{"error": "customer not found"}
```

### `PATCH /customers/:id` — Update a customer

Accepts any subset of `name`, `age`, `email` (partial update).

**Success**

```bash
curl -i -X PATCH http://localhost:8000/customers/1 \
  -H 'Content-Type: application/json' \
  -d '{"age": 31}'
```

```
HTTP/1.1 200 OK
{"id": 1, "name": "Ada Lovelace", "age": 31, "email": "ada@example.com"}
```

**Error — no fields to update (`400`)**

```bash
curl -i -X PATCH http://localhost:8000/customers/1 \
  -H 'Content-Type: application/json' \
  -d '{}'
```

```
HTTP/1.1 400 BAD REQUEST
{"error": "validation failed", "details": {"body": "no fields to update"}}
```

**Error — body `id` does not match the URL `id` (`400`)**

```bash
curl -i -X PATCH http://localhost:8000/customers/1 \
  -H 'Content-Type: application/json' \
  -d '{"id": 2, "age": 31}'
```

```
HTTP/1.1 400 BAD REQUEST
{"error": "validation failed", "details": {"id": "does not match the id in the URL"}}
```

**Error — invalid field, for example `age` out of range (`400`)**

```bash
curl -i -X PATCH http://localhost:8000/customers/1 \
  -H 'Content-Type: application/json' \
  -d '{"age": -1}'
```

```
HTTP/1.1 400 BAD REQUEST
{"error": "validation failed", "details": {"age": "must be between 0 and 120"}}
```

**Error — not found or deleted (`404`)**

```bash
curl -i -X PATCH http://localhost:8000/customers/999 \
  -H 'Content-Type: application/json' \
  -d '{"age": 31}'
```

```
HTTP/1.1 404 NOT FOUND
{"error": "customer not found"}
```

**Error — email already used by another customer (`409`)**

First create a second customer (the `id` it returns may not be `2`, see
the note at the start of this section):

```bash
curl -s -X POST http://localhost:8000/customers \
  -H 'Content-Type: application/json' \
  -d '{"name": "Grace Hopper", "age": 40, "email": "grace@example.com"}'
```

Then try to update it (replace `2` with the `id` from the previous step)
using the email already used by customer `1`:

```bash
curl -i -X PATCH http://localhost:8000/customers/2 \
  -H 'Content-Type: application/json' \
  -d '{"email": "ada@example.com"}'
```

```
HTTP/1.1 409 CONFLICT
{"error": "email already exists"}
```

### `DELETE /customers/:id` — Delete a customer (soft delete)

**Success**

```bash
curl -i -X DELETE http://localhost:8000/customers/1
```

```
HTTP/1.1 200 OK
{}
```

**Error — not found or already deleted (`404`)**

```bash
curl -i -X DELETE http://localhost:8000/customers/999
```

```
HTTP/1.1 404 NOT FOUND
{"error": "customer not found"}
```

### A customer's addresses (`Address`)

Each customer has a list of addresses nested under
`/customers/:id/addresses`. The JSON contract uses `postalcode` and
`address` exactly as written (this is how they appear in
`specs/addresses-contracts.md`), even though internally they are called
`postal_code` and `address_line`. Just like with customer `id`s, address
`id`s in the examples are just illustrative — use the one your own
database returns.

#### Quick endpoint reference

| Endpoint | Method | Path | Payload (request body) | Success |
|---|---|---|---|---|
| Create address | `POST` | `/customers/:id/addresses` | `{"country", "state", "city", "postalcode", "address"}` (all 5 required; `id` is ignored if sent) | `201` |
| List addresses | `GET` | `/customers/:id/addresses` | — | `200` |
| Get address | `GET` | `/customers/:id/addresses/:id` | — | `200` |
| Update address | `PATCH` | `/customers/:id/addresses/:id` | subset of `{"country", "state", "city", "postalcode", "address"}` (at least one) | `200` |
| Delete address | `DELETE` | `/customers/:id/addresses/:id` | — | `200` |

In all 5 endpoints, a customer `:id` that does not exist or is
soft-deleted responds with `404 {"error": "customer not found"}`; in the 4
endpoints that also take an address `:id`, an address that does not
exist, is soft-deleted, or **belongs to another customer** responds with
`404 {"error": "address not found"}` (data is never leaked between
customers). Full details with `curl` examples and error responses below.

#### `POST /customers/:id/addresses` — Create an address

**Success**

```bash
curl -i -X POST http://localhost:8000/customers/1/addresses \
  -H 'Content-Type: application/json' \
  -d '{"country": "Colombia", "state": "Meta", "city": "Villavicencio", "postalcode": "50001", "address": "Calle 10 #5-20"}'
```

```
HTTP/1.1 201 CREATED
{"id": 1, "country": "Colombia", "state": "Meta", "city": "Villavicencio", "postalcode": "50001", "address": "Calle 10 #5-20"}
```

**Error — missing or invalid field (`400`)**

```bash
curl -i -X POST http://localhost:8000/customers/1/addresses \
  -H 'Content-Type: application/json' \
  -d '{"country": "Colombia", "state": "Meta", "city": "Villavicencio", "address": "Calle 10 #5-20"}'
```

```
HTTP/1.1 400 BAD REQUEST
{"error": "validation failed", "details": {"postalcode": "is required"}}
```

**Error — parent customer not found or deleted (`404`)**

```bash
curl -i -X POST http://localhost:8000/customers/999/addresses \
  -H 'Content-Type: application/json' \
  -d '{"country": "Colombia", "state": "Meta", "city": "Villavicencio", "postalcode": "50001", "address": "Calle 10 #5-20"}'
```

```
HTTP/1.1 404 NOT FOUND
{"error": "customer not found"}
```

#### `GET /customers/:id/addresses` — List a customer's addresses

```bash
curl -i http://localhost:8000/customers/1/addresses
```

```
HTTP/1.1 200 OK
[{"id": 1, "country": "Colombia", "state": "Meta", "city": "Villavicencio", "postalcode": "50001", "address": "Calle 10 #5-20"}]
```

Just like `POST`, a customer `:id` that does not exist or is deleted
responds with `404 {"error": "customer not found"}`.

#### `GET /customers/:id/addresses/:id` — Get an address

**Success**

```bash
curl -i http://localhost:8000/customers/1/addresses/1
```

```
HTTP/1.1 200 OK
{"id": 1, "country": "Colombia", "state": "Meta", "city": "Villavicencio", "postalcode": "50001", "address": "Calle 10 #5-20"}
```

**Error — not found, deleted, or belongs to another customer (`404`)**

```bash
curl -i http://localhost:8000/customers/1/addresses/999
```

```
HTTP/1.1 404 NOT FOUND
{"error": "address not found"}
```

Security note: if the address `:id` exists but belongs to **another**
customer, the response is the same `404 {"error": "address not found"}`
— data from one customer is never leaked through another customer's
`:id`.

#### `PATCH /customers/:id/addresses/:id` — Update an address

Accepts any subset of `country`, `state`, `city`, `postalcode`, `address`
(partial update).

**Success**

```bash
curl -i -X PATCH http://localhost:8000/customers/1/addresses/1 \
  -H 'Content-Type: application/json' \
  -d '{"city": "Bogota"}'
```

```
HTTP/1.1 200 OK
{"id": 1, "country": "Colombia", "state": "Meta", "city": "Bogota", "postalcode": "50001", "address": "Calle 10 #5-20"}
```

**Error — no fields to update (`400`)**

```bash
curl -i -X PATCH http://localhost:8000/customers/1/addresses/1 \
  -H 'Content-Type: application/json' \
  -d '{}'
```

```
HTTP/1.1 400 BAD REQUEST
{"error": "validation failed", "details": {"body": "no fields to update"}}
```

**Error — body `id` does not match the URL `id` (`400`)**

```bash
curl -i -X PATCH http://localhost:8000/customers/1/addresses/1 \
  -H 'Content-Type: application/json' \
  -d '{"id": 2, "city": "Bogota"}'
```

```
HTTP/1.1 400 BAD REQUEST
{"error": "validation failed", "details": {"id": "does not match the id in the URL"}}
```

**Error — address not found, deleted, or belongs to another customer (`404`)**

```bash
curl -i -X PATCH http://localhost:8000/customers/1/addresses/999 \
  -H 'Content-Type: application/json' \
  -d '{"city": "Bogota"}'
```

```
HTTP/1.1 404 NOT FOUND
{"error": "address not found"}
```

#### `DELETE /customers/:id/addresses/:id` — Delete an address (soft delete)

**Success**

```bash
curl -i -X DELETE http://localhost:8000/customers/1/addresses/1
```

```
HTTP/1.1 200 OK
{}
```

**Error — not found, already deleted, or belongs to another customer (`404`)**

```bash
curl -i -X DELETE http://localhost:8000/customers/1/addresses/999
```

```
HTTP/1.1 404 NOT FOUND
{"error": "address not found"}
```

## Inspecting the database

To open an interactive `psql` shell inside the `db` container:

```bash
docker compose exec db psql -U customers -d customers
```

Some useful commands inside `psql`:

```sql
\dt                     -- list tables
\d customers            -- show columns, constraints, and indexes of "customers"
\d addresses            -- show columns, constraints, and indexes of "addresses"
SELECT * FROM customers ORDER BY id;
SELECT * FROM addresses ORDER BY id;
\q                      -- exit
```

You can also run a single query without opening the interactive shell:

```bash
docker compose exec db psql -U customers -d customers \
  -c "SELECT id, name, age, email, created_at, updated_at, deleted_at FROM customers ORDER BY id;"

docker compose exec db psql -U customers -d customers \
  -c "SELECT id, customer_id, country, state, city, postal_code, address_line, deleted_at FROM addresses ORDER BY id;"
```

To also see soft-deleted rows (which the API excludes), these same
queries already show them — `deleted_at` will have a date instead of
`NULL`.

The same applies to `db_test` (the database used by the integration
tests), just change the service name and database name:

```bash
docker compose exec db_test psql -U customers -d customers_test
```

## Tests

```bash
uv run pytest tests/unit                  # unit tests, no external dependencies
uv run pytest                             # full suite (unit + integration)
uv run pytest --cov=src/customers --cov-report=term-missing --cov-fail-under=85
uv run ruff check .
uv run ruff format --check .
```

The integration tests (`tests/integration/`) hit a real PostgreSQL
database (not SQLite, not mocks), so they need `db_test` to be running:

```bash
docker compose up -d db_test
```

By default they point to
`postgresql+psycopg://customers:change-me@localhost:5433/customers_test`
(the published port of `db_test`). To use different credentials, export
`TEST_DATABASE_URL` before running `pytest`.
