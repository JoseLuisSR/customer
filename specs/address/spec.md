# Addresses

Each customer has a address list with maximum 5 address per customer.

## Contracts

All CRUD operations for address entitie.

### ENTITIES

- Address
```json
{
    "id": "a8943d42-65da-4119-b11a-fb212c0468c1",
    "country": "Colombia",
    "state": "Bogotá",
    "city": "Bogotá",
    "address": "Carre 7 # 126a - 56b",
    "postal-code": "100001",
}
```

## Endpoints

- Create Address by customer id.

POST /customers/{id}/addresses

Request Payload:
```json
{
    "country": "Colombia",
    "state": "Bogotá",
    "city": "Bogotá",
    "address": "Carre 7 # 126a - 56b",
    "postal-code": "100001",
}
´´´

Response:
```json
{
    "id": "a8943d42-65da-4119-b11a-fb212c0468c1",
    "country": "Colombia",
    "state": "Bogotá",
    "city": "Bogotá",
    "address": "Carre 7 # 126a - 56b",
    "postal-code": "100001",
}
```

Status Code:

201: Created
4xx: Cliente error
5xx: Server error

- Read Address by customer id and anddress id.

GET /customers/{id}/addresses/{id}

Response:

```json
{
    "id": "a8943d42-65da-4119-b11a-fb212c0468c1",
    "country": "Colombia",
    "state": "Bogotá",
    "city": "Bogotá",
    "address": "Carre 7 # 126a - 56b",
    "postal-code": "100001",
}
```

Status Code:

200: Ok
404: Address not found
4xx: Cliente error
5xx: Server error

- Read all addresses by customer id.

GET /customers/{id}/addresses/all

Response:

```json
[
    {
        "id": "a8943d42-65da-4119-b11a-fb212c0468c1",
        "country": "Colombia",
        "state": "Bogotá",
        "city": "Bogotá",
        "address": "Carre 7 # 126a - 56b",
        "postal-code": "100001",
    },
    {
        "id": "a8943d42-65da-4119-b11a-fb212c0468c1",
        "country": "Colombia",
        "state": "Bogotá",
        "city": "Bogotá",
        "address": "Carre 7 # 126a - 56b",
        "postal-code": "100001",
    }
...
]
```

Status Code:

200: Ok
4xx: Cliente error
5xx: Server error

- Update address by customer id and address id. All the attributes are optional to send in the request and all are allow to update except the id.

PATCH /customers/{id}/addresses/{id}

Request payload

```json
{
    "country": "Colombia",
    "state": "Bogotá",
    "city": "Bogotá",
    "address": "Carre 7 # 126a - 56b",
    "postal-code": "100001",
}
```

Reponse

```json
{
    "id": "a8943d42-65da-4119-b11a-fb212c0468c1",
    "country": "Colombia",
    "state": "Bogotá",
    "city": "Bogotá",
    "address": "Carre 7 # 126a - 56b",
    "postal-code": "100001",
}
```

Status code
200: Ok
404: Address not found
4xx: Client error
5xx: Server error

- Replace address by customer id and address id. In the case the address does not exist created it. The id is not allow to update or replace.

PUT /customers/{id}/addresses/{id}

Request payload:

```json
{
    "id": "a8943d42-65da-4119-b11a-fb212c0468c1",
    "country": "Colombia",
    "state": "Bogotá",
    "city": "Bogotá",
    "address": "Carre 7 # 126a - 56b",
    "postal-code": "100001",
}
```

Response payload:

```json
{
    "country": "Colombia",
    "state": "Bogotá",
    "city": "Bogotá",
    "address": "Carre 7 # 126a - 56b",
    "postal-code": "100001",
}
```

- Delete address by customer id and address id.

DELETE /customers/{id}/addresses/{id}

Status Code:

204: Not content
404: Address not found
4xx: Cliente error
5xx: Server error

