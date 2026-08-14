# Plan de implementación — Feature `Address`

Referencia de patrón: `Customer` (`src/domain/customer.py`,
`src/application/dto/customer_dto.py`,
`src/application/repository/customer_repository.py`,
`src/application/services/customer_service.py`,
`src/exception/customer_exception.py`,
`src/infrastructure/persistence/customer_model.py`,
`src/infrastructure/persistence/database_customer_repository.py`,
`src/infrastructure/web/customer_routes.py`,
`src/infrastructure/web/error_handler.py`).

`Address` es un recurso anidado bajo `Customer`
(`/api/v1/customers/{customer_id}/addresses`), con relación 1-N
(un customer tiene entre 0 y 5 addresses). No se modificará el agregado
`Customer` existente: `Address` se implementa como entidad propia con
`customer_id` como referencia (foreign key), replicando el estilo plano
que ya usa el proyecto (sin patrón "aggregate root" explícito, que
tampoco existe hoy para `Customer`).

No hay suite de tests en el repo (no hay `pytest` en `pyproject.toml`,
no existe carpeta `tests/`; sólo quedan restos de una corrida local en
`.mypy_cache/.../test_database_customer_repository.*`, no versionados).
Tampoco hay `create_all()` ni Alembic — la creación de tablas no está
resuelta ni siquiera para `customers`. Esto se señala como hallazgo,
no se resuelve en este plan salvo que el usuario lo pida.

---

## 0. Ambigüedades y vacíos del spec — DECISIONES CONFIRMADAS

Estos puntos no estaban documentados en el spec y fueron resueltos
explícitamente con el usuario el 2026-08-11. Se listan como decisiones
cerradas, no como asunciones pendientes.

1. **Código de status de `PUT` (upsert). CONFIRMADO:** `200 OK` si
   reemplaza un address existente, `201 Created` si lo crea (semántica
   estándar de upsert). El servicio propaga un flag `created: bool`
   hacia la capa web para decidir el status code.
2. **`id` en el payload de `PUT`. CONFIRMADO:** el `id` de la URL es la
   fuente de verdad. Si el body trae `id`, se ignora silenciosamente
   (sin comparar ni rechazar).
3. **Respuesta de `PUT` sin `id` en el ejemplo del spec. CONFIRMADO:**
   se considera una omisión del spec. `PUT` responde con el mismo shape
   que los demás endpoints, incluyendo `id`. `AddressRsps` es único
   para toda la feature (no se crea un DTO de respuesta distinto para
   `PUT`).
4. **Comportamiento al exceder el máximo de 5 addresses por customer.
   CONFIRMADO:** `409 Conflict` con `MaxAddressesPerCustomerError`.
   Aplica a `POST` y también a `PUT` cuando el upsert termina creando
   un address nuevo (evita usar el upsert como vía para saltarse el
   límite).
5. **`postal-code` con guion en el JSON.** El dominio y la DB usan
   `postal_code` (snake_case). El mapeo a `postal-code` en el JSON
   público se resuelve con `pydantic.Field(alias="postal-code")` +
   `model_config = ConfigDict(populate_by_name=True)`, serializando con
   `.model_dump(by_alias=True)`. Es una desviación técnica necesaria
   respecto a `customer_dto.py` (no requiere decisión de negocio, es
   la única forma de cumplir el contrato del spec) — ver sección
   "Puntos de extensión".
6. **Validaciones de campo no especificadas** (`country`, `state`,
   `city`, `address`, `postal_code`). **CONFIRMADO:** placeholders
   razonables por analogía con `CustomerRqst`:
   - `country`, `state`, `city`: `min_length=2, max_length=100`.
   - `address`: `min_length=3, max_length=200`.
   - `postal_code`: `min_length=3, max_length=15` (alfanumérico, no
     restringido a solo dígitos, por países con formatos distintos).
7. **Existencia del customer al operar sobre addresses.**
   - En `POST` (create): debe fallar si el customer no existe. Se
     resuelve dejando que la FK `addresses.customer_id ->
     customers.id` dispare `IntegrityError`, capturado en el
     repositorio y traducido a `CustomerNotFoundError` (reutilizando la
     excepción ya existente). Evita una consulta extra de verificación.
   - En `GET`/`PATCH`/`PUT`/`DELETE`. **CONFIRMADO: no distinguir.**
     Si el customer no existe, la consulta por `(customer_id,
     address_id)` simplemente no encuentra filas y se responde
     `AddressNotFoundError` (404) genérico, sin diferenciar "customer
     no existe" de "address no existe". No se hace round-trip
     adicional de verificación.
