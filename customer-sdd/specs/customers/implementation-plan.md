# Plan de implementación — Gestión de clientes y direcciones

> Traduce a fases y cambios concretos de repositorio la especificación
> técnica `specs/customers/plan.md`, que a su vez implementa la
> especificación funcional `specs/customers/spec.md`
> (`API-CUSTOMERS-001`, v0.1.0, estado Borrador). Este documento es el
> paso 4 del flujo de trabajo (plan de implementación) y precede a la
> escritura de código.

---

## 0. Metadatos

- **Referencia técnica:** `specs/customers/plan.md` (todas las secciones; se cita la sección concreta en cada fase)
- **Referencia funcional:** `specs/customers/spec.md` v0.1.0
- **Alcance de este documento:** únicamente planificación de la implementación. No contiene código de aplicación ni pruebas — eso corresponde a la ejecución de las fases descritas aquí en un turno posterior.
- **Estado del repositorio al momento de planear:** proyecto vacío. Solo existen `main.py` (placeholder `Hello from customers!`), `pyproject.toml` (sin dependencias declaradas), `.python-version` (`3.13.5`) y `README.md` (vacío). No hay `src/`, `tests/`, `migrations/`, `Dockerfile` ni `docker-compose.yml`.
- **Convención de trazabilidad:** cada fase referencia explícitamente las secciones de `plan.md` y los `RF`/`RN`/`VAL`/`ERR`/`CA` de `spec.md` que sustentan sus decisiones. La tabla consolidada está en la sección 12.

---

## 1. Resumen de fases

| Fase | Nombre | Depende de | Objetivo |
|---|---|---|---|
| 0 | Bootstrap del proyecto | — | Estructura de carpetas, dependencias, configuración de calidad y despliegue local, sin lógica de negocio |
| 1 | Dominio | Fase 0 | Value objects, entidades, excepciones y puertos de repositorio para `Customer` y `Address` |
| 2 | Aplicación | Fase 1 | Casos de uso RF-001 a RF-009 y DTO del sobre de resultado (RN-006) |
| 3 | Infraestructura de persistencia | Fase 1 | Modelos SQLAlchemy, migraciones Alembic y adaptadores de repositorio |
| 4 | Infraestructura HTTP | Fases 2 y 3 | Schemas de request, blueprints, manejador de errores y application factory |
| 5 | Pruebas unitarias | Fases 1 y 2 | Cobertura de dominio y aplicación con repositorios fake en memoria |
| 6 | Pruebas de integración | Fases 3 y 4 | Cobertura de persistencia real, HTTP end-to-end y concurrencia |
| 7 | Validación de calidad y despliegue local | Fases 5 y 6 | `ruff`, `mypy`, `pytest` en verde y stack levantado vía `docker-compose` |

Detalle de paralelización en la sección 11.

---

## 2. Fase 0 — Bootstrap del proyecto

**Objetivo:** dejar el repositorio listo para escribir código de dominio/aplicación/infraestructura, sin implementar ninguna regla de negocio todavía.

**Referencias:** `plan.md` §4 (estructura de carpetas), §5.1 (Alembic), §5.2 (Docker/despliegue), §0 (stack).

### 2.1 Archivos a crear/editar

| Archivo | Acción | Contenido a alto nivel |
|---|---|---|
| `pyproject.toml` | Editar | Agregar dependencias de runtime: `flask`, `sqlalchemy>=2`, `alembic`, `psycopg[binary]>=3.1`, `gunicorn`. Agregar `[dependency-groups] dev = ["pytest", "ruff", "mypy"]` (formato de grupos de dependencias de `uv`). Agregar `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]` (con `testpaths = ["tests"]`) |
| `.env.example` | Crear | Documenta `DATABASE_URL`, `FLASK_ENV`, `LOG_LEVEL` (variables mínimas de `plan.md` §5.2). No se usa `python-dotenv`: `infrastructure/config.py` (Fase 4) leerá únicamente `os.environ`, evitando una dependencia no solicitada por el stack declarado |
| `src/customers/__init__.py` | Crear | Paquete raíz vacío |
| `src/customers/domain/__init__.py`, `domain/customer/__init__.py`, `domain/address/__init__.py` | Crear | Paquetes vacíos (contenido en Fase 1) |
| `src/customers/application/__init__.py`, `application/customer/__init__.py`, `application/address/__init__.py` | Crear | Paquetes vacíos (contenido en Fase 2) |
| `src/customers/infrastructure/__init__.py`, `infrastructure/http/__init__.py`, `infrastructure/persistence/__init__.py` | Crear | Paquetes vacíos (contenido en Fases 3 y 4) |
| `tests/unit/domain/`, `tests/unit/application/`, `tests/integration/persistence/`, `tests/integration/http/` | Crear (directorios) | Carpetas vacías según el árbol de `plan.md` §4, listas para las Fases 5 y 6 |
| `alembic.ini` + `migrations/env.py` + `migrations/script.py.mako` + `migrations/versions/` | Crear (comando `alembic init migrations`) | Esqueleto estándar de Alembic; `sqlalchemy.url` se deja vacío en `alembic.ini` (se inyecta desde `DATABASE_URL` en `migrations/env.py` en la Fase 3, nunca hardcodeado, según `plan.md` §5.1) |
| `Dockerfile` | Crear | Imagen `python:3.13-slim`, instala dependencias con `uv sync --frozen`, copia `src/`, expone el puerto de la app (`plan.md` §5.2) |
| `entrypoint.sh` | Crear | Script que ejecuta `alembic upgrade head` y luego `exec gunicorn` contra la app creada por `create_app()` (`plan.md` §5.2) |
| `docker-compose.yml` | Crear | Tres servicios: `db` (Postgres, uso de desarrollo/despliegue), `db_test` (Postgres en puerto distinto, exclusivo para pruebas de integración de la Fase 6, según `plan.md` §6.2) y `api` (build del `Dockerfile`, depende de `db`, usa `entrypoint.sh`) |
| `README.md` | Editar | Instrucciones mínimas: cómo instalar (`uv sync`), levantar el stack (`docker-compose up`), correr pruebas y linters |

