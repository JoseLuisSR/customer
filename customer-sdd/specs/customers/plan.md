# Especificación técnica — Gestión de clientes y direcciones

> Traduce a decisiones de implementación la especificación funcional
> `specs/customers/spec.md` (`API-CUSTOMERS-001`, v0.1.0, estado
> Borrador). Este documento es el paso 3 del flujo de trabajo (diseño
> técnico) y precede al plan de implementación (`task/*.md`).

---

## 0. Metadatos

- **Referencia funcional:** `API-CUSTOMERS-001` v0.1.0 (`specs/customers/spec.md`)
- **Estado de este documento:** Borrador técnico — pendiente de validación por el responsable funcional en los puntos marcados como supuesto (sección 7). Q-001 ya fue confirmada por negocio (2026-07-25, ver 7.1); las demás (Q-002 a Q-006) siguen siendo supuestos de ingeniería pendientes de validación
- **Stack:** Python 3.13, Flask, SQLAlchemy 2.x, PostgreSQL, Alembic, Pytest, Ruff, MyPy, UV, Docker
- **Arquitectura:** Hexagonal (dominio / aplicación / infraestructura), API Design First

### Resumen rápido de decisiones sobre preguntas abiertas

| ID | Pregunta | Decisión adoptada para v0.1.0 |
|---|---|---|
| Q-001 | ¿Identificación única? | **Confirmada por negocio (2026-07-25): sí, debe ser única.** Constraint `UNIQUE` en BD, igual tratamiento que `email` salvo normalización. Ver 7.1 |
| Q-002 | ¿Límites de edad? | `age >= 0` (obligatorio, del spec) y `age <= 120` como cota de sanidad. Ver 7.2 |
| Q-003 | ¿Estados funcionales posibles? | Modelo mínimo de 2 estados: `ACTIVE`, `DELETED`. Ver 7.3 |
| Q-004 | ¿Borrado lógico o físico? | Borrado lógico (soft delete) vía `status`. Ver 7.4 |
| Q-005 | ¿`postal_code` obligatorio en todos los países? | Se respeta el spec literal (obligatorio siempre). Ver 7.5 |
| Q-006 | ¿Paginación/filtros/orden en el listado? | Paginación simple (page/page_size); sin filtros ni orden en v0.1.0. Ver 7.6 |

Todas se detallan con su justificación completa en la sección 7.

---

## 1. Modelo de datos

### 1.1 Decisiones transversales

- **Identificadores:** `UUID` (v4) generados en la capa de dominio al construir la entidad (no `SERIAL`/`IDENTITY`). Motivo: permite asignar el id antes del `commit`, desacopla el dominio de la base de datos y evita depender de extensiones de Postgres para generación de UUID en servidor.
- **Normalización de email:** el value object `Email` normaliza (`trim` + `lower`) en el momento de construcción. Se persiste **un único** valor ya normalizado en la columna `email`; no se conserva el casing original tal como lo escribió el usuario. Esto resuelve directamente los casos límite de la sección 16 del spec ("correo con mayúsculas/minúsculas", "espacios antes o después").
- **Normalización de identification:** el value object `Identification` normaliza únicamente `trim` (sin `lower`) antes de persistir. Motivo: la unicidad de `identification` fue confirmada por negocio (Q-001, 7.1), pero a diferencia de `email` el spec funcional no menciona un caso límite de "identificación con diferencias de mayúsculas/minúsculas", y muchos documentos de identificación reales son alfanuméricos donde el casing puede ser significativo (p. ej. formatos con letras de verificación). Aplicar `trim` sí es necesario para que la constraint `UNIQUE` no pueda evadirse trivialmente con espacios en blanco. Si negocio confirma que la comparación también debe ser insensible a mayúsculas/minúsculas, se ajusta el value object para añadir `lower()` sin cambios de esquema.
- **Estados (`status`):** `VARCHAR` + `CHECK (status IN ('ACTIVE','DELETED'))` en lugar de `ENUM` nativo de Postgres, para simplificar migraciones futuras si el negocio amplía el catálogo de estados (ver 7.3). Ver justificación en 7.3/7.4.
- **Auditoría técnica:** se agregan `created_at` y `updated_at` (`TIMESTAMPTZ`, `server_default=now()`) en ambas tablas. Es una convención de ingeniería estándar para depuración en producción, no una funcionalidad de "historial de cambios" (que sigue fuera de alcance); no se expone ningún endpoint de auditoría ni versión de la entidad.
- **Borrado lógico:** ninguna operación de "eliminar" hace `DELETE` físico en el flujo normal de la API; actualiza `status = 'DELETED'`. Las lecturas (`GET`, listados, validaciones de existencia) filtran por defecto `status <> 'DELETED'`, de modo que una entidad eliminada se comporta como "no encontrada" ante nuevas operaciones (`ERR-003`/`ERR-004`), cubriendo el caso límite "actualización o eliminación repetida de una entidad ya eliminada".

