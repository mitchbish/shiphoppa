from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests


IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def test_account_profile_can_be_read_and_updated() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.get("/account/profile", headers=IMPORTER_HEADERS)
    assert response.status_code == 200
    profile = response.json()
    assert profile["owner_actor_id"] == "dev-importer"
    assert profile["default_delivery_mode"] == "ship_hoppa_pickup"

    update_response = client.put(
        "/account/profile",
        headers=IMPORTER_HEADERS,
        json={
            "importer_company_name": "North Star Imports",
            "delivery_city": "Sydney",
            "delivery_postcode": "2000",
            "default_supplier_city": "Shenzhen",
            "default_supplier_country": "China",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["importer_company_name"] == "North Star Imports"
    assert updated["delivery_city"] == "Sydney"
    assert updated["default_supplier_city"] == "Shenzhen"

    reread = client.get("/account/profile", headers=IMPORTER_HEADERS).json()
    assert reread["delivery_postcode"] == "2000"


def test_account_integrations_have_core_connectors_and_can_update() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.get("/account/integrations", headers=IMPORTER_HEADERS)
    assert response.status_code == 200
    integrations = response.json()
    providers = {integration["provider"] for integration in integrations}
    assert providers == {"alibaba", "email_inbox", "accounting", "supplier_pay", "object_storage"}

    alibaba = next(integration for integration in integrations if integration["provider"] == "alibaba")
    assert alibaba["status"] == "not_connected"
    assert alibaba["prompt_when"]

    update_response = client.put(
        "/account/integrations/alibaba",
        headers=IMPORTER_HEADERS,
        json={"status": "connected", "notes": "Connected by importer."},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == "connected"
    assert updated["last_verified_at"] is not None
    assert updated["notes"] == "Connected by importer."
