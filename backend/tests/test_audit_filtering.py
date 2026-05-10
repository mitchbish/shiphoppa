from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def booking_payload(email: str = "audit-test@example.com") -> dict:
    return {
        "importer_company_name": "Bayside Build Co.",
        "importer_contact_name": "Alex Morgan",
        "importer_email": email,
        "supplier_name": "Dongguan Home Furnishings",
        "supplier_city": "Dongguan",
        "supplier_province": "Guangdong",
        "supplier_country": "China",
        "delivery_city": "Brisbane",
        "delivery_postcode": "4101",
        "delivery_country": "Australia",
        "cargo_description": "flat-pack furniture",
        "cargo_category": "furniture",
        "cbm_estimate": 20,
        "weight_kg_estimate": 3800,
        "cargo_ready_date_earliest": date.today().isoformat(),
        "cargo_ready_date_latest": (date.today() + timedelta(days=5)).isoformat(),
        "service_level": "standard",
    }


def test_audit_events_default_returns_recent_events() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload())

    response = client.get("/audit-events", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0
    # Sorted newest-first
    timestamps = [event["created_at"] for event in body]
    assert timestamps == sorted(timestamps, reverse=True)


def test_audit_events_filter_by_actor_id() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload()).json()["booking"]
    link = client.post("/broker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()
    client.post(
        f"/broker/{link['token']}/clearance",
        json={"customs_status": "submitted", "customs_entry_number": "E-1"},
    )

    response = client.get("/audit-events?actor_id=broker-portal", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    assert all(event["actor_id"] == "broker-portal" for event in body)


def test_audit_events_filter_by_event_type() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload())

    response = client.get("/audit-events?event_type=booking_submitted", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert all(event["event_type"] == "booking_submitted" for event in body)


def test_audit_events_filter_by_entity() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload()).json()["booking"]

    response = client.get(
        f"/audit-events?entity_type=booking&entity_id={booking['id']}",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert all(event["entity_type"] == "booking" and event["entity_id"] == booking["id"] for event in body)


def test_audit_events_limit_caps_results() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    # Create several bookings to generate many audit events.
    for index in range(3):
        payload = booking_payload(f"limit-{index}@example.com")
        client.post("/bookings", headers=IMPORTER_HEADERS, json=payload)

    response = client.get("/audit-events?limit=2", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_audit_events_filter_by_actor_role() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload())

    response = client.get("/audit-events?actor_role=admin", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert all(event["actor_role"] == "admin" for event in body)


def test_audit_events_no_filter_returns_all_under_default_limit() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    starting = len(store.audit_events)
    client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload())

    response = client.get("/audit-events", headers=ADMIN_HEADERS)
    body = response.json()
    assert len(body) >= len(store.audit_events) - starting