8. **Cascade delete. CONFIRMADO:** `ForeignKey(..., ondelete="CASCADE")`
   a nivel de DB. Al borrar un `Customer` se borran automáticamente sus
   `Address` asociadas. `customer_service.delete_by_id` no requiere
   cambios (el cascade lo resuelve la BD).
9. **Ubicación de `InvalidUUIDError`.** Hoy vive en
   `src/exception/customer_exception.py` aunque es genérica (se
   reutilizará tal cual para `address_id`/`customer_id`). No se
   propone moverla en este plan para no introducir un refactor no
   solicitado, pero se señala como candidata a `src/exception/
   common_exception.py` si se agregan más entidades en el futuro.
10. **Tests. CONFIRMADO:** se agrega `pytest` como dependencia nueva
    (`uv add --dev pytest`, + `pytest-mock`) y se implementan tests en
    todas las capas de `Address` (dominio, DTOs, servicio, persistencia
    y rutas), según la Fase 9.

---

## Fase 1 — Dominio (`src/domain/`)

**Objetivo:** entidad `Address` pura, sin dependencias externas.

- Crear `src/domain/address.py`:
  - Atributos privados (name mangling): `__id: uuid.UUID`,
    `__customer_id: uuid.UUID`, `__country: str`, `__state: str`,
    `__city: str`, `__address: str`, `__postal_code: str`.
  - `create(customer_id, country, state, city, address, postal_code)`
    → genera `uuid.uuid4()` internamente (igual que `Customer.create`).
  - `restore(id, customer_id, country, state, city, address,
    postal_code)` → reconstrucción desde persistencia.
  - `@property` para todos los campos; `@<attr>.setter` para
    `country`, `state`, `city`, `address`, `postal_code` (son los
    únicos editables vía `PATCH`/`PUT`). `id` y `customer_id` sólo
    lectura (sin setter), igual que `id` en `Customer`.
  - Sin imports de Flask/SQLAlchemy/Pydantic.

**Dependencias:** ninguna (capa pura). Conceptualmente depende de que
exista un `Customer.id` válido, pero eso se valida en capas superiores.

---

## Fase 2 — Excepciones de dominio (`src/exception/`)

- Crear `src/exception/address_exception.py`:
  - `AddressNotFoundError(customer_id: uuid.UUID, address_id:
    uuid.UUID)` — mensaje incluye ambos ids.
  - `MaxAddressesPerCustomerError(customer_id: uuid.UUID, limit: int =
    5)` — para la regla de negocio del punto 4 de la sección de
    ambigüedades.
- Reutilizar sin modificar: `CustomerNotFoundError` e
  `InvalidUUIDError` de `src/exception/customer_exception.py` (ver
  ambigüedad 9 sobre su ubicación).

**Dependencias:** ninguna (no importa nada de `src/domain/address.py`,
igual que `customer_exception.py` no depende de `domain/customer.py`).

---

## Fase 3 — DTOs (`src/application/dto/`)

- Crear `src/application/dto/address_dto.py`:
  - `AddressRqst` (Pydantic `BaseModel`, para `POST` y `PUT`):
    `country`, `state`, `city`, `address`: `str` con `Field(min_length=...,
    max_length=...)` (ver ambigüedad 6); `postal_code: str =
    Field(alias="postal-code", min_length=3, max_length=15)`.
    `model_config = ConfigDict(populate_by_name=True)` para poder
    construir tanto desde `postal-code` (JSON entrante) como desde
    `postal_code` (uso interno/tests).
  - `AddressPatchRqst` (para `PATCH`, **DTO nuevo, sin precedente en
    el proyecto**): mismos campos pero todos `Optional[str] = None`,
    misma configuración de alias. Es la primera vez que el proyecto
    necesita un DTO de actualización parcial (`Customer` sólo tiene
    `update_all`, reemplazo total) — ver "Puntos de extensión".
  - `AddressRsps`: `id: uuid.UUID`, `country`, `state`, `city`,
    `address`: `str`, `postal_code: str = Field(alias="postal-code")`,
    con `populate_by_name=True` para poder construirlo desde el
    dominio usando el nombre `postal_code` y servirlo con
    `.model_dump(by_alias=True)` como `postal-code`.

