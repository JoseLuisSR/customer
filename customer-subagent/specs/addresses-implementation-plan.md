# Plan de implementación — API de Addresses (anidada bajo Customer)

Basado en `specs/addresses-contracts.md`. Estado actual del repositorio: la
entidad `Customer` ya está completamente implementada (8 fases, 99.5% de
cobertura, documentada en `specs/implementation-plan.md`). Este plan **no
modifica** ese documento ni reescribe el feature de `Customer`; extiende la
misma arquitectura hexagonal para añadir `Address` como recurso anidado
(`/customers/:id/addresses`), reutilizando las convenciones ya establecidas
(dataclasses de dominio con validación en `__post_init__`, excepciones
tipadas por entidad, puertos `ABC` + adaptador SQLAlchemy, DTOs de
entrada/salida, casos de uso de responsabilidad única, blueprint de Flask,
manejador de errores centralizado, fakes en memoria para tests unitarios,
Postgres real para tests de integración).

No se requieren dependencias nuevas: se reutiliza el stack ya instalado
(`flask`, `sqlalchemy`, `psycopg[binary]`, `alembic`, `pytest`,
`pytest-cov`, `ruff`), conforme al principio de minimalismo de dependencias
ya aplicado en el feature de `Customer`.

## 0. Supuestos y decisiones (confirmados por el usuario el 2026-07-23)

El spec `addresses-contracts.md` tiene los mismos vacíos e inconsistencias
que ya se resolvieron para `Customer`, más algunas nuevas propias de la
relación uno-a-muchos. Se listan todas para confirmación explícita antes de
implementar; donde aplica, se propone la misma decisión ya tomada para
`Customer` por consistencia.

| # | Tema | Decisión propuesta | Origen |
|---|------|---------------------|--------|
| 1 | Título del primer endpoint ("Crear un cliente") | Error de copy-paste del spec de `Customer`; la ruta `POST /customers/:id/addresses` crea una **Address**, no un Customer. Se implementa como creación de dirección. | Nota 1 del encargo |
| 2 | Campo `address` con valor de ejemplo `"2021-01-01"` | Es un error de copy-paste; se trata como **string de línea de dirección** (ej. `"Calle 10 #5-20"`), no como fecha. Internamente se nombra `address_line` (para no colisionar conceptualmente con el nombre de la entidad `Address`); en el JSON de la API se sigue exponiendo literalmente como `"address"`. | Nota 2 del encargo |
| 3 | Campo `postalcode` (sin guión bajo) | **CONFIRMADO**: se expone en la API **literalmente como `"postalcode"`** (tal como aparece en los ejemplos JSON del spec), pero internamente (dominio, DTOs, columna de BD) se usa el nombre idiomático Python `postal_code`. El mapeo JSON⇄dominio ocurre en la capa de schemas (`address_schema.py`), igual que ya ocurre con otros campos. | ✅ Confirmado |
| 4 | Campo `id` en el body de `POST` | Se ignora, igual que en `Customer`: el servidor siempre genera el `id`. | Nota 4 del encargo, mismo criterio que `customer-contracts.md` |
| 5 | Soft delete | `Address` tiene `deleted_at` con el mismo patrón que `Customer`: `DELETE` marca `deleted_at = now()` (no borra la fila); `GET`/`list` excluyen direcciones con `deleted_at != NULL` (las tratan como 404/ausentes). | Nota 5 del encargo |
| 6 | Campos expuestos en las respuestas | Los endpoints devuelven solo `id, country, state, city, postalcode, address` (igual que los ejemplos), aunque la entidad interna guarda también `created_at, updated_at, deleted_at, customer_id`. | Nota 6 del encargo, mismo criterio que `Customer` |
| 7 | Customer padre inexistente o soft-deleted | En los 5 endpoints de `Address`, si el `:id` de customer en la URL no corresponde a un cliente activo (no existe o `deleted_at != NULL`), se responde `404 {"error": "customer not found"}` — se reutiliza `CustomerNotFoundError` ya existente y su manejador HTTP, sin duplicar lógica. | Nota 7 del encargo |
| 8 | Validaciones de `country` / `state` / `city` | String no vacío (tras `strip()`), longitud 1–100. Sin restricción de charset (nombres de lugares pueden incluir tildes, guiones, apóstrofos). | Nota 8 del encargo — supuesto, sin precedente exacto en `Customer` |
| 9 | Validaciones de `postal_code` | String no vacío (tras `strip()`), longitud 1–20. Sin validación de formato/regex, porque los formatos postales varían mucho entre países (alfanuméricos, con espacios o guiones). | Nota 8 del encargo — supuesto |
| 10 | Validaciones de `address_line` | String no vacío (tras `strip()`), longitud 1–255 (igual límite que `Customer.name`). | Nota 8 del encargo — supuesto |
| 11 | Relación `customer_id` (FK) | **CONFIRMADO**: columna `customer_id BIGINT NOT NULL REFERENCES customers(id) ON DELETE CASCADE`. Se usa `ON DELETE CASCADE` como salvaguarda de integridad referencial ante un borrado físico manual de un customer (fuera de la API, que solo hace soft delete); en operación normal vía API nunca se ejecuta un `DELETE` real sobre `customers`, así que este `CASCADE` es defensivo, no parte del flujo funcional. | ✅ Confirmado |
| 12 | `PATCH` — actualización parcial y `id` en el body | Mismo criterio que `Customer`: se permiten campos parciales; si no se envía ningún campo válido → `400`; si el body trae `id` y no coincide con el `:id` de la dirección en la URL → `400`. | Mismo criterio que `Customer`, confirmado en `implementation-plan.md` |
| 13 | Body de respuesta de `DELETE` | `200` con body `{}` (vacío), igual que `Customer`. El spec solo define el status code. | Mismo criterio que `Customer` |
| 14 | Migraciones y calidad | Se reutiliza Alembic (ya confirmado) para una nueva migración `0002_create_addresses_table.py`; se reutiliza Ruff (ya confirmado) sin cambios de configuración. | Ya confirmado en `implementation-plan.md` |
| 15 | Cobertura de pruebas | Mismo umbral ya usado: ≥ 85% global, ≥ 90% en dominio/aplicación. | Ya confirmado en `implementation-plan.md` |
| 16 | Paginación en `GET /customers/:id/addresses` | Fuera de alcance, igual que `GET /customers/all`; se documenta como mejora futura. | Consistente con `Customer` |

