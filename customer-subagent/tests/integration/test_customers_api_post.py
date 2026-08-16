from customers.infrastructure.persistence.repositories import (
    SQLAlchemyCustomerRepository,
)


def test_create_customer_returns_201(client):
    response = client.post(
        "/customers",
        json={"name": "Ada Lovelace", "age": 30, "email": "ada@example.com"},
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == "Ada Lovelace"
    assert body["age"] == 30
    assert body["email"] == "ada@example.com"
    assert isinstance(body["id"], int)


def test_create_customer_with_malformed_json_returns_400(client):
    response = client.post(
        "/customers", data="not json", content_type="application/json"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "validation failed"


def test_create_customer_missing_field_returns_400(client):
    response = client.post("/customers", json={"name": "Ada Lovelace", "age": 30})

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "validation failed"
    assert "email" in body["details"]


def test_create_customer_invalid_age_returns_400(client):
    response = client.post(
        "/customers",
        json={"name": "Ada Lovelace", "age": 200, "email": "ada@example.com"},
    )

    assert response.status_code == 400
    assert response.get_json()["details"]["age"]


def test_create_customer_invalid_email_returns_400(client):
    response = client.post(
        "/customers", json={"name": "Ada Lovelace", "age": 30, "email": "not-an-email"}
    )

    assert response.status_code == 400
    assert response.get_json()["details"]["email"]


def test_create_customer_with_duplicate_email_returns_409(client, create_customer):
    create_customer(email="ada@example.com")

    response = create_customer(name="Ada 2", age=31, email="ada@example.com")

    assert response.status_code == 409
    assert response.get_json()["error"] == "email already exists"


def test_create_customer_unexpected_error_returns_500_without_leaking_details(
    client, monkeypatch
):
    def _raise(self, customer):
        raise RuntimeError("boom: connection lost to internal db host")

    monkeypatch.setattr(SQLAlchemyCustomerRepository, "add", _raise)

    response = client.post(
        "/customers",
        json={"name": "Ada Lovelace", "age": 30, "email": "ada@example.com"},
    )

    assert response.status_code == 500
    body = response.get_json()
    assert body == {"error": "internal server error"}
    assert "boom" not in response.get_data(as_text=True)