**Dependencias:** Fase 1 (los nombres de campo deben alinear con los
atributos del dominio para que el servicio los mapee 1:1, igual que
`CustomerRsps` espeja `Customer`).

---

## Fase 4 — Puerto del repositorio (`src/application/repository/`)

- Crear `src/application/repository/address_repository.py` (`ABC`,
  sin SQLAlchemy):
  - `create(self, address: Address) -> None`
  - `get_by_id(self, customer_id: uuid.UUID, address_id: uuid.UUID) ->
    Address`
  - `get_all_by_customer_id(self, customer_id: uuid.UUID) ->
    list[Address]`
  - `count_by_customer_id(self, customer_id: uuid.UUID) -> int`
    (necesario para la regla de máximo 5; no tiene equivalente en
    `CustomerRepository`, es nuevo).
  - `update_partial(self, customer_id: uuid.UUID, address_id:
    uuid.UUID, address: Address) -> Address` (recibe la entidad ya
    fusionada con los cambios del PATCH; el servicio hace el merge,
    el repositorio sólo persiste — ver Fase 5).
  - `upsert(self, customer_id: uuid.UUID, address_id: uuid.UUID,
    address: Address) -> tuple[Address, bool]` (el `bool` indica si
    fue creado, para decidir `200` vs `201` en la Fase 7 — ver
    ambigüedad 1).
  - `delete_by_id(self, customer_id: uuid.UUID, address_id: uuid.UUID)
    -> None`

**Dependencias:** Fase 1 (tipo `Address`).

---

## Fase 5 — Servicio de aplicación (`src/application/services/`)

- Crear `src/application/services/address_service.py`:
  - `AddressService(repository: AddressRepository)` — inyección por
    constructor, igual que `CustomerService`.
  - `create(customer_id, address_rqst: AddressRqst) -> AddressRsps`:
    valida `count_by_customer_id(customer_id) >= 5` →
    `MaxAddressesPerCustomerError`; construye `Address.create(...)`;
    `repository.create(...)`; devuelve `AddressRsps`.
  - `get_by_id(customer_id, address_id) -> AddressRsps`.
  - `get_all(customer_id) -> list[AddressRsps]`.
  - `update_partial(customer_id, address_id, patch_rqst:
    AddressPatchRqst) -> AddressRsps`: obtiene el `Address` actual vía
    `repository.get_by_id`, aplica sólo los setters de los campos no
    `None` del DTO, persiste vía `repository.update_partial`, retorna
    `AddressRsps`. (Patrón nuevo: `CustomerService` no tiene
    equivalente porque `Customer` no soporta `PATCH`.)
  - `replace(customer_id, address_id, address_rqst: AddressRqst) ->
    tuple[AddressRsps, bool]`: construye `Address.restore(address_id,
    customer_id, ...)` con los datos del request (el `id` del payload,
    si viene, se ignora — decisión confirmada, punto 2) y llama
    `repository.upsert(...)`; si `created is True` y ya había 5
    addresses, debe fallar con `MaxAddressesPerCustomerError` **antes**
    de intentar el upsert (chequeo previo con `count_by_customer_id`,
    igual que en `create`) — decisión confirmada, punto 4. El `bool`
    se propaga a la Fase 7 para decidir el status code.
  - `delete_by_id(customer_id, address_id) -> None`.

**Dependencias:** Fase 3 (DTOs), Fase 4 (puerto), Fase 2 (excepciones
usadas indirectamente vía el repositorio), Fase 1 (dominio).

---

## Fase 6 — Persistencia (`src/infrastructure/persistence/`)

- Crear `src/infrastructure/persistence/address_model.py`:
  - `AddressModel(db.Model)`, `__tablename__ = "addresses"`.
  - `id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True),
    primary_key=True)`.
  - `customer_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True),
    ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)`
    (cascade delete confirmado, punto 8).
  - `country`, `state`, `city`, `address`, `postal_code`: `Mapped[str]
    = mapped_column(String, nullable=False)` (estilo 2.0, igual que
    `customer_model.py`; sin `Column` legacy).
  - Opcional: índice en `customer_id` para acelerar
    `get_all_by_customer_id`/`count_by_customer_id`
    (`mapped_column(..., index=True)`).

