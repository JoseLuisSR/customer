# Addresses

Cada customer tiene una lista de direcciones asociada.

## Contratos

### Entidades

- Address
```json
{
    "id": 1,
    "country": "Colombia",
    "state": "Meta",
    "city": "Villavicencio", 
    "postalcode": "50001",
    "address": "2021-01-01",
    "created_at": "2021-01-01",
    "updated_at": "2021-01-01",
    "deleted_at": "2021-01-01"
}
```

### Endpoints


- POST /customers/:id/addresses -> Crear un cliente

Request
```json
{
    "id": 1,
    "country": "Colombia",
    "state": "Meta",
    "city": "Villavicencio", 
    "postalcode": "50001",
    "address": "2021-01-01"
}
```

Response
status codes

201 - Creación
4xx - error en el cliente
5xx - error en el servidor

- GET /customers/:id/addresses -> Listar todos las direcciones del cliente con id.

Response
```json
[
    {
        "id": 1,
        "country": "Colombia",
        "state": "Meta",
        "city": "Villavicencio", 
        "postalcode": "50001",
        "address": "2021-01-01"
    }
]
```

status code 
200 - Ok

- GET /customers/:id/addresses/:id -> Consultar una dirección con id del cliente con id.

Response
```json
{
    "id": 1,
    "country": "Colombia",
    "state": "Meta",
    "city": "Villavicencio", 
    "postalcode": "50001",
    "address": "2021-01-01"
}
```

status code
200 - Ok
404 - Not found
5xx - error en el servidor


- PATCH /customers/:id/addresses/:id -> Actualizar los atributos de una dirección con id, de un cliente con id.
Request
```json
{
    "id": 1,
    "country": "Colombia",
    "state": "Meta",
    "city": "Villavicencio", 
    "postalcode": "50001",
    "address": "2021-01-01"
}
```

Response
```json
{
    "id": 1,
    "country": "Colombia",
    "state": "Meta",
    "city": "Villavicencio", 
    "postalcode": "50001",
    "address": "2021-01-01"
}
```

status code
200 - Ok
404 - Not found
5xx - error en el servidor



- DELETE /customers/:id/addresses/:id -> Eliminar una dirección con id de un cliente con id.
Response

status code
200 - Ok
404 - Not found
5xx - error en el servidor