### 1.2 Tabla `customers`

| Columna | Tipo | Constraints | Notas |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY` | Generado en dominio (uuid4) |
| `name` | `VARCHAR(255)` | `NOT NULL`, `CHECK (btrim(name) <> '')` | VAL-003 |
| `identification` | `VARCHAR(64)` | `NOT NULL`, `UNIQUE` (índice `ux_customers_identification`), `CHECK (btrim(identification) <> '')` | VAL-004 + unicidad confirmada por negocio (Q-001, 7.1). Normalizada solo con `trim` (sin `lower`) antes de persistir, ver 1.1 |
| `age` | `SMALLINT` | `NOT NULL`, `CHECK (age >= 0 AND age <= 120)` | VAL-005 + cota de sanidad (Q-002, 7.2) |
| `email` | `VARCHAR(320)` | `NOT NULL`, `UNIQUE` (índice `ux_customers_email`) | Ya normalizado (trim+lower) antes de persistir. VAL-001/VAL-002/RN-001 |
| `status` | `VARCHAR(16)` | `NOT NULL DEFAULT 'ACTIVE'`, `CHECK (status IN ('ACTIVE','DELETED'))` | Q-003/Q-004 |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Técnico |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Técnico, actualizado por la aplicación en cada `UPDATE` |

Índices:
- `ux_customers_email` (único, ya cubre VAL-002)
- `ux_customers_identification` (único — Q-001 confirmada por negocio, ver 7.1 y 2.4)
- `ix_customers_status` (para filtrar activos eficientemente en listados)

### 1.3 Tabla `addresses`

| Columna | Tipo | Constraints | Notas |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY` | Generado en dominio |
| `customer_id` | `UUID` | `NOT NULL`, `FOREIGN KEY -> customers.id ON DELETE CASCADE` | RN-005. `CASCADE` es una salvaguarda defensiva (el flujo normal no hace `DELETE` físico; ver 7.4) |
| `country` | `VARCHAR(100)` | `NOT NULL`, `CHECK (btrim(country) <> '')` | VAL-009 |
| `state` | `VARCHAR(100)` | `NOT NULL`, `CHECK (btrim(state) <> '')` | VAL-009 |
| `city` | `VARCHAR(100)` | `NOT NULL`, `CHECK (btrim(city) <> '')` | VAL-009 |
| `address` | `VARCHAR(255)` | `NOT NULL`, `CHECK (btrim(address) <> '')` | VAL-009 |
| `postal_code` | `VARCHAR(20)` | `NOT NULL`, `CHECK (btrim(postal_code) <> '')` | VAL-009. Obligatorio para todos los países (Q-005, 7.5) |
| `status` | `VARCHAR(16)` | `NOT NULL DEFAULT 'ACTIVE'`, `CHECK (status IN ('ACTIVE','DELETED'))` | Q-003/Q-004 |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Técnico |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Técnico |

Índices:
- `ix_addresses_customer_id`
- `ix_addresses_customer_id_status` (compuesto, soporta el conteo de "máximo 5 direcciones activas" y el listado por cliente)

### 1.4 Regla RN-003 (máximo 5 direcciones) y concurrencia

No existe una forma declarativa simple en Postgres (sin trigger) para limitar el conteo de filas por FK. Decisión:

- **Invariante de dominio:** el agregado `Customer` expone `add_address(...)` que lanza `MaxAddressesExceededError` si ya tiene 5 direcciones activas cargadas.
- **Protección de concurrencia (caso límite "solicitudes simultáneas"):** el caso de uso `CreateAddress` toma un bloqueo pesimista (`SELECT ... FOR UPDATE`) sobre la fila del `customer` antes de contar direcciones activas e insertar. Esto evita condiciones de carrera entre dos altas simultáneas que individualmente pasarían la validación de dominio pero en conjunto superarían el límite.
- **RN-001 (email único) bajo concurrencia:** se resuelve por el `UNIQUE` de base de datos, que es atómico; la aplicación captura la violación de constraint y la traduce a `ERR-002`. No se requiere bloqueo adicional.
- **Unicidad de `identification` bajo concurrencia (Q-001 confirmada):** mismo tratamiento que el email — el `UNIQUE` de base de datos (`ux_customers_identification`) es atómico y suficiente; la aplicación captura la violación de constraint y la traduce al código de error definido en 2.4 (`ERR-008`, propuesto). No se requiere bloqueo pesimista adicional porque, igual que con el email, la garantía de atomicidad la da la base de datos y no depende de una lectura previa seguida de una escritura separada.

