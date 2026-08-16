from customers.infrastructure.persistence.repositories import (
    SQLAlchemyAddressRepository,
)


def test_list_addresses_returns_empty_list(client, create_customer):
    customer = create_customer().get_json()

    response = client.get(f"/customers/{customer['id']}/addresses")

    assert response.status_code == 200
    assert response.get_json() == []


def test_list_addresses_returns_created_addresses(
    client, create_customer, create_address
):
    customer = create_customer().get_json()
    create_address(customer["id"], city="Villavicencio")
    create_address(customer["id"], city="Bogota")

    response = client.get(f"/customers/{customer['id']}/addresses")

    assert response.status_code == 200
    cities = {address["city"] for address in response.get_json()}
    assert cities == {"Villavicencio", "Bogota"}


def test_list_addresses_excludes_soft_deleted(client, create_customer, create_address):
    customer = create_customer().get_json()
    active = create_address(customer["id"]).get_json()
    deleted = create_address(customer["id"], city="Bogota").get_json()
    client.delete(f"/customers/{customer['id']}/addresses/{deleted['id']}")

    response = client.get(f"/customers/{customer['id']}/addresses")

    ids = [address["id"] for address in response.get_json()]
    assert ids == [active["id"]]


def test_list_addresses_excludes_addresses_from_other_customers(
    client, create_customer, create_address
):
    customer_a = create_customer().get_json()
    customer_b = create_customer(email="grace@example.com").get_json()
    create_address(customer_a["id"])
    create_address(customer_b["id"], city="Bogota")

    response = client.get(f"/customers/{customer_a['id']}/addresses")

    assert len(response.get_json()) == 1


def test_list_addresses_returns_404_when_customer_does_not_exist(client):
    response = client.get("/customers/999999/addresses")

    assert response.status_code == 404
    assert response.get_json() == {"error": "customer not found"}


def test_list_addresses_unexpected_error_returns_500_without_leaking_details(
    client, create_customer, monkeypatch
):
    customer = create_customer().get_json()

    def _raise(self, customer_id):
        raise RuntimeError("boom: connection lost to internal db host")

    monkeypatch.setattr(SQLAlchemyAddressRepository, "list_active_by_customer", _raise)

    response = client.get(f"/customers/{customer['id']}/addresses")

    assert response.status_code == 500
    body = response.get_json()
    assert body == {"error": "internal server error"}
    assert "boom" not in response.get_data(as_text=True)
