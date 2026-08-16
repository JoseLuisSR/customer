# Plan de implementación — API de Customers

Basado en `specs/customer-contracts.md`. Estado actual del repositorio: proyecto
recién inicializado con `uv` (`pyproject.toml` sin dependencias, `main.py` de
ejemplo, sin carpetas `src/` ni `tests/`, sin Dockerfile). Es un proyecto
greenfield, por lo que se define arquitectura hexagonal desde cero, sin
necesidad de migrar código legado.

## 0. Supuestos y decisiones (confirmados por el usuario el 2026-07-22)

El spec dejaba varias reglas de negocio y detalles técnicos sin definir. Los
puntos 6, 7 y 9/11 fueron confirmados explícitamente por el usuario; el resto
son supuestos razonables que se mantienen salvo objeción:

| # | Tema | Decisión | Estado |
|---|------|---------------------|--------------------------------|
| 1 | Campos en las respuestas | Los endpoints devuelven solo `id, name, age, email` (tal como muestran los ejemplos de request/response), aunque la entidad interna sí guarda `created_at, updated_at, deleted_at`. | Supuesto, sin objeción |
| 2 | Borrado | `DELETE` hace **soft delete** (`deleted_at = now()`), no borra la fila. `GET /customers/all` y `GET /customers/:id` excluyen registros con `deleted_at != NULL` (los tratan como 404/ausentes). | Supuesto, sin objeción |
| 3 | Validaciones de `name` | String no vacío (tras `strip()`), longitud 1–255. | Supuesto, sin objeción |
| 4 | Validaciones de `age` | Entero, rango 0–120. | Supuesto, sin objeción |
| 5 | Validaciones de `email` | String requerido, formato válido de email (regex simple `local@dominio.tld`), longitud máx. 255. | Supuesto, sin objeción |
| 6 | Unicidad de `email` | **CONFIRMADO: email único por cliente.** Constraint `UNIQUE` en BD; `POST`/`PATCH` con email duplicado → `409 Conflict`. | ✅ Confirmado |
| 7 | `PATCH` — actualización parcial | Se permiten campos parciales (no hace falta enviar los 4 campos); si no se envía ningún campo válido, `400`. **CONFIRMADO:** si el body trae `id` y no coincide con el `:id` de la URL, se responde `400`. | ✅ Confirmado |
| 8 | Body de respuesta de `DELETE` | `200` con body `{}` (vacío). El spec solo define el status code. | Supuesto, sin objeción |
| 9 | Migraciones | **CONFIRMADO: se usa Alembic** para versionar el esquema, aunque no está listado explícitamente en el stack del spec (solo SQLAlchemy). | ✅ Confirmado |
| 10 | Validación de entrada en la capa web | Validación manual con clases Python simples (sin `marshmallow`/`pydantic`), para no introducir dependencias no solicitadas. | Supuesto, sin objeción |
| 11 | Lint/seguridad | **CONFIRMADO: se usa Ruff** (lint + format + reglas tipo `flake8-bandit`) como herramienta de calidad, aunque no está en el stack del spec. | ✅ Confirmado |
| 12 | Cobertura de pruebas | Umbral propuesto: ≥ 85% global (dominio y aplicación ≥ 90%, por ser lógica de negocio pura). | Supuesto, sin objeción |
| 13 | Servidor WSGI en Docker | Se usa el servidor de desarrollo de Flask (`flask run`) dentro del contenedor para no añadir `gunicorn` (no listado en el stack). Se deja anotado como mejora futura para producción real. | Supuesto, sin objeción |

Con estos puntos confirmados, el plan queda listo para iniciar la Fase 1 de
implementación.

## 1. Arquitectura

Arquitectura hexagonal (puertos y adaptadores) en 3 capas + configuración,
dentro de un paquete `src/customers/`:

- **`domain/`** (núcleo, sin dependencias de frameworks):
  - `entities/customer.py`: entidad `Customer` (POO pura, con sus propias
    validaciones de invariantes básicas: nombre no vacío, edad en rango,
    email con formato válido). No conoce Flask ni SQLAlchemy.
  - `exceptions.py`: excepciones tipadas del dominio
    (`CustomerNotFoundError`, `CustomerValidationError`,
    `CustomerAlreadyDeletedError`, `CustomerEmailAlreadyExistsError`).
  - `repositories/customer_repository.py`: **puerto** — interfaz abstracta
    (`abc.ABC` o `typing.Protocol`) `CustomerRepository` con los métodos
    `add`, `get_by_id`, `list_active`, `update`, `soft_delete`. El dominio y
    la aplicación dependen de esta interfaz, nunca de una implementación
    concreta (Inversión de Dependencias / DIP).

- **`application/`** (casos de uso, orquestan el dominio a través de los
  puertos; sin conocer Flask ni SQLAlchemy):
  - `dtos/customer_dto.py`: DTOs de entrada/salida (`CreateCustomerInput`,
    `UpdateCustomerInput`, `CustomerOutput`) para desacoplar la
    entidad de dominio de los contratos de la API.
  - `use_cases/`: una clase por caso de uso, responsabilidad única (SRP):
    `CreateCustomerUseCase`, `ListCustomersUseCase`, `GetCustomerUseCase`,
    `UpdateCustomerUseCase`, `DeleteCustomerUseCase`. Cada una recibe el
    puerto `CustomerRepository` por constructor (inyección de dependencias).

- **`infrastructure/`** (adaptadores, frameworks y detalles técnicos):
  - `persistence/`: adaptador de salida.
    - `models/customer_model.py`: modelo ORM SQLAlchemy 2.0 (`Mapped`,
      `mapped_column`) — separado de la entidad de dominio.
    - `mappers/customer_mapper.py`: conversión `Customer` (dominio) ↔
      `CustomerModel` (ORM).
    - `repositories/sqlalchemy_customer_repository.py`: implementación
      concreta de `CustomerRepository` usando SQLAlchemy (adaptador que
      "cumple" el puerto del dominio).
    - `database.py`: engine, `sessionmaker`, gestión de sesión por request.
  - `web/`: adaptador de entrada (Flask).
    - `app.py`: *application factory* `create_app()`.
    - `schemas/customer_schema.py`: validadores manuales de request JSON
      (sin librería externa) que producen los DTOs de `application/` o
      lanzan `CustomerValidationError`.
    - `blueprints/customers_blueprint.py`: rutas Flask; cada ruta solo
      parsea/valida el request, invoca el caso de uso correspondiente y
      serializa la respuesta — sin lógica de negocio (evita fuga de lógica
      al controlador).
    - `error_handlers.py`: mapeo centralizado de excepciones de dominio a
      respuestas HTTP + logging.
  - `config/settings.py`: configuración vía variables de entorno
    (`DATABASE_URL`, `FLASK_ENV`, etc.), sin dependencias nuevas
    (`os.getenv`).

Principios SOLID aplicados:
- **SRP**: cada caso de uso, cada repositorio, cada mapper tiene una única
  responsabilidad.
- **OCP**: nuevas reglas de validación o nuevos adaptadores de persistencia
  se agregan sin modificar el dominio.
- **LSP**: cualquier implementación de `CustomerRepository` (SQLAlchemy hoy,
  en memoria en tests) es intercambiable.
- **ISP**: el puerto `CustomerRepository` solo expone los métodos que la
  aplicación necesita.
- **DIP**: `application/` depende de la abstracción `CustomerRepository`,
  no de SQLAlchemy; `infrastructure/persistence` es quien implementa esa
  abstracción.

## 2. Estructura de carpetas propuesta