### 1.5 Diagrama relacional (conceptual)

```
customers (1) ──< (0..5 activas) addresses
customers.id  <──FK── addresses.customer_id
```

---

## 2. Contrato de API

### 2.1 Convenciones generales

- Base path versionado: `/api/v1`
- Formato: JSON (`Content-Type: application/json`)
- Todas las respuestas —éxito o error— usan el **sobre de resultado funcional** (RN-006, sección 10.3 del spec):

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

- `entity_status` refleja el `status` de la entidad afectada tras la operación (p. ej. `ACTIVE` tras crear/actualizar, `DELETED` tras eliminar). Es `null` cuando no aplica a una única entidad (listados) o cuando la operación fue rechazada antes de identificar una entidad concreta.
- **Decisión de diseño — `DELETE` devuelve `200 OK` con cuerpo, no `204 No Content`:** el spec exige el sobre de resultado "en todas las respuestas" (sección 18, supuestos). `204` no admite cuerpo, por lo que se usa `200` con el sobre confirmando `entity_status: "DELETED"`.
- `errors` es un arreglo de objetos `{ "code": "VAL-00X" | "ERR-00X", "field": "string | null", "message": "string" }`, para trazabilidad directa con las tablas de validaciones/errores del spec funcional.

### 2.2 Endpoints — Customer

| Método | Ruta | RF | Éxito | Body request |
|---|---|---|---|---|
| `POST` | `/api/v1/customers` | RF-001 | `201 Created` | `CustomerCreateRequest` |
| `GET` | `/api/v1/customers/{customer_id}` | RF-002 | `200 OK` | — |
| `GET` | `/api/v1/customers?page=&page_size=` | RF-003 | `200 OK` | — (query params, ver 7.6) |
| `PUT` | `/api/v1/customers/{customer_id}` | RF-004 | `200 OK` | `CustomerUpdateRequest` |
| `DELETE` | `/api/v1/customers/{customer_id}` | RF-005 | `200 OK` | — |

**Decisión — `PUT` (reemplazo completo) en vez de `PATCH`:** RN-002 exige que todo cliente tenga siempre `name`, `identification`, `age`, `email`; al ser todos obligatorios de forma permanente, un reemplazo completo evita la ambigüedad semántica de un `PATCH` parcial con campos opcionales. El payload de actualización **no** acepta `addresses` (esa colección se gestiona exclusivamente vía los endpoints de `Address`), para no duplicar la fuente de verdad de la relación 1:N.

`CustomerCreateRequest`:
```json
{
  "name": "string",
  "identification": "string",
  "age": 0,
  "email": "string",
  "addresses": [
    { "country": "string", "state": "string", "city": "string", "address": "string", "postal_code": "string" }
  ]
}
```
`addresses` es opcional (0 a 5 elementos); si excede 5, se rechaza con `ERR-005` antes de crear nada (operación atómica).

`CustomerUpdateRequest`:
```json
{ "name": "string", "identification": "string", "age": 0, "email": "string" }
```

`CustomerResponse` (usado en `data`):
```json
{
  "id": "uuid",
  "name": "string",
  "identification": "string",
  "age": 0,
  "email": "string",
  "status": "ACTIVE",
  "addresses": [ /* AddressResponse[] */ ],
  "created_at": "2026-07-25T00:00:00Z",
  "updated_at": "2026-07-25T00:00:00Z"
}
```

Listado (RF-003), `data`:
```json
{
  "items": [ /* CustomerResponse[] sin addresses embebidas, ver nota */ ],
  "page": 1,
  "page_size": 20,
  "total": 42
}
```
Nota: para el listado se omite el arreglo `addresses` embebido por cliente (evita N+1 y payloads grandes); se puede obtener el detalle completo vía `GET /customers/{id}`. Se documenta como decisión técnica, no como restricción funcional.

### 2.3 Endpoints — Address