### 2.2 Dependencias entre pasos de la fase

1. `pyproject.toml` primero (todo lo demás depende de que `uv sync` funcione).
2. Estructura de paquetes (`src/customers/...`, `tests/...`) en paralelo entre sí, sin orden estricto.
3. `alembic init migrations` después de que `pyproject.toml` tenga `alembic` instalado.
4. `Dockerfile`, `entrypoint.sh` y `docker-compose.yml` pueden crearse en paralelo con el resto; solo dependen conceptualmente de que exista `main.py`/`create_app()` como destino final (ese código llega en Fase 4), por lo que su contenido puede quedar con referencias "hacia adelante" (p. ej. `CMD` apuntando a `main:app`) sin bloquear la fase.

### 2.3 Criterios de salida (checklist)

- [ ] `uv sync` instala todas las dependencias sin error.
- [ ] `uv run ruff check .` y `uv run mypy src` corren sin fallar por configuración (aunque no haya código de negocio todavía).
- [ ] La estructura de carpetas coincide exactamente con el árbol de `plan.md` §4.
- [ ] `docker-compose config` valida sin errores de sintaxis.
- [ ] `alembic.ini`/`migrations/env.py` existen y `alembic current` no falla contra una `DATABASE_URL` de prueba (aunque no haya migraciones aún).

---

## 3. Fase 1 — Capa de dominio (`Customer`, `Address`)

**Objetivo:** modelar las reglas de negocio como invariantes de dominio, independientes de Flask/SQLAlchemy.

**Referencias:** `plan.md` §1.1, §1.4, §3, §4 (árbol `domain/`); `spec.md` RN-001 a RN-006, VAL-001 a VAL-010.

### 3.1 Orden de implementación (estrictamente secuencial dentro del paquete `customer`, luego `address`)

| Paso | Archivo | Contenido a alto nivel |
|---|---|---|
| 1 | `src/customers/domain/customer/value_objects.py` | `Email` (trim+lower, valida formato — VAL-001), `Name` (no vacío tras trim — VAL-003), `Identification` (solo trim, sin lower — VAL-004, decisión de negocio Q-001 confirmada en `plan.md` §1.1/§7.1), `Age` (entero, `0 <= age <= 120` — VAL-005 + cota de sanidad Q-002), `CustomerId` (wrapper de `uuid.UUID` v4) |
| 2 | `src/customers/domain/customer/exceptions.py` | `InvalidEmailError`, `InvalidNameError`, `InvalidIdentificationError`, `InvalidAgeError`, `DuplicateEmailError`, `DuplicateIdentificationError` (ver nota de riesgo en §11 sobre el código provisional `ERR-008`), `MaxAddressesExceededError` (RN-003/VAL-007), `CustomerNotFoundError` (VAL-006) |
| 3 | `src/customers/domain/customer/entities.py` | Agregado `Customer` (aggregate root): construcción a partir de los value objects, `status` (`ACTIVE`/`DELETED`), colección de `Address` cargadas, método `add_address(address)` que lanza `MaxAddressesExceededError` si ya hay 5 direcciones `ACTIVE` (RN-003), método `mark_deleted()` que también marca `DELETED` cada dirección activa asociada (RN-004) |
| 4 | `src/customers/domain/customer/repository.py` | Puerto `CustomerRepository` (`Protocol`/`ABC`) con, como mínimo: `add`, `get_by_id`, `get_by_id_for_update` (soporta el bloqueo pesimista de `plan.md` §1.4, necesario para la Fase 3), `list_paginated`, `find_by_email`, `find_by_identification`, `update`. **Importante:** el método de bloqueo pesimista debe quedar definido aquí aunque su implementación real llegue en la Fase 3, para no tener que volver a tocar el puerto de dominio después |
| 5 | `src/customers/domain/address/value_objects.py` | `Country`, `State`, `City`, `StreetAddress`, `PostalCode` (todos: no vacíos tras trim — VAL-009), `AddressId` (wrapper de `uuid.UUID` v4). Referencian `CustomerId` del paso 1 para tipar `customer_id` |
| 6 | `src/customers/domain/address/exceptions.py` | `InvalidAddressFieldError`, `AddressNotFoundError` (VAL-010), `AddressCustomerMismatchError` (VAL-008/ERR-006) |
| 7 | `src/customers/domain/address/entities.py` | Entidad `Address`: no puede construirse sin `customer_id` válido (RN-005), campo `status` |
| 8 | `src/customers/domain/address/repository.py` | Puerto `AddressRepository` con: `add`, `get_by_id`, `list_by_customer` (activas por defecto), `count_active_by_customer`, `update`, `mark_all_deleted_by_customer` (soporte de RN-004 dentro de `DeleteCustomer`, Fase 2) |

### 3.2 Nota de diseño obligatoria — agregación de errores de validación (ver riesgo en §11)