- Crear
  `src/infrastructure/persistence/database_address_repository.py`:
  - `DatabaseAddressRepository(AddressRepository)`.
  - `create`: `INSERT`; captura `IntegrityError` → si es violación de
    FK, `raise CustomerNotFoundError(customer_id) from error` (punto 7);
    cualquier otro `SQLAlchemyError` →
    `PersistenceUnavailableError` (reutilizada de
    `customer_exception.py`, no es específica de `Customer` a pesar
    del nombre del módulo — mismo comentario que ambigüedad 9).
  - `get_by_id`: `select(AddressModel).where(id==..., customer_id==...)`;
    si no hay resultado → `AddressNotFoundError(customer_id,
    address_id)`.
  - `get_all_by_customer_id`: `select(...).where(customer_id ==
    ...).order_by(...)` (definir criterio de orden, p. ej. por
    `country`/`city`, ya que el spec no lo especifica — asunción
    menor, sin impacto funcional).
  - `count_by_customer_id`: `select(func.count()).select_from(
    AddressModel).where(customer_id == ...)`.
  - `update_partial`: `update(AddressModel).where(id==..., customer_id
    ==...).values(...).returning(AddressModel.id)`, igual patrón que
    `update_all` de `database_customer_repository.py`; si
    `scalar_one_or_none() is None` → `AddressNotFoundError`.
  - `upsert`: **no hay precedente en el proyecto** (Customer no tiene
    upsert). Implementar como `SELECT` explícito para detectar
    existencia y luego `INSERT` o `UPDATE` dentro de la misma
    transacción (preferido sobre `session.merge()` para mantener el
    estilo explícito de statements ya usado en el repo). Devuelve
    `(address, created: bool)`.
  - `delete_by_id`: igual patrón que `delete_by_id` de customer, con
    `AddressNotFoundError` si no hay filas afectadas.
  - `_to_domain` / `_to_model`: métodos estáticos de traducción,
    replicando el patrón exacto de `database_customer_repository.py`.
  - Logging estructurado con `logger.error(..., extra={"operation":
    ..., "sql_alchemy_error": type(error).__name__})`. **No** replicar
    el `print(...)` de depuración que existe hoy en
    `database_customer_repository._handle_error` (es ruido, no forma
    parte de la convención documentada: usar sólo `logging`).

**Dependencias:** Fase 1 (dominio), Fase 4 (puerto), Fase 2
(excepciones), y la tabla `customers` ya existente (FK).

---

## Fase 7 — API web (`src/infrastructure/web/`)