| Método | Ruta | RF | Éxito | Body request |
|---|---|---|---|---|
| `POST` | `/api/v1/customers/{customer_id}/addresses` | RF-006 | `201 Created` | `AddressRequest` |
| `GET` | `/api/v1/customers/{customer_id}/addresses` | RF-007 | `200 OK` | — |
| `PUT` | `/api/v1/customers/{customer_id}/addresses/{address_id}` | RF-008 | `200 OK` | `AddressRequest` |
| `DELETE` | `/api/v1/customers/{customer_id}/addresses/{address_id}` | RF-009 | `200 OK` | — |

`AddressRequest`:
```json
{ "country": "string", "state": "string", "city": "string", "address": "string", "postal_code": "string" }
```

`AddressResponse`:
```json
{
  "id": "uuid",
  "customer_id": "uuid",
  "country": "string", "state": "string", "city": "string",
  "address": "string", "postal_code": "string",
  "status": "ACTIVE",
  "created_at": "2026-07-25T00:00:00Z",
  "updated_at": "2026-07-25T00:00:00Z"
}
```

### 2.4 Mapeo de errores funcionales a HTTP

| Código funcional | Situación | HTTP | `success` | Notas |
|---|---|---|---|---|
| ERR-001 | Datos obligatorios inválidos/ausentes (VAL-001, VAL-003, VAL-004, VAL-005, VAL-009) | `400 Bad Request` | `false` | `errors[]` con un elemento por campo inválido |
| ERR-002 | Correo duplicado (VAL-002) | `409 Conflict` | `false` | Al actualizar, se excluye al propio cliente de la verificación (ver 2.5) |
| ERR-003 | Cliente inexistente (VAL-006) | `404 Not Found` | `false` | Incluye clientes con `status = DELETED` |
| ERR-004 | Dirección inexistente (VAL-010) | `404 Not Found` | `false` | Incluye direcciones con `status = DELETED` |
| ERR-005 | Máximo de direcciones alcanzado (VAL-007) | `409 Conflict` | `false` | Conteo sobre direcciones `ACTIVE` |
| ERR-006 | Dirección no pertenece al cliente indicado (VAL-008) | `404 Not Found` | `false` | Se usa `404` (no `403`) para no revelar la existencia del recurso bajo otro cliente — semántica REST de colección anidada |
| ERR-007 | Error no controlado | `500 Internal Server Error` | `false` | Mensaje genérico al cliente; detalle completo solo en logs (sección 3.3) |
| **ERR-008** (propuesto, ver nota) | Identificación duplicada (VAL-011, propuesta) | `409 Conflict` | `false` | Al actualizar, se excluye al propio cliente de la verificación (ver 2.5). Análogo a `ERR-002`/`VAL-002` pero para `identification` |

**⚠️ Nota — discrepancia con el spec funcional (`specs/customers/spec.md` v0.1.0):** Q-001 ya fue respondida por el responsable funcional ("la identificación debe ser única", confirmado 2026-07-25), pero el spec funcional v0.1.0 **todavía no documenta** esta regla como validación (`VAL-0XX`) ni como código de error (`ERR-0XX`) — solo existe `VAL-002`/`ERR-002` para el correo, y `Q-001` sigue listada como "Abierta" en la sección 20 del documento funcional. Esta sección técnica queda desactualizada respecto del propio flujo si el spec funcional no se corrige.

Se evaluaron dos alternativas técnicas:
1. **Reutilizar `ERR-002`/`VAL-002`** ampliando su alcance a "correo o identificación duplicados". Se descarta: el mensaje funcional de `ERR-002` ("Ya existe un cliente con el correo indicado") es específico de correo, y el campo `field` del objeto de error necesita distinguir cuál de los dos campos duplicados causó el rechazo (importante para que el consumidor resalte el campo correcto en un formulario). Sobrecargar un código para dos campos distintos rompe la trazabilidad 1:1 código-de-error ↔ regla de negocio que sigue el resto del documento.
2. **Introducir un código nuevo `ERR-008` (y `VAL-011`)**, análogo a `ERR-002`/`VAL-002` pero para `identification`, manteniendo la trazabilidad 1:1. **Es la opción adoptada.**

Estos códigos (`VAL-011`, `ERR-008`) son una **anticipación técnica, no códigos ya aprobados en el spec funcional**. Antes de implementar, el spec funcional (`specs/customers/spec.md`) debería actualizarse en su próxima revisión para: (a) mover Q-001 de "Abierta" a resuelta en la sección 20, (b) agregar una regla de negocio equivalente a RN-001 pero para `identification` (o ampliar la redacción de RN-001) en la sección 9, (c) agregar `VAL-011` a la sección 11, y (d) agregar `ERR-008` con su mensaje funcional a la sección 13. Esta tarea no incluye modificar `specs/customers/spec.md`; se deja señalado aquí para que el responsable funcional lo incorpore.