```
customers/
├── pyproject.toml
├── uv.lock
├── README.md
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_create_customers_table.py
├── src/
│   └── customers/
│       ├── __init__.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── entities/
│       │   │   ├── __init__.py
│       │   │   └── customer.py
│       │   ├── exceptions.py
│       │   └── repositories/
│       │       ├── __init__.py
│       │       └── customer_repository.py
│       ├── application/
│       │   ├── __init__.py
│       │   ├── dtos/
│       │   │   ├── __init__.py
│       │   │   └── customer_dto.py
│       │   └── use_cases/
│       │       ├── __init__.py
│       │       ├── create_customer.py
│       │       ├── list_customers.py
│       │       ├── get_customer.py
│       │       ├── update_customer.py
│       │       └── delete_customer.py
│       └── infrastructure/
│           ├── __init__.py
│           ├── config/
│           │   ├── __init__.py
│           │   └── settings.py
│           ├── persistence/
│           │   ├── __init__.py
│           │   ├── database.py
│           │   ├── models/
│           │   │   ├── __init__.py
│           │   │   └── customer_model.py
│           │   ├── mappers/
│           │   │   ├── __init__.py
│           │   │   └── customer_mapper.py
│           │   └── repositories/
│           │       ├── __init__.py
│           │       └── sqlalchemy_customer_repository.py
│           └── web/
│               ├── __init__.py
│               ├── app.py
│               ├── error_handlers.py
│               ├── logging_config.py
│               ├── schemas/
│               │   ├── __init__.py
│               │   └── customer_schema.py
│               └── blueprints/
│                   ├── __init__.py
│                   └── customers_blueprint.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── domain/
│   │   │   └── test_customer_entity.py
│   │   └── application/
│   │       ├── fakes/
│   │       │   └── in_memory_customer_repository.py
│   │       ├── test_create_customer_use_case.py
│   │       ├── test_list_customers_use_case.py
│   │       ├── test_get_customer_use_case.py
│   │       ├── test_update_customer_use_case.py
│   │       └── test_delete_customer_use_case.py
│   └── integration/
│       ├── conftest.py
│       ├── test_customers_api_post.py
│       ├── test_customers_api_list.py
│       ├── test_customers_api_get.py
│       ├── test_customers_api_patch.py
│       └── test_customers_api_delete.py
└── specs/
    ├── customer-contracts.md
    └── implementation-plan.md
```

`main.py` actual se reemplaza por el *entry point* de Flask
(`create_app()` en `infrastructure/web/app.py`), ejecutado vía
`uv run flask --app customers.infrastructure.web.app:create_app run`.

## 3. Modelo de datos y migraciones

### Entidad `Customer` (dominio) — invariantes de negocio
- `id`: entero, autogenerado (no editable por el cliente de la API).
- `name`: str no vacío, 1–255 caracteres.
- `age`: int, 0–120.
- `email`: str no vacío, formato de email válido, ≤255 caracteres.
- `created_at`: fecha de creación, gestionada por infraestructura.
- `updated_at`: fecha de última modificación, gestionada por infraestructura.
- `deleted_at`: nulo mientras el cliente esté activo; se setea en soft delete.

### Tabla `customers` (PostgreSQL, vía SQLAlchemy 2.0 + Alembic)

```sql
CREATE TABLE customers (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 0 AND age <= 120),
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX idx_customers_deleted_at ON customers (deleted_at);
```

- `updated_at` se actualiza desde la capa de aplicación/repositorio en cada
  `UPDATE` (no se usa trigger de DB, para mantener la lógica en Python y
  testeable).
- `email` es único a nivel de base de datos (constraint `UNIQUE`); el
  repositorio traduce la violación de esta restricción (`IntegrityError`) a
  una excepción de dominio `CustomerEmailAlreadyExistsError`, que la capa web
  mapea a `409 Conflict`.
- Migración inicial `migrations/versions/0001_create_customers_table.py`
  (Alembic) crea la tabla anterior, incluyendo el constraint `UNIQUE` en
  `email`.

## 4. Diseño de endpoints

Todas las rutas bajo el blueprint `customers_blueprint`, prefijo `/customers`.
Respuestas de error homogéneas: `{"error": "<mensaje>"}` con logging del
detalle técnico en servidor (nunca se expone stacktrace ni detalles internos
al cliente).

### POST /customers
- Valida body JSON: `name`, `age`, `email` requeridos y con las reglas de la
  sección 3.
- Casos de error:
  - JSON ausente/malformado → `400 {"error": "invalid or missing JSON body"}`
  - Campo faltante o inválido → `400` con detalle por campo
    (`{"error": "validation failed", "details": {"age": "must be between 0 and 120"}}`)
  - Email ya registrado (en cliente activo o soft-deleted) → `409 {"error": "email already exists"}`
  - Falla inesperada de DB → `500` genérico, error real solo en logs