`plan.md` §2.5 exige que, ante una dirección con varios campos vacíos, la respuesta incluya **un elemento en `errors[]` por cada campo inválido**, no solo el primero. Si cada value object lanza su excepción en el constructor, una construcción directa de la entidad detendría la validación en el primer campo inválido. Para cumplir esto, la Fase 1 debe exponer, junto a cada value object, una función `validate(value) -> Error | None` que **no** lance excepción (o bien capturar cada excepción de forma individual desde la Fase 2), de modo que la capa de aplicación pueda intentar construir cada campo por separado y acumular todos los fallos antes de decidir si rechaza la operación. Este mismo mecanismo se reutiliza en `schemas.py` (Fase 4) para errores de forma/tipo del JSON.

### 3.3 Criterios de salida (checklist)

- [ ] Los value objects de `Customer` cubren VAL-001 (`Email`), VAL-003 (`Name`), VAL-004 (`Identification`), VAL-005 (`Age`), incluyendo la cota `age <= 120` (Q-002, `plan.md` §7.2).
- [ ] `Identification` normaliza solo `trim` (no `lower`), documentado explícitamente en el docstring del value object, referenciando la decisión de `plan.md` §1.1/§7.1.
- [ ] `Customer.add_address` lanza `MaxAddressesExceededError` exactamente al intentar agregar una 6ª dirección activa (RN-003).
- [ ] `Customer.mark_deleted()` deja el propio cliente y todas sus direcciones activas en `DELETED` (RN-004), sin borrado físico (Q-004, `plan.md` §7.4).
- [ ] Los value objects de `Address` cubren VAL-009 (todos los campos obligatorios, incluyendo `postal_code` sin excepción por país — Q-005, `plan.md` §7.5).
- [ ] `Address` no puede existir sin un `customer_id` (RN-005).
- [ ] Los puertos `CustomerRepository`/`AddressRepository` exponen todos los métodos que las Fases 2 y 3 necesitarán (ver tabla 3.1), evitando retrabajo posterior del contrato de puerto.
- [ ] Existe el mecanismo de validación "que no aborta en el primer error" descrito en 3.2.

---

## 4. Fase 2 — Capa de aplicación (casos de uso RF-001 a RF-009)

**Objetivo:** orquestar el dominio y los puertos de repositorio para cada requisito funcional, sin conocer Flask ni SQLAlchemy.

**Referencias:** `plan.md` §1.4, §2.4, §2.5, §3, §4 (árbol `application/`); `spec.md` RF-001 a RF-009, RN-001 a RN-006.

### 4.1 Orden de implementación

| Paso | Archivo | Contenido a alto nivel | RF / RN / VAL |
|---|---|---|---|
| 1 | `src/customers/application/operation_result.py` | DTO `OperationResult` (`success`, `operation`, `entity`, `entity_status`, `message`, `data`, `errors`) — sobre de resultado de `plan.md` §2.1/RN-006. Todos los casos de uso siguientes lo construyen como valor de retorno | RN-006 |
| 2 | `src/customers/application/customer/create_customer.py` | Valida campos (usando el mecanismo de 3.2 para acumular errores), verifica unicidad de `email` (VAL-002) e `identification` (VAL-011 provisional, ver §11) vía repositorio, construye hasta 5 `Address` si vienen en el payload, persiste de forma atómica (todo o nada — `plan.md` §2.5) | RF-001, RN-001/002/003/006, VAL-001..005, VAL-007, VAL-009 |
| 3 | `src/customers/application/customer/get_customer.py` | Busca por id excluyendo `DELETED` (VAL-006), incluye direcciones activas embebidas | RF-002 |
| 4 | `src/customers/application/customer/list_customers.py` | Paginación `page`/`page_size` (Q-006, `plan.md` §7.6, por defecto 20, máximo 100), sin `addresses` embebidas (`plan.md` §2.2) | RF-003 |
| 5 | `src/customers/application/customer/update_customer.py` | Reemplazo completo (`PUT`), excluye al propio cliente en la verificación de unicidad de `email`/`identification` (`plan.md` §2.5) | RF-004, RN-001/002/006, VAL-002, VAL-011 (provisional) |
| 6 | `src/customers/application/customer/delete_customer.py` | Soft delete del cliente y de todas sus direcciones asociadas (RN-004) vía `Customer.mark_deleted()` + `AddressRepository.mark_all_deleted_by_customer` | RF-005, RN-004/006 |
| 7 | `src/customers/application/address/create_address.py` | Verifica existencia de cliente (VAL-006), usa `CustomerRepository.get_by_id_for_update` (bloqueo pesimista, `plan.md` §1.4) antes de contar direcciones activas e insertar (VAL-007/RN-003) | RF-006, RN-003/005/006, VAL-006, VAL-007, VAL-009 |
| 8 | `src/customers/application/address/list_addresses.py` | Verifica cliente existente, lista solo direcciones de ese cliente | RF-007 |
| 9 | `src/customers/application/address/update_address.py` | Verifica cliente y dirección existentes, y que `address.customer_id == customer_id` (VAL-008/ERR-006) | RF-008, RN-005/006, VAL-008, VAL-010 |
| 10 | `src/customers/application/address/delete_address.py` | Verifica cliente y dirección existentes y pertenencia, soft delete | RF-009, RN-005/006, VAL-008, VAL-010 |

### 4.2 Dependencias internas