### 2.5 Notas de validación específicas por caso límite del spec (sección 16)

- **Email sin cambios en un update:** la verificación de unicidad de `Email` en `UpdateCustomer` excluye el propio `customer_id` (`WHERE email = :email AND id <> :customer_id`), evitando falso `ERR-002`.
- **Identification sin cambios en un update (Q-001 confirmada):** mismo tratamiento que el email — la verificación de unicidad de `Identification` en `UpdateCustomer` excluye el propio `customer_id` (`WHERE identification = :identification AND id <> :customer_id`), evitando un falso `ERR-008` cuando el cliente reenvía su propia identificación sin cambios.
- **Edad 0:** válida (`age >= 0`). **Edad negativa:** `ERR-001`.
- **Dirección con campos vacíos:** `ERR-001` con un `errors[]` por cada campo vacío detectado (no solo el primero), para reducir ida y vuelta del consumidor.
- **Creación de cliente con 6 direcciones en el mismo payload:** se rechaza toda la operación (`ERR-005`), sin crear el cliente ni ninguna dirección (atomicidad de la transacción).

---

## 3. Validaciones y su ubicación en la arquitectura

| Validación | Capa | Mecanismo |
|---|---|---|
| Formato de email (VAL-001), normalización | Dominio | Value object `Email` (regex simplificado RFC 5322 + `trim`/`lower` en el constructor) |
| Nombre/identificación no vacíos (VAL-003, VAL-004) | Dominio | Value objects `Name`, `Identification` (rechazan cadena vacía tras `trim`) |
| Edad entera no negativa y cota de sanidad (VAL-005) | Dominio | Value object `Age` |
| Campos obligatorios de dirección no vacíos (VAL-009) | Dominio | Value object por campo o validación en el constructor de `Address` |
| Máximo 5 direcciones (VAL-007) | Dominio (invariante del agregado) + Aplicación (bloqueo de concurrencia, ver 1.4) | `Customer.add_address()` |
| Unicidad de email (VAL-002) | Aplicación (consulta al repositorio) + Infraestructura (constraint `UNIQUE` como red de seguridad) | Casos de uso `CreateCustomer`/`UpdateCustomer` vía puerto `CustomerRepository` |
| Unicidad de identification (VAL-011, propuesta — ver nota en 2.4) | Aplicación (consulta al repositorio) + Infraestructura (constraint `UNIQUE` como red de seguridad) | Casos de uso `CreateCustomer`/`UpdateCustomer` vía puerto `CustomerRepository`, análogo a la unicidad de email (Q-001 confirmada, 7.1) |
| Existencia de cliente/dirección (VAL-006, VAL-010) | Aplicación | Casos de uso consultan el repositorio y lanzan `CustomerNotFoundError`/`AddressNotFoundError` |
| Pertenencia dirección-cliente (VAL-008) | Aplicación | Casos de uso `UpdateAddress`/`DeleteAddress` verifican `address.customer_id == customer_id` |
| Forma/tipo del JSON de entrada (tipos, campos requeridos presentes en el payload) | Infraestructura (HTTP) | Parseo manual de request → DTO en `infrastructure/http/schemas.py`; errores de parseo se traducen a `ERR-001` antes de llegar a la capa de aplicación |

**Nota sobre dependencias de validación:** se implementa el parseo/validación de payloads con Python puro (sin `pydantic` ni `marshmallow`), ya que el stack declarado no los incluye y no se quiere introducir una dependencia no solicitada. Si en el futuro se requiere un esquema más complejo, se debe evaluar explícitamente con el usuario antes de añadir la dependencia.

Las excepciones de dominio/aplicación se capturan en un manejador de errores centralizado de Flask (`infrastructure/http/error_handlers.py`) que las traduce al sobre de resultado y código HTTP de la tabla 2.4.

---

## 4. Estructura de carpetas propuesta (hexagonal)

