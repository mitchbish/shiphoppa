from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store
from app.operations import create_supplier_link


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def _booking_payload() -> dict:
    return {
        "importer_company_name": "Acme Imports",
        "importer_contact_name": "Sam Trader",
        "importer_email": "preview@example.com",
        "supplier_name": "Foshan Light Co.",
        "supplier_city": "Foshan",
        "supplier_province": "Guangdong",
        "supplier_country": "China",
        "delivery_city": "Sydney",
        "delivery_postcode": "2000",
        "delivery_country": "Australia",
        "cargo_description": "lighting fixtures",
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


def test_supplier_preview_returns_portal_response_for_importer() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)

    response = client.get(f"/bookings/{booking['id']}/supplier-preview", headers=IMPORTER_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["booking"]["id"] == booking["id"]
    assert "supplier_instructions" in body
    assert "checklist" in body
    assert "events" in body


def test_supplier_preview_returns_404_for_unknown_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.get("/bookings/UNKNOWN/supplier-preview", headers=IMPORTER_HEADERS)
    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found"


def test_supplier_preview_does_not_create_or_mutate_supplier_links() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    initial_links = len(store.supplier_links)

    response = client.get(f"/bookings/{booking['id']}/supplier-preview", headers=IMPORTER_HEADERS)
    assert response.status_code == 200
    assert len(store.supplier_links) == initial_links


def test_supplier_preview_does_not_update_last_used_at_on_existing_link() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    link = create_supplier_link(store, booking["id"])
    assert link.last_used_at is None

    response = client.get(f"/bookings/{booking['id']}/supplier-preview", headers=IMPORTER_HEADERS)
    assert response.status_code == 200

    refreshed = store.supplier_links[link.id]
    assert refreshed.last_used_at is None


def test_supplier_preview_writes_audit_event() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)

    response = client.get(f"/bookings/{booking['id']}/supplier-preview", headers=ADMIN_HEADERS)
    assert response.status_code == 200

    matching = [
        e
        for e in store.audit_events.values()
        if e.event_type == "supplier_portal_previewed"
        and e.entity_type == "booking"
        and e.entity_id == booking["id"]
    ]
    assert len(matching) == 1
    assert "actor" in matching[0].metadata


def test_supplier_preview_response_keys_match_token_route() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    link = create_supplier_link(store, booking["id"])

    preview = client.get(f"/bookings/{booking['id']}/supplier-preview", headers=IMPORTER_HEADERS)
    via_token = client.get(f"/supplier/{link.token}")
    assert preview.status_code == 200
    assert via_token.status_code == 200
    assert sorted(preview.json().keys()) == sorted(via_token.json().keys())
