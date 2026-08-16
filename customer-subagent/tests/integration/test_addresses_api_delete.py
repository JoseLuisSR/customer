from customers.infrastructure.persistence.repositories import (
    SQLAlchemyAddressRepository,
)


def test_delete_address_returns_200_and_soft_deletes(
    client, create_customer, create_address
):
    customer = create_customer().get_json()
    created = create_address(customer["id"]).get_json()

    response = client.delete(f"/customers/{customer['id']}/addresses/{created['id']}")

    assert response.status_code == 200
    assert response.get_json() == {}
    assert (
        client.get(f"/customers/{customer['id']}/addresses/{created['id']}").status_code
        == 404
    )


def test_delete_address_returns_404_when_customer_does_not_exist(client):
    response = client.delete("/customers/999999/addresses/1")

    assert response.status_code == 404
    assert response.get_json() == {"error": "customer not found"}


def test_delete_address_returns_404_when_address_does_not_exist(
    client, create_customer
):
    customer = create_customer().get_json()

    response = client.delete(f"/customers/{customer['id']}/addresses/999999")

    assert response.status_code == 404
    assert response.get_json() == {"error": "address not found"}


def test_delete_address_returns_404_when_already_deleted(
    client, create_customer, create_address
):
    customer = create_customer().get_json()
    created = create_address(customer["id"]).get_json()
    client.delete(f"/customers/{customer['id']}/addresses/{created['id']}")

    response = client.delete(f"/customers/{customer['id']}/addresses/{created['id']}")

    assert response.status_code == 404


def test_delete_address_returns_404_when_belongs_to_another_customer(
    client, create_customer, create_address
):
    customer_a = create_customer().get_json()
    customer_b = create_customer(email="grace@example.com").get_json()
    address_of_b = create_address(customer_b["id"]).get_json()

    response = client.delete(
        f"/customers/{customer_a['id']}/addresses/{address_of_b['id']}"
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "address not found"}

    still_there = client.get(
        f"/customers/{customer_b['id']}/addresses/{address_of_b['id']}"
    )
    assert still_there.status_code == 200


def test_delete_address_unexpected_error_returns_500_without_leaking_details(
    client, create_customer, create_address, monkeypatch
):
    customer = create_customer().get_json()
    created = create_address(customer["id"]).get_json()

    def _raise(self, address):
        raise RuntimeError("boom: connection lost to internal db host")

    monkeypatch.setattr(SQLAlchemyAddressRepository, "soft_delete", _raise)

    response = client.delete(f"/customers/{customer['id']}/addresses/{created['id']}")

    assert response.status_code == 500
    body = response.get_json()
    assert body == {"error": "internal server error"}
    assert "boom" not in response.get_data(as_text=True)