```
customers/
├── pyproject.toml
├── main.py                              # entrypoint (arranca la app Flask vía factory)
├── src/
│   └── customers/
│       ├── __init__.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── shared/
│       │   │   └── result.py            # (si se requieren tipos compartidos)
│       │   ├── customer/
│       │   │   ├── entities.py          # Customer (aggregate root)
│       │   │   ├── value_objects.py     # Email, Age, Name, Identification, CustomerId
│       │   │   ├── exceptions.py        # DuplicateEmailError, DuplicateIdentificationError, MaxAddressesExceededError, CustomerNotFoundError...
│       │   │   └── repository.py        # Puerto: CustomerRepository (Protocol/ABC)
│       │   └── address/
│       │       ├── entities.py          # Address
│       │       ├── value_objects.py
│       │       ├── exceptions.py        # AddressNotFoundError, AddressCustomerMismatchError
│       │       └── repository.py        # Puerto: AddressRepository
│       ├── application/
│       │   ├── __init__.py
│       │   ├── operation_result.py      # DTO del sobre de resultado (RN-006)
│       │   ├── customer/
│       │   │   ├── create_customer.py
│       │   │   ├── get_customer.py
│       │   │   ├── list_customers.py
│       │   │   ├── update_customer.py
│       │   │   └── delete_customer.py
│       │   └── address/
│       │       ├── create_address.py
│       │       ├── list_addresses.py
│       │       ├── update_address.py
│       │       └── delete_address.py
│       └── infrastructure/
│           ├── __init__.py
│           ├── config.py                # Config desde variables de entorno
│           ├── logging_config.py
│           ├── flask_app.py             # Application factory (create_app)
│           ├── http/
│           │   ├── customer_routes.py   # Blueprint /customers
│           │   ├── address_routes.py    # Blueprint /customers/<id>/addresses
│           │   ├── schemas.py           # Parseo/validación de payloads JSON -> DTOs
│           │   ├── error_handlers.py    # Excepciones -> sobre + status HTTP
│           │   └── response_envelope.py # Construcción del sobre de resultado
│           └── persistence/
│               ├── db.py                # engine, session factory (scoped_session)
│               ├── models.py            # CustomerModel, AddressModel (SQLAlchemy ORM)
│               ├── customer_repository.py  # Adaptador de CustomerRepository
│               └── address_repository.py   # Adaptador de AddressRepository
├── migrations/                          # Alembic
│   ├── env.py
│   └── versions/
├── alembic.ini
└── tests/
    ├── unit/
    │   ├── domain/
    │   └── application/
    └── integration/
        ├── persistence/
        └── http/
```

Justificación: separa puertos (`domain/*/repository.py`) de adaptadores (`infrastructure/persistence/*_repository.py`), evita que Flask/SQLAlchemy se filtren al dominio, y permite testear casos de uso con repositorios en memoria sin base de datos.

---

## 5. Estrategia de migraciones y despliegue

### 5.1 Migraciones (Alembic)

- Alembic configurado con `sqlalchemy.url` leído de `DATABASE_URL` (variable de entorno), nunca hardcodeado.
- Migración inicial (`0001_create_customers_and_addresses.py`) crea ambas tablas, constraints `CHECK`, `UNIQUE`, `FOREIGN KEY` e índices descritos en la sección 1.
- Se usa `alembic revision --autogenerate` a partir de `models.py` como punto de partida, pero cada migración autogenerada se revisa manualmente antes de aplicarse (los `CHECK` con `btrim()` no siempre se autogeneran correctamente).
- Convención de nombres: `NNNN_descripcion_snake_case.py`.

### 5.2 Despliegue (consideraciones básicas)

- Imagen Docker basada en `python:3.13-slim`, gestionada con `uv` (`uv sync --frozen`) para reproducibilidad.
- `docker-compose.yml` con dos servicios como mínimo: `db` (Postgres) y `api` (Flask vía `gunicorn`), más un `entrypoint` que ejecuta `alembic upgrade head` antes de levantar el servidor.
- Variables de entorno mínimas: `DATABASE_URL`, `FLASK_ENV`, `LOG_LEVEL`.
- No se incluye configuración de autenticación/autorización ni gateway, dado que está explícitamente fuera de alcance funcional (sección 4.2 del spec); solo se deja el punto de extensión (middleware/decorador) documentado para cuando el negocio lo defina.

---

## 6. Estrategia de pruebas

### 6.1 Pruebas unitarias (sin base de datos, sin Flask)

- **Dominio:** value objects (`Email` normaliza y valida formato; `Age` rechaza negativos y valores fuera de cota; `Name`/`Identification` rechazan vacíos tras `trim`), invariante de `Customer.add_address` (rechaza la 6ª dirección), invariante de no permitir `Address` sin `customer_id`.
- **Aplicación:** cada caso de uso probado con implementaciones *fake* en memoria de `CustomerRepository`/`AddressRepository` (sin mocks de infraestructura real), cubriendo: creación exitosa, email duplicado, identificación duplicada (Q-001 confirmada), cliente inexistente, dirección ajena a otro cliente, límite de 5 direcciones, actualización de email sin cambios (no debe disparar falso duplicado), actualización de identificación sin cambios (no debe disparar falso duplicado), eliminación con direcciones asociadas (deben quedar `DELETED`, no huérfanas).