Los puntos #3 y #11 fueron confirmados explícitamente por el usuario; el
resto son supuestos razonables que se mantienen salvo objeción. El plan
queda listo para iniciar la implementación.

## 1. Arquitectura

Se extiende la arquitectura hexagonal ya existente en `src/customers/`
añadiendo un segundo "sub-agregado" `Address`, dependiente de `Customer`
pero con su **propio puerto de repositorio** (no se modifica
`CustomerRepository` — principio Abierto/Cerrado: el feature nuevo se añade
sin tocar el contrato ni la implementación existentes de `Customer`).

- **`domain/`**:
  - `entities/address.py`: entidad `Address` (dataclass con validación en
    `__post_init__`, mismo patrón que `Customer`). Incluye `customer_id`
    como atributo obligatorio (una `Address` siempre pertenece a un
    `Customer`).
  - `exceptions.py` (se **extiende**, no se reemplaza): se agregan
    `AddressValidationError`, `AddressNotFoundError`,
    `AddressAlreadyDeletedError`. Se reutiliza `CustomerNotFoundError` ya
    existente para el caso "customer padre no encontrado/soft-deleted"
    (ver supuesto #7) — no se crea una excepción nueva para eso.
  - `repositories/address_repository.py`: **puerto** nuevo
    `AddressRepository` (ABC), con métodos `add`, `get_by_id`,
    `list_active_by_customer`, `update`, `soft_delete`, todos con
    `customer_id` como parte de la firma para garantizar que una dirección
    de un customer nunca sea visible/editable a través del `customer_id`
    de otro (aislamiento del recurso anidado).

- **`application/`**:
  - `dtos/address_dto.py`: `CreateAddressInput`, `UpdateAddressInput`,
    `AddressOutput` (con `from_entity`), mismo patrón que
    `customer_dto.py`. Los DTOs usan nombres idiomáticos (`postal_code`,
    `address_line`); el mapeo a los nombres literales del contrato JSON
    (`postalcode`, `address`) ocurre en `web/schemas/address_schema.py`.
  - `use_cases/`: `CreateAddressUseCase`, `ListAddressesUseCase`,
    `GetAddressUseCase`, `UpdateAddressUseCase`, `DeleteAddressUseCase`.
    Cada caso de uso recibe **ambos puertos** por constructor
    (`CustomerRepository` y `AddressRepository`, inyección de
    dependencias): primero valida que el customer padre existe y está
    activo (reutilizando `CustomerRepository.get_by_id`, que ya excluye
    soft-deleted por defecto — cero cambios en `CustomerRepository`), y
    luego delega en `AddressRepository` para la operación sobre la
    dirección.

- **`infrastructure/`**:
  - `persistence/models/address_model.py`: `AddressModel` (SQLAlchemy 2.0),
    con FK a `customers.id`.
  - `persistence/mappers/address_mapper.py`: conversión `Address` ↔
    `AddressModel`, mismo patrón que `CustomerMapper`.
  - `persistence/repositories/sqlalchemy_address_repository.py`:
    `SQLAlchemyAddressRepository(AddressRepository)`, mismo patrón que
    `SQLAlchemyCustomerRepository`, filtrando siempre por `customer_id`.
  - `web/schemas/address_schema.py`: validadores manuales de request JSON
    (sin librerías externas), que mapean `postalcode`→`postal_code` y
    `address`→`address_line` al construir los DTOs, y a la inversa al
    serializar la respuesta.
  - `web/blueprints/addresses_blueprint.py`: **blueprint nuevo**
    (`addresses_blueprint`), no se modifica `customers_blueprint.py`. Usa
    `url_prefix="/customers/<int:customer_id>/addresses"` (Flask admite
    convertidores de tipo dentro del `url_prefix` de un blueprint), con
    rutas `POST ""`, `GET ""`, `GET "/<int:address_id>"`,
    `PATCH "/<int:address_id>"`, `DELETE "/<int:address_id>"`.
  - `web/app.py`: se **extiende** (cambio mínimo) para registrar el nuevo
    blueprint: `app.register_blueprint(addresses_blueprint)`.
  - `web/error_handlers.py`: se **extiende** (cambio mínimo) añadiendo
    manejadores para `AddressValidationError` (400) y
    `AddressNotFoundError` / `AddressAlreadyDeletedError` (404). No se
    toca el manejador genérico `Exception` → 500 ni los de `Customer`.

Principios SOLID aplicados (adicionales a los ya vigentes para `Customer`):
- **OCP**: el feature `Address` se añade sin modificar `CustomerRepository`,
  `customers_blueprint.py` ni las entidades/casos de uso de `Customer`; los
  únicos archivos existentes que se tocan (`app.py`, `error_handlers.py`)
  reciben adiciones puntuales, no reescritura.
- **ISP**: `AddressRepository` es un puerto independiente con solo los
  métodos que necesita el caso de uso de `Address`; no se amplía
  `CustomerRepository` con responsabilidades que no le corresponden.
- **SRP/DIP**: cada caso de uso de `Address` depende de las abstracciones
  `CustomerRepository`/`AddressRepository`, nunca de SQLAlchemy.

**Desviación señalada**: esta es la primera vez que se registra más de un
blueprint en la aplicación y que un caso de uso depende de dos puertos de
repositorio distintos. No es una desviación de la arquitectura hexagonal
(sigue siendo puertos y adaptadores), pero es un patrón nuevo dentro de este
proyecto que conviene tener presente para features futuros con relaciones
similares.

## 2. Estructura de carpetas y archivos

Archivos **nuevos**:

```
src/customers/
├── domain/
│   ├── entities/
│   │   └── address.py                          [nuevo]
│   └── repositories/
│       └── address_repository.py                [nuevo]
├── application/
│   ├── dtos/
│   │   └── address_dto.py                        [nuevo]
│   └── use_cases/
│       ├── create_address.py                     [nuevo]
│       ├── list_addresses.py                     [nuevo]
│       ├── get_address.py                        [nuevo]
│       ├── update_address.py                     [nuevo]
│       └── delete_address.py                     [nuevo]
└── infrastructure/
    ├── persistence/
    │   ├── models/
    │   │   └── address_model.py                  [nuevo]
    │   ├── mappers/
    │   │   └── address_mapper.py                 [nuevo]
    │   └── repositories/
    │       ├── sqlalchemy_address_repository.py  [nuevo]
    │       └── __init__.py                       [modificado: exporta también SQLAlchemyAddressRepository]
    └── web/
        ├── schemas/
        │   └── address_schema.py                 [nuevo]
        ├── blueprints/
        │   └── addresses_blueprint.py             [nuevo]
        ├── app.py                                  [modificado: registra addresses_blueprint]
        └── error_handlers.py                       [modificado: agrega handlers de Address]

migrations/versions/
└── 0002_create_addresses_table.py                 [nuevo]

tests/unit/
├── domain/
│   └── test_address_entity.py                     [nuevo]
└── application/
    ├── fakes/
    │   └── in_memory_address_repository.py         [nuevo]
    ├── test_create_address_use_case.py             [nuevo]
    ├── test_list_addresses_use_case.py              [nuevo]
    ├── test_get_address_use_case.py                 [nuevo]
    ├── test_update_address_use_case.py               [nuevo]
    └── test_delete_address_use_case.py               [nuevo]

tests/integration/
├── conftest.py                                       [modificado: clean_db trunca también addresses; fixture create_address]
├── test_addresses_api_post.py                        [nuevo]
├── test_addresses_api_list.py                        [nuevo]
├── test_addresses_api_get.py                         [nuevo]
├── test_addresses_api_patch.py                       [nuevo]
└── test_addresses_api_delete.py                      [nuevo]

specs/
├── addresses-contracts.md                            [ya existe]
└── addresses-implementation-plan.md                  [este documento]
```

No se modifica ningún archivo de `domain/entities/customer.py`,
`domain/repositories/customer_repository.py`,
`application/use_cases/*_customer.py`,
`infrastructure/persistence/repositories/sqlalchemy_customer_repository.py`
ni `infrastructure/web/blueprints/customers_blueprint.py`.

## 3. Modelo de datos y migración

### Entidad `Address` (dominio) — invariantes de negocio
- `id`: entero, autogenerado (no editable por el cliente de la API).
- `customer_id`: entero, obligatorio, referencia al `Customer` propietario.
- `country`: str no vacío, 1–100 caracteres.
- `state`: str no vacío, 1–100 caracteres.
- `city`: str no vacío, 1–100 caracteres.
- `postal_code`: str no vacío, 1–20 caracteres (expuesto como `postalcode`
  en la API — ver supuesto #3).
- `address_line`: str no vacío, 1–255 caracteres (expuesto como `address`
  en la API — ver supuesto #2).
- `created_at` / `updated_at`: gestionados por infraestructura.
- `deleted_at`: nulo mientras la dirección esté activa; se setea en soft
  delete.

### Tabla `addresses` (PostgreSQL, vía SQLAlchemy 2.0 + Alembic)

```sql
CREATE TABLE addresses (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    country VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    address_line VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX ix_addresses_customer_id ON addresses (customer_id);
CREATE INDEX ix_addresses_deleted_at ON addresses (deleted_at);
```

- No hay constraint `UNIQUE` (a diferencia de `email` en `Customer`): el
  spec no pide unicidad de ningún campo de `Address`.
- `updated_at` se actualiza desde el repositorio en cada `UPDATE`/soft
  delete, igual que en `Customer` (sin triggers de DB).
- Migración `migrations/versions/0002_create_addresses_table.py`
  (Alembic, encadenada como `down_revision` a la migración `0001` de
  `customers`) crea la tabla anterior.

## 4. Diseño de endpoints

Blueprint nuevo `addresses_blueprint`, prefijo
`/customers/<int:customer_id>/addresses`. Mismo formato homogéneo de error
que `Customer`: `{"error": "<mensaje>"}` (+ `"details"` en validaciones),
sin exponer stacktraces.

En **todos** los endpoints, el primer paso es resolver el customer padre
con `CustomerRepository.get_by_id(customer_id)` (excluye soft-deleted por
defecto); si es `None` → `CustomerNotFoundError` → `404
{"error": "customer not found"}` (reutilizando el manejador ya existente).

### POST /customers/:id/addresses
- Requiere customer padre activo (si no, `404`).
- Valida body JSON: `country`, `state`, `city`, `postalcode`, `address`
  requeridos, con las reglas de la sección 3. El campo `id` del body, si
  viene, se ignora (supuesto #4).
- Casos de error:
  - JSON ausente/malformado → `400 {"error": "validation failed", "details": {"body": "invalid or missing JSON body"}}`
  - Campo faltante o inválido → `400` con detalle por campo
  - Customer padre no encontrado/soft-deleted → `404`
  - Falla inesperada de DB → `500` genérico
- Éxito → `201` con `{"id","country","state","city","postalcode","address"}`.

### GET /customers/:id/addresses
- Requiere customer padre activo (si no, `404`).
- Excluye direcciones con `deleted_at != NULL`.
- Éxito → `200` con lista (posiblemente vacía).
- Falla inesperada de DB → `500`.

### GET /customers/:id/addresses/:id
- Rutas con convertidores `<int:customer_id>` / `<int:address_id>` (si no
  son enteros, Werkzeug devuelve `404` automáticamente).
- Customer padre no encontrado/soft-deleted → `404`.
- Dirección no encontrada, soft-deleted, o perteneciente a **otro**
  customer → `404 {"error": "address not found"}` (el repositorio filtra
  siempre por `customer_id`, así que una dirección de otro customer nunca
  es visible aquí, evitando fuga de datos entre customers).
- Éxito → `200`.
- Falla inesperada de DB → `500`.

### PATCH /customers/:id/addresses/:id
- Requiere customer padre activo (si no, `404`).
- Body JSON con cualquier subconjunto de `country`, `state`, `city`,
  `postalcode`, `address`. Si `id` viene en el body y difiere del `:id` de
  la dirección en la URL → `400`.
- Si no hay campos válidos para actualizar → `400 {"error": "validation failed", "details": {"body": "no fields to update"}}`.
- Cada campo enviado se valida con las mismas reglas del POST.
- Dirección no encontrada / soft-deleted / de otro customer → `404`.
- Éxito → `200` con el recurso actualizado.
- Falla inesperada de DB → `500`.

### DELETE /customers/:id/addresses/:id
- Requiere customer padre activo (si no, `404`).
- Dirección no encontrada / ya eliminada / de otro customer → `404`.
- Éxito → soft delete, `200` con `{}`.
- Falla inesperada de DB → `500`.

### Manejo de errores (extensión de `error_handlers.py`)
Se agregan, junto a los handlers ya existentes de `Customer`:
- `AddressValidationError` → `400`
- `AddressNotFoundError` / `AddressAlreadyDeletedError` → `404 {"error": "address not found"}`

No se modifica el mapeo existente de `CustomerNotFoundError` (`404
{"error": "customer not found"}`), que ya cubre el caso del customer padre
en las rutas de `Address`. El handler genérico `Exception` → `500` (con
`logging.exception`) sigue aplicando sin cambios.

## 5. Plan de pruebas (Pytest, patrón AAA)

### Unitarias (sin Flask, sin DB real)
- `tests/unit/domain/test_address_entity.py`: construcción válida; cada
  campo vacío/fuera de longitud → `AddressValidationError`; `mark_deleted`
  dos veces → `AddressAlreadyDeletedError`.
- `tests/unit/application/fakes/in_memory_address_repository.py`: doble de
  prueba de `AddressRepository`, filtrando siempre por `customer_id` (para
  poder testear el aislamiento entre customers también a nivel de caso de
  uso).
- Los tests de casos de uso combinan el fake de `Address` con el fake ya
  existente `InMemoryCustomerRepository` (reutilizado tal cual, sin
  cambios) para construir el escenario "customer activo" / "customer no
  encontrado" / "customer soft-deleted".
- Un archivo de test por caso de uso, cubriendo: camino feliz, customer
  padre inexistente, customer padre soft-deleted, dirección no encontrada,
  dirección de otro customer, validación por campo, sin campos para
  actualizar (`PATCH`), `id` de body no coincide con `id` de URL
  (`PATCH`), doble delete.

### Integración (Flask test client + PostgreSQL real, `db_test`)
- `tests/integration/conftest.py` se extiende (no se reemplaza):
  - `clean_db` trunca también la tabla `addresses` (además de `customers`,
    ya sea con `TRUNCATE customers, addresses RESTART IDENTITY CASCADE` o
    truncando ambas en el orden correcto).
  - Nueva fixture `create_address(client, customer_id, **overrides)` que
    hace `POST /customers/{customer_id}/addresses` con un payload por
    defecto válido, análoga a la fixture `create_customer` ya existente.
- Un archivo de test por endpoint, cubriendo: éxito, cada validación de
  entrada, `404` por customer padre inexistente/soft-deleted, `404` por
  dirección inexistente/soft-deleted/de otro customer, y al menos un caso
  `5xx` simulando fallo de repositorio vía `monkeypatch` sobre
  `SQLAlchemyAddressRepository` (mismo patrón que
  `test_customers_api_delete.py`), verificando que no se filtran detalles
  internos.
- Caso explícito de aislamiento: crear dos customers, una dirección para
  cada uno, y verificar que `GET /customers/{A}/addresses/{id_de_B}`
  devuelve `404` (no `200` con datos de otro customer).
- Cobertura objetivo: se mantiene el mismo comando/umbral ya usado
  (`pytest --cov=src/customers --cov-report=term-missing
  --cov-fail-under=85`), evaluado sobre el proyecto completo (`Customer` +
  `Address`).

## 6. Migraciones y Docker

- Nueva migración Alembic `0002_create_addresses_table.py`, generada con
  `down_revision` apuntando a la revisión de `0001_create_customers_table`
  (encadenamiento correcto del historial de esquema).
- No se requieren cambios en `Dockerfile` ni en `docker-compose.yml`: el
  servicio `migrate` ya ejecuta `alembic upgrade head`, que recogerá
  automáticamente la nueva migración; los servicios `db`/`db_test`/`api`
  no cambian.
- Tras `docker compose up -d`, validar manualmente con `curl` los 5
  endpoints de `Address` contra un customer real creado previamente
  (smoke test, igual que se hizo para `Customer`).

## 7. Orden recomendado de implementación

1. **Fase 0 — Confirmación**: validar con el usuario los puntos #3
   (`postalcode` vs `postal_code`) y #11 (`ON DELETE CASCADE`) de la
   sección 0; el resto de supuestos se asumen salvo objeción. —
   **completada** (ver sección 0).
2. **Fase 1 — Dominio**: entidad `Address`, excepciones nuevas en
   `exceptions.py`, puerto `AddressRepository`. Pruebas unitarias de
   entidad.
3. **Fase 2 — Aplicación**: DTOs y los 5 casos de uso, con
   `InMemoryAddressRepository` fake y reutilización de
   `InMemoryCustomerRepository` existente; pruebas unitarias (TDD).
4. **Fase 3 — Persistencia**: `AddressModel`, `AddressMapper`,
   `SQLAlchemyAddressRepository`, migración `0002`. Exportar el nuevo
   repositorio en `infrastructure/persistence/repositories/__init__.py`.
5. **Fase 4 — Web**: `address_schema.py` (con el mapeo
   `postalcode`↔`postal_code` y `address`↔`address_line`),
   `addresses_blueprint.py`, registrar el blueprint en `app.py`, extender
   `error_handlers.py`.
6. **Fase 5 — Verificación con Docker**: `docker compose up`, confirmar
   que `alembic upgrade head` crea `addresses`, smoke test manual con
   `curl` de los 5 endpoints (incluyendo el caso de aislamiento entre
   customers).
7. **Fase 6 — Pruebas de integración**: extender `conftest.py`, escribir
   los 5 archivos de test contra `db_test`, medir cobertura conjunta.
8. **Fase 7 — Calidad**: `ruff check`, `ruff format --check` sobre los
   archivos nuevos/modificados, revisión manual de seguridad (sin SQL
   crudo con interpolación, sin secretos), actualizar `README.md` con los
   nuevos endpoints.

## 8. Riesgos y dependencias

- **Puntos #3 y #11 sin confirmar**: son los dos únicos supuestos con
  impacto en el contrato público (nombre de campo JSON) o en el esquema de
  BD (comportamiento de `ON DELETE`) que conviene cerrar antes de escribir
  la migración y los schemas, para evitar rework.
- **Doble dependencia de repositorio en los casos de uso**: cada caso de
  uso de `Address` depende de `CustomerRepository` + `AddressRepository`;
  si en el futuro se necesita una regla de negocio compartida más compleja
  (p. ej. límite máximo de direcciones por customer), convendría evaluar
  extraerla a un servicio de dominio en vez de duplicarla en cada caso de
  uso — no es necesario para el alcance actual.
- **Blueprint con `url_prefix` dinámico**: depende de que Flask/Werkzeug
  resuelvan correctamente el convertidor `<int:customer_id>` dentro del
  `url_prefix` del blueprint (comportamiento soportado, pero es la primera
  vez que se usa en este proyecto); se valida explícitamente con un test
  de integración y con el smoke test de Docker.
- **Aislamiento entre customers**: riesgo funcional principal si el
  repositorio no filtra correctamente por `customer_id` en `get_by_id` —
  se cubre con un test de integración dedicado (sección 5).
- **Pruebas de integración requieren Postgres real**: mismo riesgo ya
  documentado para `Customer` (`docker compose up -d db_test` como
  prerrequisito).
- **No se introducen dependencias nuevas**: se reutiliza el stack ya
  confirmado para `Customer`; si durante la implementación surge la
  necesidad de alguna librería adicional, se marcará como decisión abierta
  antes de instalarla, igual que en el feature anterior.