- Extraer `parse_uuid` de `customer_routes.py` a un módulo compartido,
  p. ej. `src/infrastructure/web/uuid_parser.py`, para no duplicarlo en
  `address_routes.py` (pequeña refactorización necesaria, no estaba
  pedida por el spec pero evita copy-paste — ver "Puntos de
  extensión"). Actualizar el import en `customer_routes.py`.

- Crear `src/infrastructure/web/address_routes.py`:
  - `address_bp = Blueprint("address", __name__, url_prefix=
    "/api/v1/customers/<string:customer_id>/addresses")` (verificar
    que Flask resuelve correctamente el segmento dinámico dentro del
    `url_prefix` de un Blueprint — soportado desde Flask ≥0.7, pero se
    debe probar explícitamente ya que el proyecto no lo usa hoy en
    ningún blueprint).
  - `POST ""` → `create`: parsea `customer_id`, valida
    `AddressRqst.model_validate(request.get_json())`, delega a
    `address_service.create`, responde `.model_dump(by_alias=True)`,
    `HTTPStatus.CREATED`.
  - `GET "/all"` → `get_all`: debe registrarse junto a
    `"/<string:address_id>"`; replicar el mismo orden que
    `customer_routes.py` (`/all` como ruta literal), que ya funciona
    correctamente porque Flask prioriza rutas estáticas sobre
    dinámicas independientemente del orden de registro.
  - `GET "/<string:address_id>"` → `get_by_id`: `HTTPStatus.OK` (404
    vía `error_handler`).
  - `PATCH "/<string:address_id>"` → `update_partial`: valida con
    `AddressPatchRqst`, `HTTPStatus.OK`.
  - `PUT "/<string:address_id>"` → `replace`: valida con `AddressRqst`
    (ignorando cualquier `id` del body), usa el `bool created` que
    retorna el servicio para responder `HTTPStatus.CREATED` si se creó
    o `HTTPStatus.OK` si se reemplazó (decisión confirmada, punto 1).
  - `DELETE "/<string:address_id>"` → `delete_by_id`:
    `Response(status=HTTPStatus.NO_CONTENT)`.
  - Todos los handlers son "thin": sólo parseo + delegación al
    servicio + `.model_dump(...)`, sin `try/except` (los errores se
    resuelven en `error_handler.py`).

- Modificar `src/infrastructure/web/error_handler.py`:
  - Importar `AddressNotFoundError`, `MaxAddressesPerCustomerError` de
    `src/exception/address_exception.py`.
  - `handle_address_not_found_error` → `404`, payload con
    `customer_id` y `address_id`.
  - `handle_max_addresses_per_customer_error` → `409` (ver ambigüedad
    4), payload con `customer_id` y `limit`.
  - Registrar ambos en `register_exception_handlers(app)`. No se
    requiere tocar los handlers de `Customer` ya existentes
    (`CustomerNotFoundError` ya cubre el caso de la ambigüedad 7 en
    `create`).

- Modificar `src/infrastructure/web/app.py`:
  - Importar y registrar `address_bp` con
    `app.register_blueprint(address_bp)`.

**Dependencias:** Fase 5 (servicio), Fase 2 (excepciones), Fase 6
(repositorio concreto para instanciar `DatabaseAddressRepository()` al
inicio del módulo, igual que `customer_routes.py` hace con
`DatabaseCustomerRepository()`).

---

## Fase 8 — Verificación cruzada / wiring final

- Confirmar que `main.py` no necesita cambios (usa `create_app()`).
- Revisar si existe algún mecanismo de creación de tablas
  (`db.create_all()`, script SQL, Alembic). Hoy no se encontró ninguno
  ni para `customers` — dejar constancia de que `addresses` tendrá el
  mismo problema/gap y no es responsabilidad de esta feature
  resolverlo, salvo que el usuario lo pida explícitamente.
- Ejecutar `ruff` y `mypy` (dependencias de dev ya presentes) sobre
  todo el código nuevo para asegurar tipado estricto y estilo,
  siguiendo la convención transversal del proyecto.
- Revisar `request_logging.py` para confirmar que el logging de
  requests ya es genérico (no específico de `Customer`) y no requiere
  cambios para cubrir las nuevas rutas de `Address`.

**Dependencias:** Fases 1–7 completas.

---

## Fase 9 — Tests (nuevo para el repo)

No existe hoy infraestructura de testing en el proyecto. **Confirmado**
introducir `pytest` (`uv add --dev pytest`, + `pytest-mock` para
mockear `AddressRepository`/`CustomerRepository` en los tests de
servicio). Estructura propuesta, en espejo con `src/`:

- `tests/domain/test_address.py`: `create()` genera `uuid4`; `restore()`
  reconstruye exactamente los valores dados; setters mutan sólo el
  atributo esperado; atributos no accesibles fuera de la clase
  (name mangling).
- `tests/application/dto/test_address_dto.py`: `AddressRqst` acepta
  `postal-code` (alias) y `postal_code` (nombre); rechaza longitudes
  fuera de rango (Fase 3, punto 6); `AddressPatchRqst` permite todos
  los campos ausentes; `AddressRsps.model_dump(by_alias=True)`
  produce la clave `postal-code`.
- `tests/application/services/test_address_service.py`: con
  `AddressRepository` mockeado —
  - `create` respeta el límite de 5 (`count_by_customer_id == 5` →
    `MaxAddressesPerCustomerError`, sin llamar a `repository.create`).
  - `update_partial` sólo sobreescribe los campos presentes en el
    patch, preservando los demás.
  - `replace` ignora el `id` del payload y usa el de la URL.
  - Todos los métodos devuelven DTOs (`AddressRsps`), nunca `Address`.
- `tests/infrastructure/persistence/test_database_address_repository.py`:
  requiere decidir estrategia (SQLite en memoria vs. Postgres real vía
  `docker-compose` vs. `testcontainers`) — **flag**: el proyecto usa
  Postgres específicamente (`psycopg`, tipos `Uuid`), así que SQLite en
  memoria podría no ser 100% representativo (p. ej. `ON DELETE
  CASCADE`, tipos `Uuid`). Recomendación: usar el mismo Postgres de
  `docker-compose.yaml` en un esquema/DB de test, o introducir
  `testcontainers` como nueva dependencia (requiere aprobación del
  usuario). Cubrir: `IntegrityError` en `create` sin customer válido →
  `CustomerNotFoundError`; `count_by_customer_id`; `upsert` create vs.
  update; `AddressNotFoundError` en update/delete sobre id inexistente.
- `tests/infrastructure/web/test_address_routes.py`: usando el Flask
  test client (`create_app().test_client()`) —
  status codes exactos por endpoint (201/200/204/404/409/400), forma
  del JSON de respuesta (incluyendo `postal-code` con guion), y que
  `error_handler.py` traduce cada excepción de dominio al status
  correcto.

**Dependencias:** todas las fases anteriores. Esta fase puede empezar
en paralelo a la Fase 8 una vez cerradas las Fases 1–7 de cada
capa respectiva (tests de dominio tan pronto termine la Fase 1, etc.),
pero se agrupa al final del documento porque depende de una decisión
de tooling (agregar `pytest`) que no estaba resuelta en el repo.

---

## Puntos de extensión (desviaciones respecto al patrón de `Customer`)

Estos son los lugares donde el patrón existente de `Customer` no cubre
completamente el caso de `Address`, y por qué se decidió desviarse:

1. **DTO de actualización parcial (`AddressPatchRqst`).** `Customer`
   sólo soporta reemplazo total (`update_all` + `PUT`). `Address`
   requiere `PATCH` con todos los campos opcionales — no hay
   precedente, se introduce un DTO nuevo en vez de reutilizar
   `AddressRqst` con campos opcionales, para no debilitar la
   validación de `POST`/`PUT` (que sí deben exigir todos los campos).
2. **Alias de Pydantic (`postal-code` ↔ `postal_code`).** Primer caso
   en el proyecto donde el nombre del campo en JSON no es válido como
   identificador Python. Se resuelve con `Field(alias=...)` +
   `populate_by_name=True`, y obliga a usar `.model_dump(by_alias=
   True)` en las rutas en vez de `.model_dump()` a secas como hace
   hoy `customer_routes.py`.
3. **Upsert (`PUT` con creación implícita).** No existe en
   `CustomerRepository`/`CustomerService` (el `PUT` de `Customer` es
   reemplazo estricto, falla si no existe). Se añade un método
   `upsert` nuevo en el puerto y su implementación, y el servicio debe
   propagar un flag `created: bool` hacia la capa web para decidir el
   status code — esto agrega una firma de retorno (`tuple[...]`)
   distinta al patrón `-> Rsps` usado en el resto de servicios; se
   documenta explícitamente para que sea intencional y no un
   descuido.
4. **`count_by_customer_id` en el repositorio.** Nuevo método sin
   equivalente en `CustomerRepository`, necesario únicamente por la
   regla de negocio de máximo 5 addresses.
5. **`parse_uuid` compartido.** Se extrae de `customer_routes.py` a un
   módulo común para evitar duplicación entre dos blueprints — es un
   micro-refactor no solicitado por el spec pero necesario para no
   violar DRY al introducir el segundo blueprint.
6. **Blueprint con segmento dinámico en `url_prefix`.** Ningún
   blueprint existente en el proyecto anida un recurso bajo otro; se
   debe verificar en la práctica (Fase 7) que Flask resuelve
   `customer_id` correctamente como kwarg en todos los handlers.

---

## Orden de ejecución resumido

```
Fase 1 (Dominio)
   -> Fase 2 (Excepciones)              [independiente de Fase 1, puede ir en paralelo]
      -> Fase 3 (DTOs)
         -> Fase 4 (Puerto repositorio)
            -> Fase 5 (Servicio)
               -> Fase 6 (Persistencia)
                  -> Fase 7 (API web)
                     -> Fase 8 (Wiring / verificación)
                        -> Fase 9 (Tests, requiere decisión de tooling)
```

Todos los puntos de la sección de ambigüedades (1–10) están confirmados
con el usuario (2026-08-11). El plan queda listo para iniciar la
implementación desde la Fase 1 sin bloqueos pendientes, salvo los
puntos 5 y 9, que son decisiones técnicas ya resueltas en el propio
plan (no requerían decisión de negocio).