- El paso 1 (`operation_result.py`) es prerrequisito de los pasos 2 a 10.
- Los pasos 2 a 6 (`customer/*`) y 7 a 10 (`address/*`) son independientes entre sí — ambos grupos solo dependen de los **puertos** definidos en la Fase 1 (`CustomerRepository`/`AddressRepository`), no de implementaciones concretas, por lo que pueden desarrollarse en paralelo.
- Dentro de `customer/*`: `create_customer.py` y `update_customer.py` comparten la lógica de verificación de unicidad de `email`/`identification`; se recomienda extraer un helper compartido (p. ej. `_ensure_unique_email_and_identification(...)`) para no duplicar la consulta a los dos repositorios y mantener consistente el mapeo a `DuplicateEmailError`/`DuplicateIdentificationError`.

### 4.3 Criterios de salida (checklist)

- [ ] Cada caso de uso devuelve siempre un `OperationResult` (éxito o fallo), nunca deja excepciones de dominio sin capturar propagarse fuera de la capa de aplicación sin ser traducidas (RN-006, CA-008).
- [ ] `CreateCustomer` rechaza la operación completa (sin crear cliente ni direcciones) si el payload trae más de 5 direcciones (`plan.md` §2.5).
- [ ] `UpdateCustomer` no dispara falso `DuplicateEmailError`/`DuplicateIdentificationError` cuando el cliente reenvía su propio valor sin cambios (caso límite spec §16, `plan.md` §2.5).
- [ ] `CreateAddress` usa el bloqueo pesimista del repositorio antes de contar+insertar (protección de concurrencia, `plan.md` §1.4).
- [ ] `DeleteCustomer` no deja direcciones huérfanas ni en estado `ACTIVE` tras eliminar el cliente (RN-004, CA-005, Escenario 7 del spec).
- [ ] `UpdateAddress`/`DeleteAddress` rechazan cuando la dirección no pertenece al cliente indicado (VAL-008/ERR-006, Escenario 6 del spec).

---

## 5. Fase 3 — Infraestructura de persistencia

**Objetivo:** implementar los puertos de repositorio contra PostgreSQL y dejar el esquema de base de datos versionado con Alembic.

**Referencias:** `plan.md` §1 completo (modelo de datos), §5.1 (migraciones), §4 (árbol `infrastructure/persistence/`).

### 5.1 Orden de implementación

| Paso | Archivo | Contenido a alto nivel |
|---|---|---|
| 1 | `src/customers/infrastructure/config.py` | Lee `DATABASE_URL`, `FLASK_ENV`, `LOG_LEVEL` desde `os.environ` (sin `python-dotenv`, ver §2.1), expone un objeto/función `get_config()` |
| 2 | `src/customers/infrastructure/logging_config.py` | Configura logging estándar (nivel desde `LOG_LEVEL`, formato con timestamp/nivel/módulo), sin datos sensibles en los mensajes |
| 3 | `src/customers/infrastructure/persistence/db.py` | `engine = create_engine(config.DATABASE_URL)`, `scoped_session`/`sessionmaker`, función `init_engine()`/`get_session()` reutilizable por la Fase 4 (inyección por request) y por los tests de integración |
| 4 | `src/customers/infrastructure/persistence/models.py` | `Base` declarativa, `CustomerModel` y `AddressModel` (SQLAlchemy 2.x, `Mapped`/`mapped_column`) reproduciendo exactamente las tablas `customers`/`addresses` de `plan.md` §1.2/§1.3: tipos, `CHECK` (`btrim(...) <> ''`, rango de `age`, `status IN (...)`), `UNIQUE` (`ux_customers_email`, `ux_customers_identification`), `FOREIGN KEY ... ON DELETE CASCADE`, índices (`ix_customers_status`, `ix_addresses_customer_id`, `ix_addresses_customer_id_status`), `created_at`/`updated_at` |
| 5 | `src/customers/infrastructure/persistence/customer_repository.py` | Adaptador `SqlAlchemyCustomerRepository(CustomerRepository)`: mapea `CustomerModel` ↔ `Customer` (dominio), implementa `get_by_id_for_update` con `SELECT ... FOR UPDATE`, captura `IntegrityError` de `ux_customers_email`/`ux_customers_identification` y las traduce a `DuplicateEmailError`/`DuplicateIdentificationError` como red de seguridad ante condiciones de carrera |
| 6 | `src/customers/infrastructure/persistence/address_repository.py` | Adaptador `SqlAlchemyAddressRepository(AddressRepository)`: mapea `AddressModel` ↔ `Address`, filtra `status <> 'DELETED'` por defecto en lecturas |
| 7 | `migrations/env.py` | Editar el esqueleto generado en Fase 0: `target_metadata = models.Base.metadata`, `sqlalchemy.url` inyectada dinámicamente desde `DATABASE_URL` (no desde `alembic.ini`) |
| 8 | `migrations/versions/0001_create_customers_and_addresses.py` | Generada con `alembic revision --autogenerate -m "create customers and addresses"` a partir de `models.py`, **revisada manualmente** (los `CHECK` con `btrim()` no siempre se autogeneran correctamente — `plan.md` §5.1) |

### 5.2 Dependencias internas

- Orden estrictamente secuencial: `config.py` → `db.py` → `models.py` → (`customer_repository.py` y `address_repository.py` en paralelo) → `migrations/env.py` → primera revisión de Alembic.
- `logging_config.py` es independiente del resto y puede hacerse en paralelo con cualquier paso.
- Los adaptadores de repositorio dependen de los **puertos y entidades de dominio** definidos en la Fase 1 (no se puede implementar `SqlAlchemyCustomerRepository` sin que `CustomerRepository` y `Customer` ya existan).

### 5.3 Criterios de salida (checklist)