- Éxito → `201` con `{"id", "name", "age", "email"}`

### GET /customers/all
- Sin parámetros (paginación fuera de alcance de este spec; se documenta
  como mejora futura).
- Excluye registros con `deleted_at != NULL`.
- Éxito → `200` con lista (posiblemente vacía) de `{"id","name","age","email"}`.
- Falla inesperada de DB → `500`.

### GET /customers/:id
- Ruta con convertidor `<int:customer_id>` (si no es entero, Flask/Werkzeug
  devuelve `404` automáticamente, consistente con el spec).
- No encontrado o `deleted_at != NULL` → `404 {"error": "customer not found"}`.
- Éxito → `200` con `{"id","name","age","email"}`.
- Falla inesperada de DB → `500`.

### PATCH /customers/:id
- Body JSON con cualquier subconjunto de `name`, `age`, `email` (ver
  supuesto #7). Si `id` viene en el body y difiere del de la URL → `400`.
- Si no hay campos válidos para actualizar → `400 {"error": "no fields to update"}`.
- Cada campo enviado se valida con las mismas reglas de POST.
- Email ya usado por otro cliente → `409 {"error": "email already exists"}`.
- No encontrado / soft-deleted → `404`.
- Éxito → `200` con el recurso actualizado, `updated_at` refrescado
  internamente.
- Falla inesperada de DB → `500`.

### DELETE /customers/:id
- No encontrado / ya eliminado (`deleted_at != NULL`) → `404`.
- Éxito → soft delete (`deleted_at = now()`), `200` con `{}`.
- Falla inesperada de DB → `500`.

### Manejo de errores (transversal)
- `error_handlers.py` registra manejadores para:
  - `CustomerValidationError` → `400`
  - `CustomerNotFoundError` / `CustomerAlreadyDeletedError` → `404`
  - `CustomerEmailAlreadyExistsError` → `409`
  - `werkzeug.exceptions.BadRequest` (JSON malformado) → `400`
  - `Exception` genérica → `500`, log con `logging.exception(...)` incluyendo
    método/ruta/id de request pero sin volcar el body completo (evita
    exponer PII como email en logs de error masivos; si se loguea, se hace a
    nivel DEBUG y solo en entornos no productivos).

## 5. Plan de pruebas (Pytest, patrón AAA) — implementado y validado

### Unitarias (sin Flask, sin DB real)
- `tests/unit/domain/test_customer_entity.py`: construcción válida; nombre
  vacío, edad fuera de rango, email inválido → `CustomerValidationError`.
- `tests/unit/application/fakes/in_memory_customer_repository.py`: doble de
  prueba que implementa el puerto `CustomerRepository` en memoria (permite
  testear casos de uso sin infraestructura, cumpliendo LSP).
- Un archivo de test por caso de uso, cubriendo camino feliz y cada
  escenario de fallo previsible (no encontrado, validación, ya eliminado,
  sin campos para actualizar, `id` de body no coincide con `id` de URL).

### Integración (Flask test client + PostgreSQL real)
- Se usa una base de datos Postgres real de pruebas (servicio
  `db_test` en `docker-compose.yml`), no SQLite ni mocks, para ser fieles al
  motor de producción y a los `CHECK` constraints definidos.
- `tests/integration/conftest.py`: fixture `app` (factory con
  `DATABASE_URL` apuntando a `db_test`), fixture `client`
  (`app.test_client()`), fixture `db_session`/`clean_db` que trunca la tabla
  `customers` antes de cada test (o usa transacción + rollback) para
  aislamiento entre tests.
- Un archivo de test por endpoint cubriendo: éxito, cada validación de
  entrada, `404` (no encontrado / soft-deleted), `409` (email duplicado en
  `POST` y `PATCH`), y al menos un caso de error `5xx` simulando fallo de
  repositorio (con monkeypatch) para verificar que no se filtran detalles
  internos al cliente.
- Cobertura objetivo (ver supuesto #12): `pytest --cov=src/customers
  --cov-report=term-missing --cov-fail-under=85`.

Resultado real: 73 tests (45 unitarios + 28 de integración, incluyendo tres
tests unitarios extra de `Settings.from_env` y dos de integración añadidos
al cerrar huecos de cobertura: ruta desconocida no interceptada por el 500
genérico, e `id` no entero en el body de `PATCH`), **99.5% de cobertura**
sobre `src/customers` (100% en dominio y aplicación). Las dos únicas líneas
sin cubrir son ramas defensivas del repositorio SQLAlchemy (`CustomerModel`
desaparecido entre el `get` del caso de uso y el `update`/`soft_delete`, y
un `IntegrityError` no relacionado con el email) que exigirían condiciones
de carrera artificiales para ejercitarse; se dejaron sin test por bajo
valor relativo al esfuerzo.

## 6. Docker y docker-compose

### Dockerfile (multi-stage, basado en `uv`) — implementado y validado

- Stage `builder`: imagen `python:3.13-slim`, instala `uv`, copia
  `pyproject.toml`/`uv.lock`, ejecuta `uv sync --frozen --no-dev
  --no-install-project` (capa cacheable) y luego `COPY . .` +
  `uv sync --frozen --no-dev` para instalar el propio paquete `customers`.
- Stage final: copia `/app` completo (incluye `.venv`, `src/`, `migrations/`,
  `alembic.ini`) desde `builder`, crea usuario no root, expone el puerto
  `5000`. `CMD` invoca directamente el binario del venv (sin `uv run`, para
  no requerir el binario de `uv` en la imagen final):
  `flask --app customers.infrastructure.web.app:create_app run --host=0.0.0.0 --port=5000`.
- **`UV_PYTHON_DOWNLOADS=never`**: necesario porque, sin esto, `uv sync`
  descarga su propio intérprete Python bajo `/root/.local/...` en el stage
  `builder`; ese path no se copia al stage final y el venv queda con un
  symlink roto. Con esta variable, `uv` usa el Python del sistema de la
  imagen base (3.13.14, satisface `requires-python >=3.13.5`).
- **`.python-version` excluido vía `.dockerignore`**: el archivo pinea la
  versión exacta `3.13.5`; si entra al contexto de build, el segundo
  `uv sync` (tras `COPY . .`) exige esa versión exacta y falla porque el
  sistema tiene 3.13.14, no 3.13.5. Excluirlo del build deja que `uv`
  resuelva contra el rango `>=3.13.5` de `pyproject.toml`.

### docker-compose.yml — implementado y validado

- `db`: `postgres:16-alpine`, variables `POSTGRES_DB/USER/PASSWORD` desde
  `.env`, volumen nombrado para persistencia, `healthcheck` con
  `pg_isready`.
- `db_test`: mismo motor, base de datos `customers_test` separada, usada
  solo por las pruebas de integración (Fase 7).
- `migrate`: build del mismo Dockerfile, comando `alembic upgrade head`,
  `depends_on: db (service_healthy)`. Es un servicio uno-off (corre y
  termina).
- `api`: build del Dockerfile, `depends_on: migrate (service_completed_successfully)`
  — así `docker compose up` aplica migraciones automáticamente antes de
  levantar la API —, variable `DATABASE_URL` tomada de `.env`, puerto
  publicado **`8000:5000`** (el contenedor sigue escuchando internamente en
  5000; en macOS el puerto 5000 del host está ocupado por el receptor
  AirPlay del sistema — `Server: AirTunes/...` respondiendo con 403 — por lo
  que se publica en 8000 en su lugar).
- `.env.example` documenta todas las variables requeridas
  (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DATABASE_URL`,
  `TEST_DATABASE_URL`, `FLASK_ENV`).

Validado end-to-end: `docker compose up -d` levanta los 4 servicios, la
migración crea la tabla `customers` en Postgres real, y los 5 endpoints
responden correctamente vía `curl` contra `http://localhost:8000` (incluida
la persistencia del soft delete y los timestamps gestionados por la app).

## 7. Orden recomendado de implementación

1. **Fase 0 — Confirmación**: validar con el usuario la tabla de supuestos
   de la sección 0 (en especial 6, 7, 9, 11, 12).
2. **Fase 1 — Base del proyecto**: actualizar `pyproject.toml`
   (dependencias: `flask`, `sqlalchemy>=2`, `psycopg[binary]`, `alembic`,
   `pytest`, `pytest-cov`, `ruff` como dev-dependency), crear estructura
   `src/`/`tests/`, `.gitignore`, `.env.example`.
3. **Fase 2 — Dominio**: entidad `Customer`, excepciones, puerto
   `CustomerRepository`. Pruebas unitarias de entidad.
4. **Fase 3 — Aplicación**: DTOs y los 5 casos de uso, con repositorio fake
   en memoria y sus pruebas unitarias (TDD recomendado: test primero).
5. **Fase 4 — Persistencia**: modelo ORM, mapper, engine/sesión,
   `SQLAlchemyCustomerRepository`, migración inicial de Alembic.
6. **Fase 5 — Web**: *application factory*, validadores manuales de
   request, blueprint con las 5 rutas, manejadores de error centralizados,
   logging.
7. **Fase 6 — Contenerización**: Dockerfile, docker-compose, validar
   `docker compose up` + `alembic upgrade head` + smoke test manual con
   `curl`.
8. **Fase 7 — Pruebas de integración**: contra `db_test` en
   docker-compose, medir cobertura.
9. **Fase 8 — Calidad**: `ruff check`, `ruff format --check`, revisión de
   reglas de seguridad, ajustes finales y actualización del `README.md`
   con instrucciones de arranque local y con Docker. — **implementado y
   validado**. Se añadió `[tool.ruff]` a `pyproject.toml` (hasta ahora
   Ruff corría con el set de reglas por defecto, sin las de seguridad):
   `E`, `F`, `I` (imports), `UP` (sintaxis moderna), `B` (bugbear), `C4`
   (comprehensions) y **`S` (flake8-bandit, seguridad)** — `S101` (uso de
   `assert`) exceptuado solo en `tests/**`, donde es el patrón normal de
   pytest. Cero hallazgos de seguridad. Los fixes automáticos modernizaron
   `datetime.now(timezone.utc)` → `datetime.now(UTC)`, `Union`/`Sequence`
   de `typing` → sintaxis `X | Y` / `collections.abc`, y ordenaron
   imports. También se resolvieron los `E501` (líneas largas) exponiendo
   `SQLAlchemyCustomerRepository` en el `__init__.py` de su paquete en vez
   de forzar el `line-length` global. Revisión manual adicional (fuera del
   alcance de Ruff): sin `eval`/`exec`/`pickle`/`subprocess`, sin SQL crudo
   con interpolación de datos de usuario (el único `text()` es un
   `TRUNCATE` estático en tests), sin secretos hardcodeados en `.py`.
   Suite completa (73 tests) y build de Docker re-verificados tras los
   cambios: todo en verde.

## 8. Riesgos y dependencias

- **Reglas de negocio no explícitas** (rangos de validación, unicidad de
  email, comportamiento exacto de `PATCH`/`DELETE`) son el principal riesgo:
  implementarlas sin confirmación puede requerir rework. Mitigado por la
  sección 0.
- **Dependencias añadidas fuera del stack literal del spec** (`Alembic`,
  `Ruff`, `psycopg`): se marcan explícitamente para decisión del usuario;
  ninguna se instalará antes de la Fase 1.
- **Pruebas de integración requieren Postgres real**: si el entorno de
  desarrollo/CI no puede levantar `docker-compose`, esas pruebas quedarán
  bloqueadas; se documentará claramente el comando de arranque
  (`docker compose up -d db_test`) como prerrequisito.
- **SQLAlchemy 2.0 style**: se asume esta versión (API moderna con
  `Mapped`/`mapped_column`); si el usuario requiere 1.4 legacy style, ajustar
  Fase 4.
- **Paginación / filtros en `GET /customers/all`**: fuera de alcance del
  spec actual; se deja como mejora futura, no bloquea esta implementación.
