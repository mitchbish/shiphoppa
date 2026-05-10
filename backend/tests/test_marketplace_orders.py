from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def _booking_payload() -> dict:
    return {
        "importer_company_name": "Acme",
        "importer_contact_name": "Sam",
        "importer_email": "marketplace@example.com",
        "supplier_name": "F",
        "supplier_city": "Foshan",
        "supplier_province": "Guangdong",
        "supplier_country": "China",
        "delivery_city": "Sydney",
        "delivery_postcode": "2000",
        "delivery_country": "Australia",
        "cargo_description": "x",
        "cargo_category": "homewares",
        "cbm_estimate": 18,
        "weight_kg_estimate": 3200,
        "cargo_ready_date_earliest": date.today().isoformat(),
        "cargo_ready_date_latest": (date.today() + timedelta(days=4)).isoformat(),
        "service_level": "standard",
    }


def _new_booking(client: TestClient) -> dict:
    response = client.post("/bookings", headers=IMPORTER_HEADERS, json=_booking_payload())
    assert response.status_code == 201
    return response.json()["booking"]


def test_post_marketplace_order_returns_record_with_alibaba_provider() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)

    response = client.post(
        "/marketplace-orders",
        headers=IMPORTER_HEADERS,
        json={
            "marketplace": "alibaba",
            "booking_id": booking["id"],
            "external_order_id": "ALI-789",
            "trade_assurance_status": "covered",
            "supplier_profile_url": "https://supplier.example/profile",
            "agreed_terms_snapshot": "FOB Shenzhen, 30% deposit, 70% balance before shipment",
            "sync_method": "email_forward",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["marketplace"] == "alibaba"
    assert body["booking_id"] == booking["id"]
    assert body["external_order_id"] == "ALI-789"
    assert body["sync_method"] == "email_forward"
    assert body["last_synced_at"] is not None


def test_post_marketplace_order_supports_1688_provider() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.post(
        "/marketplace-orders",
        headers=IMPORTER_HEADERS,
        json={"marketplace": "1688", "external_order_id": "1688-abc"},
    )
    assert response.status_code == 201
    assert response.json()["marketplace"] == "1688"


def test_post_marketplace_order_404_for_unknown_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.post(
        "/marketplace-orders",
        headers=IMPORTER_HEADERS,
        json={"marketplace": "alibaba", "booking_id": "UNKNOWN"},
    )
    assert response.status_code == 404


def test_get_marketplace_orders_filters_by_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking_a = _new_booking(client)
    booking_b = client.post(
        "/bookings",
        headers=IMPORTER_HEADERS,
        json={**_booking_payload(), "importer_email": "marketplace-b@example.com"},
    ).json()["booking"]

    client.post(
        "/marketplace-orders",
        headers=IMPORTER_HEADERS,
        json={"marketplace": "alibaba", "booking_id": booking_a["id"]},
    )
    client.post(
        "/marketplace-orders",
        headers=IMPORTER_HEADERS,
        json={"marketplace": "made_in_china", "booking_id": booking_b["id"]},
    )

    response = client.get(
        f"/marketplace-orders?booking_id={booking_a['id']}",
        headers=IMPORTER_HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["marketplace"] == "alibaba"


def test_post_marketplace_order_writes_audit_event() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    client.post(
        "/marketplace-orders",
        headers=IMPORTER_HEADERS,
        json={"marketplace": "global_sources", "booking_id": booking["id"]},
    )
    audits = [
        e
        for e in store.audit_events.values()
        if e.event_type == "marketplace_order_recorded"
    ]
    assert len(audits) == 1
    assert audits[0].metadata["marketplace"] == "global_sources"


def test_get_marketplace_orders_returns_newest_first() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    first = client.post(
        "/marketplace-orders",
        headers=IMPORTER_HEADERS,
        json={"marketplace": "alibaba", "booking_id": booking["id"], "external_order_id": "first"},
    ).json()
    second = client.post(
        "/marketplace-orders",
        headers=IMPORTER_HEADERS,
        json={"marketplace": "made_in_china", "booking_id": booking["id"], "external_order_id": "second"},
    ).json()

    response = client.get(
        f"/marketplace-orders?booking_id={booking['id']}",
        headers=IMPORTER_HEADERS,
    )
    body = response.json()
    assert body[0]["id"] == second["id"]
    assert body[1]["id"] == first["id"]