- [ ] `alembic upgrade head` contra una base Postgres limpia crea ambas tablas con todos los `CHECK`/`UNIQUE`/`FOREIGN KEY`/índices de `plan.md` §1.2/§1.3.
- [ ] Insertar dos clientes con el mismo `email` (normalizado) viola `ux_customers_email` a nivel de base de datos.
- [ ] Insertar dos clientes con la misma `identification` (tras `trim`) viola `ux_customers_identification` (Q-001 confirmada, `plan.md` §7.1) — **sujeto al riesgo documentado en §11 sobre `ERR-008`/`VAL-011`**.
- [ ] `get_by_id_for_update` genera un `SELECT ... FOR UPDATE` verificable (por ejemplo, inspeccionando el SQL emitido o con una prueba de bloqueo en Fase 6).
- [ ] Las lecturas de ambos repositorios excluyen por defecto entidades con `status = 'DELETED'`.
- [ ] `IntegrityError` de las dos constraints `UNIQUE` se traduce a la excepción de dominio correspondiente, no se propaga como error no controlado (evitaría caer incorrectamente en ERR-007).

---

## 6. Fase 4 — Infraestructura HTTP

**Objetivo:** exponer los casos de uso como una API Flask que respeta el contrato de `plan.md` §2.

**Referencias:** `plan.md` §2 completo, §3 (última fila, validación de forma del JSON), §4 (árbol `infrastructure/http/`).

### 6.1 Orden de implementación

| Paso | Archivo | Contenido a alto nivel |
|---|---|---|
| 1 | `src/customers/infrastructure/http/response_envelope.py` | Función `build_envelope(success, operation, entity, entity_status, message, data=None, errors=None) -> dict` según `plan.md` §2.1 |
| 2 | `src/customers/infrastructure/http/schemas.py` | Parseo manual (Python puro, sin `pydantic`/`marshmallow` — decisión de `plan.md` §3) de `CustomerCreateRequest`, `CustomerUpdateRequest`, `AddressRequest` desde el JSON crudo; usa el mecanismo de acumulación de errores de la sección 3.2 para reportar todos los campos de forma/tipo inválidos a la vez (no solo el primero) |
| 3 | `src/customers/infrastructure/http/error_handlers.py` | Registra manejadores de excepción de Flask que traducen cada excepción de dominio/aplicación al código HTTP y sobre de `plan.md` §2.4 (`ERR-001` a `ERR-007`, y el provisional `ERR-008`, ver riesgo §11) |
| 4 | `src/customers/infrastructure/http/customer_routes.py` | `Blueprint` con los 5 endpoints de `plan.md` §2.2: parsea con `schemas.py`, invoca el caso de uso correspondiente (inyectado), construye la respuesta con `response_envelope.py` |
| 5 | `src/customers/infrastructure/http/address_routes.py` | `Blueprint` con los 4 endpoints de `plan.md` §2.3 |
| 6 | `src/customers/infrastructure/flask_app.py` | `create_app()`: registra ambos blueprints bajo `/api/v1`, registra `error_handlers`, conecta el ciclo de vida de la sesión de SQLAlchemy (`teardown_appcontext`), realiza la inyección de los repositorios concretos (Fase 3) en los casos de uso (Fase 2) por request |
| 7 | `main.py` | Editar: reemplaza el placeholder actual por `app = create_app()` (objetivo de `gunicorn`/`entrypoint.sh`) y un bloque `if __name__ == "__main__": app.run(...)` para desarrollo local |

### 6.2 Dependencias internas

- `response_envelope.py` y `schemas.py` son independientes entre sí, ambos son prerrequisito de `error_handlers.py` (que también depende de las excepciones de dominio/aplicación definidas en Fases 1 y 2) y de las rutas.
- `customer_routes.py` y `address_routes.py` pueden desarrollarse en paralelo una vez existen `schemas.py`, `error_handlers.py`, `response_envelope.py` y los casos de uso (Fase 2) — no dependen entre sí porque `address_routes.py` invoca sus propios casos de uso de `application/address/*`, que ya validan la existencia del cliente.
- `flask_app.py` depende de que ambos blueprints y `error_handlers.py` existan, y de los adaptadores concretos de repositorio (Fase 3) para la inyección de dependencias.
- `main.py` depende de `flask_app.py`.

### 6.3 Criterios de salida (checklist)

- [ ] Cada endpoint de `plan.md` §2.2/§2.3 responde con el código HTTP y el sobre exactos de la tabla de esa sección.
- [ ] `DELETE` responde `200 OK` con `entity_status: "DELETED"` en el cuerpo, nunca `204` (`plan.md` §2.1).
- [ ] El mapeo completo de `plan.md` §2.4 está implementado en `error_handlers.py` (ERR-001 a ERR-007, más el provisional ERR-008 con la advertencia de trazabilidad de §11).
- [ ] El listado de clientes (`GET /customers`) soporta `page`/`page_size` con los valores por defecto/máximos de `plan.md` §7.6, y no embebe `addresses`.
- [ ] Un payload de dirección con varios campos vacíos responde con un elemento en `errors[]` por cada campo (verificable manualmente con `curl`/Postman contra el stack de `docker-compose`, confirmado formalmente en Fase 6).

---

## 7. Fase 5 — Pruebas unitarias

**Objetivo:** cubrir dominio y aplicación sin base de datos ni Flask, con repositorios *fake* en memoria.

**Referencias:** `plan.md` §6.1.

### 7.1 Archivos a crear