### 6.2 Pruebas de integración (con Postgres real)

- **Repositorios (`infrastructure/persistence`):** contra una base Postgres real (vía `docker-compose` de pruebas), verificando que los `CHECK`/`UNIQUE`/`FOREIGN KEY` de la sección 1 actúan como red de seguridad y que el filtrado por `status <> 'DELETED'` funciona.
- **HTTP end-to-end:** cliente de pruebas de Flask contra la app completa + Postgres real, cubriendo los escenarios 1–7 y los criterios de aceptación CA-001 a CA-008 del spec funcional, verificando explícitamente el sobre de resultado (`success`, `operation`, `entity`, `entity_status`, `message`, `data`, `errors`) y el código HTTP de la tabla 2.4 para cada `ERR-00X`.
- **Concurrencia (casos límite sección 16):** prueba de integración que dispara dos requests concurrentes de creación de cliente con el mismo email, dos requests concurrentes de creación de cliente con la misma identificación (Q-001 confirmada, ver 1.4), y dos requests concurrentes de creación de la 5ª/6ª dirección, verificando que solo una tiene éxito en cada caso.
- Esquema de base de datos de pruebas: se crea/destruye por sesión de pruebas mediante `Base.metadata.create_all()/drop_all()` para velocidad; se mantiene un test separado que ejecuta `alembic upgrade head` contra una base limpia para validar que las migraciones son consistentes con los modelos ORM.

No se define aquí un porcentaje de cobertura objetivo porque el spec funcional no lo exige y el proyecto aún no tiene configuración de cobertura en `pyproject.toml`; se recomienda acordarlo explícitamente con el usuario antes de la fase de implementación.

---

## 7. Supuestos y decisiones frente a las preguntas abiertas del spec funcional

> Estas decisiones permiten avanzar sin bloquear el trabajo, pero **deben ser validadas por el responsable funcional** antes de pasar el spec funcional a estado "Aprobada". Todas son reversibles con una migración adicional si el negocio decide algo distinto.
>
> **Q-001 es la excepción:** ya no es un supuesto técnico, sino una decisión de negocio confirmada por el responsable funcional (ver 7.1). Se conserva en esta sección por trazabilidad respecto a la numeración original de preguntas abiertas del spec funcional, y porque el spec funcional en sí mismo aún no fue actualizado para reflejar la respuesta (ver nota de discrepancia en 7.1 y 2.4).

### 7.1 Q-001 — ¿La identificación debe ser única? — **Resuelta (decisión de negocio confirmada)**

**Estado:** Ya no es un supuesto técnico ni una pregunta abierta. El responsable funcional confirmó el 2026-07-25 que `identification` debe ser única, con la misma restricción de unicidad que ya aplica a `email` (RN-001), extendida ahora a `identification`.

**Decisión técnica adoptada:** Se implementa constraint `UNIQUE` en base de datos (`ux_customers_identification`) sobre `identification`, con la misma estrategia usada para `email`: validación en la capa de aplicación (casos de uso `CreateCustomer`/`UpdateCustomer`) más el `UNIQUE` de base de datos como red de seguridad ante condiciones de carrera (ver 1.4). A diferencia de `email`, **no** se aplica normalización de casing (`lower()`) a `identification`, solo `trim`: el spec funcional no define un caso límite de "identificación con diferencias de mayúsculas/minúsculas" (sí lo hace explícitamente para el correo, sección 16), y muchos formatos reales de identificación son alfanuméricos donde el casing puede ser significativo. Si negocio confirma en el futuro que la comparación también debe ser insensible a mayúsculas/minúsculas, el ajuste se limita al value object `Identification` sin cambios de esquema.

**Discrepancia pendiente con el spec funcional:** esta decisión ya fue tomada por negocio, pero `specs/customers/spec.md` v0.1.0 no ha sido actualizado para reflejarla — Q-001 sigue figurando como "Abierta" en su sección 20, y no existen `VAL-0XX`/`ERR-0XX` funcionales para la unicidad de `identification` (se documentó la solución técnica provisional `VAL-011`/`ERR-008` en 2.4). Se recomienda que el responsable funcional actualice el spec funcional en su próxima revisión antes de pasarlo a estado "Aprobada". Esta tarea no incluye modificar `specs/customers/spec.md`.

