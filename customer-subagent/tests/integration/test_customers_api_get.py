from customers.infrastructure.persistence.repositories import (
    SQLAlchemyCustomerRepository,
)


def test_get_customer_returns_200(client, create_customer):
    created = create_customer().get_json()

    response = client.get(f"/customers/{created['id']}")

    assert response.status_code == 200
    assert response.get_json() == created


def test_get_customer_returns_404_when_not_found(client):
    response = client.get("/customers/999999")

    assert response.status_code == 404
    assert response.get_json() == {"error": "customer not found"}


def test_unknown_route_returns_default_404_not_generic_500(client):
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.get_json() != {"error": "internal server error"}


def test_get_customer_returns_404_when_soft_deleted(client, create_customer):
    created = create_customer().get_json()
    client.delete(f"/customers/{created['id']}")

    response = client.get(f"/customers/{created['id']}")

    assert response.status_code == 404


def test_get_customer_unexpected_error_returns_500_without_leaking_details(
    client, create_customer, monkeypatch
):
    created = create_customer().get_json()

    def _raise(self, customer_id, *, include_deleted=False):
        raise RuntimeError("boom: connection lost to internal db host")

    monkeypatch.setattr(SQLAlchemyCustomerRepository, "get_by_id", _raise)

    response = client.get(f"/customers/{created['id']}")

    assert response.status_code == 500
    body = response.get_json()
    assert body == {"error": "internal server error"}
    assert "boom" not in response.get_data(as_text=True)