| Archivo | Contenido |
|---|---|
| `tests/unit/domain/customer/test_value_objects.py` | `Email` normaliza y valida formato (VAL-001); `Age` rechaza negativos y valores > 120 (VAL-005, Q-002); `Name`/`Identification` rechazan vacío tras `trim` (VAL-003/VAL-004); `Identification` no aplica `lower()` (caso explícito de regresión sobre la decisión de `plan.md` §1.1) |
| `tests/unit/domain/customer/test_entities.py` | `Customer.add_address` rechaza la 6ª dirección activa (RN-003); `Customer.mark_deleted()` deja direcciones activas en `DELETED` |
| `tests/unit/domain/address/test_value_objects.py` | Cada campo de dirección rechaza vacío tras `trim` (VAL-009), incluyendo `postal_code` (Q-005) |
| `tests/unit/domain/address/test_entities.py` | `Address` no se puede construir sin `customer_id` (RN-005) |
| `tests/unit/application/fakes.py` | Implementaciones *fake* en memoria de `CustomerRepository`/`AddressRepository` (listas Python, sin SQL), incluyendo un `get_by_id_for_update` que simplemente delega en `get_by_id` (no hay concurrencia real en memoria; la concurrencia real se prueba en Fase 6) |
| `tests/unit/application/customer/test_create_customer.py` | Creación exitosa; email duplicado (ERR-002); identificación duplicada (riesgo ERR-008, §11); cliente con 0/5/6 direcciones en el payload |
| `tests/unit/application/customer/test_get_customer.py` | Cliente existente; cliente inexistente o `DELETED` (ERR-003) |
| `tests/unit/application/customer/test_list_customers.py` | Paginación por defecto y con parámetros explícitos |
| `tests/unit/application/customer/test_update_customer.py` | Actualización exitosa; email sin cambios (no debe disparar falso duplicado); identificación sin cambios (ídem); cliente inexistente |
| `tests/unit/application/customer/test_delete_customer.py` | Eliminación exitosa; cliente con direcciones asociadas (deben quedar `DELETED`, no huérfanas); cliente inexistente |
| `tests/unit/application/address/test_create_address.py` | Creación exitosa; cliente inexistente (ERR-003); límite de 5 direcciones alcanzado (ERR-005) |
| `tests/unit/application/address/test_list_addresses.py` | Lista solo direcciones del cliente solicitado |
| `tests/unit/application/address/test_update_address.py` | Actualización exitosa; dirección de otro cliente (ERR-006); dirección inexistente (ERR-004) |
| `tests/unit/application/address/test_delete_address.py` | Eliminación exitosa; dirección de otro cliente; dirección inexistente |

### 7.2 Dependencias internas

- `fakes.py` es prerrequisito de todos los tests de `tests/unit/application/*`.
- Los tests de dominio (`tests/unit/domain/*`) no dependen de `fakes.py` y pueden escribirse en paralelo con cualquier otro archivo de esta fase.
- Esta fase depende de que las Fases 1 y 2 estén completas, pero **no** de las Fases 3/4 — puede ejecutarse en paralelo con la Fase 3 (ver §11).

### 7.3 Criterios de salida (checklist)

- [ ] `pytest tests/unit` pasa en verde sin requerir Postgres ni Docker levantado.
- [ ] Cada escenario de la tabla de `plan.md` §6.1 tiene al menos una prueba correspondiente.
- [ ] Los escenarios 1, 2, 3, 4, 6 y 7 del spec funcional (§12) están cubiertos a nivel de aplicación (no solo HTTP).

---

## 8. Fase 6 — Pruebas de integración

**Objetivo:** validar persistencia real, el flujo HTTP completo y los casos de concurrencia contra PostgreSQL.

**Referencias:** `plan.md` §6.2.

### 8.1 Archivos a crear

| Archivo | Contenido |
|---|---|
| `tests/integration/conftest.py` | Fixtures: engine contra `db_test` (docker-compose), `Base.metadata.create_all()`/`drop_all()` por sesión de pruebas, fixture `app` (`create_app()` en modo pruebas) y `client` (`app.test_client()`) |
| `tests/integration/persistence/test_customer_repository.py` | `ux_customers_email`/`ux_customers_identification` actúan como red de seguridad; `get_by_id_for_update` bloquea correctamente; filtrado por `status <> 'DELETED'` |
| `tests/integration/persistence/test_address_repository.py` | FK a `customers.id`; filtrado por `status <> 'DELETED'`; conteo de activas por cliente |
| `tests/integration/http/test_customer_endpoints.py` | Escenarios 1, 2, 5, 7 y CA-001 a CA-005/CA-008 del spec, verificando sobre de resultado y código HTTP exactos de `plan.md` §2.4 |
| `tests/integration/http/test_address_endpoints.py` | Escenarios 3, 4, 6 y CA-006/CA-007/CA-008 |
| `tests/integration/test_migrations.py` | Ejecuta `alembic upgrade head` contra una base limpia (no `create_all()`) y valida que el esquema resultante coincide con `models.py` |
| `tests/integration/test_concurrency.py` | `concurrent.futures.ThreadPoolExecutor` (librería estándar, sin dependencia nueva): dos altas simultáneas con el mismo `email`; dos altas simultáneas con la misma `identification`; dos altas simultáneas de la 5ª/6ª dirección para el mismo cliente — verifica que exactamente una tiene éxito en cada caso (casos límite spec §16) |

### 8.2 Dependencias internas