### 7.2 Q-002 — ¿Límites de edad?

**Decisión:** `age >= 0` (obligatorio y explícito en el spec, VAL-005) y `age <= 120` como cota de sanidad técnica, aplicada tanto en el value object de dominio como en `CHECK` de base de datos.
**Motivo:** El spec solo exige "entero no negativo"; el límite superior es una salvaguarda de calidad de datos razonable (evita valores absurdos por error de entrada) y no impone una regla de negocio real (p. ej. edad mínima para contratar). Debe confirmarse con negocio si existe un límite funcional distinto (p. ej. mayoría de edad).

### 7.3 Q-003 — ¿Qué estados funcionales puede tener un cliente o una dirección?

**Decisión:** Modelo mínimo de dos estados: `ACTIVE` y `DELETED`.
**Motivo:** Es el conjunto mínimo que satisface los requisitos explícitos del spec (crear, consultar, actualizar, eliminar) sin inventar estados especulativos (p. ej. `SUSPENDED`, `PENDING_VALIDATION`) que el spec no menciona. Se modela como `VARCHAR` + `CHECK` (no `ENUM` nativo de Postgres) para que ampliar el catálogo en el futuro sea una migración de bajo costo.

### 7.4 Q-004 — ¿La eliminación debe ser lógica o definitiva?

**Decisión:** Eliminación lógica (soft delete) mediante `status = 'DELETED'`.
**Motivo:** El spec ya modela un campo `status` obligatorio para ambas entidades ("debe reflejar el resultado o estado vigente"), lo que encaja naturalmente con un borrado lógico. Es la opción más segura por defecto (reversible, auditable a nivel de estado) y resuelve de forma natural el caso límite "actualización o eliminación repetida de una entidad ya eliminada" (se trata como no encontrada). Si el negocio confirma que debe ser físico, el cambio se limita a la capa de infraestructura (reemplazar `UPDATE status` por `DELETE`) sin tocar dominio ni contrato de API.

### 7.5 Q-005 — ¿El código postal es obligatorio para todos los países?

**Decisión:** Se respeta literalmente la tabla de datos funcionales del spec (sección 10.2), donde `postal_code` está marcado como obligatorio sin excepción por país.
**Motivo:** No introducir una excepción no solicitada. Se deja constancia explícita de que existen países sin sistema de código postal estandarizado, por lo que se recomienda que el responsable funcional confirme si se requiere una excepción antes de pasar a "Aprobada".

### 7.6 Q-006 — ¿La consulta de clientes requiere paginación, filtros u ordenamiento?

**Decisión:** Se implementa paginación simple (`page`, `page_size`, con `page_size` por defecto 20 y máximo 100) en `GET /customers`. No se implementan filtros ni ordenamiento en v0.1.0.
**Motivo:** Sin paginación, un listado sin límite de tamaño es una decisión de diseño riesgosa a nivel de escalabilidad y no una preferencia estética; se considera un requisito técnico implícito de cualquier endpoint de listado en producción, no una funcionalidad de negocio nueva. Filtros y ordenamiento sí son funcionalidad de negocio no solicitada explícitamente, por lo que se excluyen de v0.1.0 y quedan pendientes de definición.

---

## 8. Trazabilidad de esta especificación técnica

| Sección del spec funcional | Sección de este documento |
|---|---|
| 9. Reglas de negocio (RN-001 a RN-006) | 1.1, 1.4, 3 |
| 10. Datos funcionales | 1.2, 1.3, 2.2, 2.3 |
| 11. Validaciones funcionales (VAL-001 a VAL-010) | 3 |
| 13. Manejo funcional de errores (ERR-001 a ERR-007) | 2.4 |
| 16. Casos límite | 1.4, 2.5, 6.2 |
| 20. Preguntas abiertas (Q-001 a Q-006) | 7 |

**Nota de trazabilidad pendiente:** la fila de `VAL-011`/`ERR-008` (unicidad de `identification`, secciones 2.4, 3 y 7.1 de este documento) **no tiene contraparte todavía** en las secciones 9, 11 y 13 del spec funcional v0.1.0, porque Q-001 fue respondida por negocio pero el documento funcional no fue actualizado (ver 7.1). Cuando `specs/customers/spec.md` incorpore la regla de negocio, `VAL-011` y `ERR-008` correspondientes, esta tabla debe actualizarse para reflejar los códigos definitivos que asigne el responsable funcional (pueden no coincidir con los nombres provisionales `VAL-011`/`ERR-008` usados aquí).
