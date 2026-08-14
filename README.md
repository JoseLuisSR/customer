# Customers

API Flask para gestionar customers y sus addresses, con arquitectura hexagonal
(dominio / aplicación / infraestructura), SQLAlchemy 2.0 y Pydantic.

## Requisitos

- [uv](https://docs.astral.sh/uv/)
- Docker y Docker Compose

## Configuración

Variables de entorno en `.env` (no versionado):

```
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=
```

## Levantar el proyecto

```
docker compose up --build
```

Esto levanta, en orden: `postgres` (con healthcheck), `migrate` (aplica las
migraciones de base de datos pendientes y termina) y `app` (arranca solo si
`migrate` terminó exitosamente).

## Migraciones de base de datos

El esquema de base de datos se versiona con [Flask-Migrate](https://flask-migrate.readthedocs.io/)
(Alembic) en `migrations/`. **No existe `db.create_all()`**: las tablas solo
se crean/actualizan a través de migraciones.

### Aplicarlas

En `docker compose up`, el servicio `migrate` corre `flask db upgrade`
automáticamente antes de que arranque `app`. No requiere ningún paso manual.

### Generar una migración nueva

Cuando se agregue o modifique un modelo en `src/infrastructure/persistence/`:

1. Levantar solo la base de datos: `docker compose up -d postgres`.
2. Generar la migración contra esa base de datos, desde el host:
   ```
   FLASK_APP=main:app POSTGRES_HOST=localhost uv run flask db migrate -m "mensaje descriptivo"
   ```
3. **Revisar a mano** el archivo generado en `migrations/versions/` — el
   autogenerate de Alembic no siempre detecta bien constraints (`ondelete`,
   índices, tipos), así que hay que confirmar que el DDL coincide exactamente
   con el modelo de SQLAlchemy.
4. Aplicarla localmente para probarla: `FLASK_APP=main:app POSTGRES_HOST=localhost uv run flask db upgrade`.
5. Commitear el archivo de migración junto con el cambio de modelo.

### Agregar una entidad nueva

Al agregar una entidad nueva (dominio, DTOs, puerto de repositorio, servicio,
modelo de persistencia y rutas, siguiendo el patrón ya usado por `Customer` y
`Address`), el último paso es generar y revisar su migración como se describe
arriba, antes de dar la feature por completa.