- Todos los archivos de esta fase dependen de `tests/integration/conftest.py`.
- `test_migrations.py` depende de que la migración `0001_...` (Fase 3, paso 8) exista.
- `test_concurrency.py` depende de que `create_address.py` (Fase 2) y `get_by_id_for_update` (Fase 3) estén implementados; es el único archivo que ejercita explícitamente el bloqueo pesimista de `plan.md` §1.4.
- Esta fase requiere el servicio `db_test` de `docker-compose.yml` (Fase 0) levantado antes de ejecutar `pytest tests/integration`.

### 8.3 Criterios de salida (checklist)

- [ ] `docker-compose up -d db_test && pytest tests/integration` pasa en verde.
- [ ] Los 7 escenarios funcionales (§12 del spec) y los 8 criterios de aceptación (§15 del spec) tienen al menos una prueba de integración HTTP correspondiente.
- [ ] Las tres pruebas de concurrencia de `plan.md` §6.2 confirman que solo una operación concurrente tiene éxito en cada caso (email duplicado, identificación duplicada, 6ª dirección).
- [ ] `test_migrations.py` confirma que el esquema generado por Alembic coincide con `Base.metadata` de `models.py` (sin *drift*).

---

## 9. Fase 7 — Validación de calidad y despliegue local

**Objetivo:** dejar el proyecto en un estado verificable y desplegable localmente antes de cerrar la implementación.

**Referencias:** stack declarado (Ruff, MyPy, Pytest, Docker), `plan.md` §5.2.

### 9.1 Pasos

1. `uv run ruff check .` y `uv run ruff format --check .` — corregir hallazgos.
2. `uv run mypy src` — corregir hallazgos de tipado (los puertos `Protocol`/`ABC` de la Fase 1 deben quedar completamente tipados para que esto sea efectivo).
3. `uv run pytest tests/unit` — deben pasar sin infraestructura externa.
4. `docker-compose up -d db_test` seguido de `uv run pytest tests/integration` — deben pasar contra Postgres real.
5. `docker-compose up --build` — validar que `entrypoint.sh` ejecuta `alembic upgrade head` y luego levanta `gunicorn` sirviendo `create_app()`; probar manualmente al menos un flujo completo (crear cliente → crear dirección → consultar → actualizar → eliminar) con `curl`/Postman.
6. Revisar explícitamente con el usuario el porcentaje de cobertura objetivo antes de cerrar esta fase, dado que `plan.md` §6.2 señala expresamente que no hay un umbral definido todavía (ver riesgo en §11).

### 9.2 Criterios de salida (checklist)

- [ ] `ruff`, `mypy` y `pytest` (unitarias + integración) en verde.
- [ ] El stack completo (`api` + `db`) se levanta con `docker-compose up` y responde en `/api/v1/customers`.
- [ ] Todos los checklists de las Fases 0 a 6 están marcados como completos.
- [ ] Los riesgos de la sección 11 fueron revisados explícitamente con el usuario (aceptados, mitigados o convertidos en tareas de seguimiento).

---

## 10. Orden de ejecución recomendado y paralelización

```
Fase 0 (bootstrap)
   │
   ▼
Fase 1 (dominio)
   │
   ├──────────────┐
   ▼              ▼
Fase 2         Fase 3
(aplicación)   (persistencia)
   │              │
   │◄─────┐       │
   ▼      │       ▼
Fase 5    │    (ninguna, Fase 3 no tiene
(unit)    │     fase paralela adicional)
   │      │       │
   │      └───────┤
   │              ▼
   │           Fase 4 (HTTP) — requiere Fases 2 y 3 completas
   │              │
   └──────┬───────┘
          ▼
       Fase 6 (integración) — requiere Fases 3 y 4 completas
          │
          ▼
       Fase 7 (calidad y despliegue) — requiere Fases 5 y 6 completas
```

- **Estrictamente secuencial:** Fase 0 → Fase 1 → (Fase 2 y Fase 3) → Fase 4 → Fase 6 → Fase 7.
- **Paralelizable:** Fase 2 y Fase 3 pueden avanzar simultáneamente una vez cerrada la Fase 1, porque la aplicación depende de los **puertos** de dominio (ya definidos en Fase 1), no de los adaptadores concretos de persistencia.
- **Paralelizable:** la Fase 5 (pruebas unitarias) puede iniciarse tan pronto la Fase 2 esté completa, sin esperar a las Fases 3 o 4 — se ejecuta en paralelo con la Fase 3 si esta aún sigue en curso, y en paralelo con la Fase 4 si esta ya inició.
- **No paralelizable:** la Fase 4 requiere que tanto la Fase 2 (casos de uso a invocar) como la Fase 3 (repositorios concretos a inyectar) estén terminadas.
- **No paralelizable:** la Fase 6 requiere la Fase 3 (esquema/migraciones reales) y la Fase 4 (endpoints HTTP) completas, además del servicio `db_test` de Docker levantado.
- Dentro de cada fase, el orden interno recomendado está detallado en la tabla de "Orden de implementación" correspondiente; los pasos marcados como paralelizables entre sí no tienen dependencia de datos/tipos entre ellos.

---

## 11. Riesgos y bloqueos conocidos

