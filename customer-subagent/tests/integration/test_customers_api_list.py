from customers.infrastructure.persistence.repositories import (
    SQLAlchemyCustomerRepository,
)


def test_list_customers_returns_empty_list(client):
    response = client.get("/customers/all")

    assert response.status_code == 200
    assert response.get_json() == []


def test_list_customers_returns_created_customers(client, create_customer):
    create_customer(name="Ada Lovelace", email="ada@example.com")
    create_customer(name="Grace Hopper", email="grace@example.com")

    response = client.get("/customers/all")

    assert response.status_code == 200
    emails = {customer["email"] for customer in response.get_json()}
    assert emails == {"ada@example.com", "grace@example.com"}


def test_list_customers_excludes_soft_deleted(client, create_customer):
    active = create_customer(email="ada@example.com").get_json()
    deleted = create_customer(email="grace@example.com").get_json()
    client.delete(f"/customers/{deleted['id']}")

    response = client.get("/customers/all")

    ids = [customer["id"] for customer in response.get_json()]
    assert ids == [active["id"]]


def test_list_customers_unexpected_error_returns_500_without_leaking_details(
    client, monkeypatch
):
    def _raise(self):
        raise RuntimeError("boom: connection lost to internal db host")

    monkeypatch.setattr(SQLAlchemyCustomerRepository, "list_active", _raise)

    response = client.get("/customers/all")

    assert response.status_code == 500
    body = response.get_json()
    assert body == {"error": "internal server error"}
    assert "boom" not in response.get_data(as_text=True)
