from customers.infrastructure.persistence.repositories import (
    SQLAlchemyCustomerRepository,
)


def test_delete_customer_returns_200_and_soft_deletes(client, create_customer):
    created = create_customer().get_json()

    response = client.delete(f"/customers/{created['id']}")

    assert response.status_code == 200
    assert response.get_json() == {}
    assert client.get(f"/customers/{created['id']}").status_code == 404


def test_delete_customer_returns_404_when_not_found(client):
    response = client.delete("/customers/999999")

    assert response.status_code == 404


def test_delete_customer_returns_404_when_already_deleted(client, create_customer):
    created = create_customer().get_json()
    client.delete(f"/customers/{created['id']}")

    response = client.delete(f"/customers/{created['id']}")

    assert response.status_code == 404


def test_delete_customer_unexpected_error_returns_500_without_leaking_details(
    client, create_customer, monkeypatch
):
    created = create_customer().get_json()

    def _raise(self, customer):
        raise RuntimeError("boom: connection lost to internal db host")

    monkeypatch.setattr(SQLAlchemyCustomerRepository, "soft_delete", _raise)

    response = client.delete(f"/customers/{created['id']}")

    assert response.status_code == 500
    body = response.get_json()
    assert body == {"error": "internal server error"}
    assert "boom" not in response.get_data(as_text=True)