1. **Discrepancia `ERR-008`/`VAL-011` (identificación duplicada) sin formalizar en el spec funcional.** `plan.md` §2.4/§7.1/§8 documenta que Q-001 fue confirmada por negocio pero `specs/customers/spec.md` v0.1.0 todavía no incorpora la regla de negocio, `VAL-0XX` ni `ERR-0XX` correspondientes. Se implementará con los códigos provisionales `VAL-011`/`ERR-008` (Fases 1, 2, 4, 5, 6). **Impacto si el spec funcional se actualiza con códigos distintos:** habrá que renombrar constantes/mensajes en `domain/customer/exceptions.py`, `infrastructure/http/error_handlers.py`, y los `errors[].code` esperados en las pruebas de las Fases 5 y 6. Se recomienda centralizar estos códigos en un único lugar (p. ej. constantes en `error_handlers.py`) para minimizar el costo del cambio.
2. **Q-002 a Q-006 siguen siendo supuestos de ingeniería, no decisiones de negocio confirmadas** (a diferencia de Q-001). Si el responsable funcional responde de forma distinta a lo asumido en `plan.md` §7.2-§7.6, el impacto por pregunta es:
   - Q-002 (límite de edad): cambio acotado a `Age` (Fase 1) y `CHECK` de `age` en `models.py`/migración (Fase 3).
   - Q-003 (catálogo de estados): cambio acotado al `CHECK (status IN (...))` (Fase 3) y a la lógica que decide `entity_status` en las respuestas (Fase 4); el modelado como `VARCHAR` (no `ENUM`) ya anticipa esto.
   - Q-004 (borrado lógico vs físico): cambio acotado a los métodos `mark_deleted`/`mark_all_deleted_by_customer` en la Fase 3 (reemplazar `UPDATE status` por `DELETE`); dominio y contrato HTTP no cambian.
   - Q-005 (`postal_code` obligatorio): cambio acotado al value object `PostalCode` (Fase 1) y a su `CHECK`/nulabilidad (Fase 3).
   - Q-006 (paginación/filtros/orden): cambio de mayor alcance si se agregan filtros/orden — afectaría el contrato de `GET /customers` (Fase 4/6) y el puerto `list_paginated` (Fase 1).
3. **Sin umbral de cobertura de pruebas acordado** (`plan.md` §6.2 lo señala explícitamente como pendiente). Se recomienda decidirlo con el usuario antes de cerrar la Fase 7, para no bloquear las Fases 5/6 con un número arbitrario.
4. **Elección del driver de PostgreSQL (`psycopg[binary]` v3) no está pinneada explícitamente en `plan.md`.** Es una decisión de ingeniería razonable dentro del stack ya declarado (PostgreSQL + SQLAlchemy 2.x), tomada en la Fase 0 de este plan; se señala aquí por transparencia, no requiere confirmación de negocio.
5. **`docker-compose.yml` único con dos servicios de Postgres (`db` y `db_test`)** en vez de un archivo de compose separado para pruebas. Es una decisión de implementación de la Fase 0 para evitar duplicar la definición de infraestructura; si el usuario prefiere archivos separados (p. ej. `docker-compose.yml` + `docker-compose.test.yml`), es un ajuste de bajo costo dentro de la misma fase.
6. **Estrategia de acumulación de errores múltiples (§3.2).** `plan.md` §2.5 exige reportar todos los campos inválidos de una dirección a la vez, pero no especifica el mecanismo técnico. Este documento define que los value objects deben poder validarse sin lanzar excepción de inmediato (o bien capturarse individualmente), tanto en la Fase 1 (dominio) como en la Fase 4 (`schemas.py`). Si no se implementa de forma consistente en ambas capas, el comportamiento observado en Fase 6 podría no coincidir con `plan.md` §2.5 (reportaría solo el primer campo inválido).
7. **El proyecto no tiene `Dockerfile`/`docker-compose.yml` en el árbol de carpetas de `plan.md` §4** (esa sección solo detalla `src/`, `migrations/`, `tests/`). Se agregan en la Fase 0 de este plan porque son necesarios para `plan.md` §5.2 y para las pruebas de integración de §6.2; se señala como una extensión razonable del árbol original, no una desviación de las decisiones ya tomadas.

---

## 12. Trazabilidad consolidada

| Fase | RF cubiertos | RN cubiertas | VAL cubiertas | ERR cubiertos | CA relacionados | Secciones de `plan.md` |
|---|---|---|---|---|---|---|
| 1 (dominio) | — (soporte transversal) | RN-001 a RN-005 | VAL-001, VAL-003, VAL-004, VAL-005, VAL-007, VAL-009, VAL-011 (provisional) | — | — | §1.1, §1.4, §3, §4 |
| 2 (aplicación) | RF-001 a RF-009 | RN-001 a RN-006 | VAL-001 a VAL-011 (provisional) | (mapeo a HTTP ocurre en Fase 4) | — | §1.4, §2.4, §2.5, §3, §4 |
| 3 (persistencia) | — (soporte transversal) | RN-003, RN-005 (integridad referencial) | VAL-002, VAL-007, VAL-011 (provisional, red de seguridad en BD) | — | — | §1 completo, §5.1 |
| 4 (HTTP) | RF-001 a RF-009 (expuestos) | RN-006 (sobre de resultado) | VAL-006, VAL-008, VAL-010 (existencia/pertenencia) | ERR-001 a ERR-007, ERR-008 (provisional) | CA-001 a CA-008 | §2 completo, §3 |
| 5 (unit) | RF-001 a RF-009 (a nivel de aplicación) | RN-001 a RN-006 | Todas las anteriores | — | Escenarios 1-4, 6-7 del spec | §6.1 |
| 6 (integración) | RF-001 a RF-009 (end-to-end) | RN-001 a RN-006 | Todas las anteriores | ERR-001 a ERR-007, ERR-008 (provisional) | CA-001 a CA-008 | §6.2 |
| 7 (calidad/despliegue) | — (transversal) | — | — | — | — | §5.2, §6 |

---
