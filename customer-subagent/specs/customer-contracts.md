# Customers

Aplicación web de clientes, cada cliente tiene los atributos de id, name, age y email.

## Stacks

### Backend

- Python
- Flask
- Pytest
- SQLAlchemy
- PostgreSQL
- Ruff
- MyPy
- Pytest
- UV
- Docker

## Contratos

### Entidades

- Customer
```json
{
    "id": 1,
    "name": "Curso de React",
    "age": 39,
    "email": "email@test.com", 
    "created_at": "2021-01-01",
    "updated_at": "2021-01-01",
    "deleted_at": "2021-01-01"
}
```

### Endpoints


- POST /customers -> Crear un cliente

Request
```json
{
    "name": "Curso de React",
    "age": 39,
    "email": "email@test.com",
}
```

Response
status codes

201 - Creación
4xx - error en el cliente
5xx - error en el servidor

- GET /customers/all -> Listar todos los clientes

Response
```json
[
    {
        "id": 1,
        "name": "Curso de React",
        "age": 39,
        "email": "email@test.com", 
    }
]
```

status code 
200 - Ok

- GET /customers/:id -> Obtener un cliente

Response
```json
{
    "id": 1,
    "name": "Curso de React",
    "age": 39,
    "email": "email@test.com"
}
```

status code
200 - Ok
404 - Not found
5xx - error en el servidor


- PATCH /customers/:id -> Actualizar los atributos de un cliente
Request
```json
{
    "id": 1,
    "name": "Curso de React",
    "age": 39,
    "email": "email@test.com"
}
```

Response
```json
{
    "id": 1,
    "name": "Curso de React",
    "age": 39,
    "email": "email@test.com"
}
```

status code
200 - Ok
404 - Not found
5xx - error en el servidor



- DELETE /customers/:id -> Eliminar un cliente
Response

status code
200 - Ok
404 - Not found
5xx - error en el servidor