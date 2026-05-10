from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def booking_payload(email: str = "broker-test@example.com") -> dict:
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
        "cargo_description": "flat-pack vanities and bathroom cabinets",
        "cargo_category": "furniture",
        "cbm_estimate": 20,
        "weight_kg_estimate": 3800,
        "cargo_ready_date_earliest": date.today().isoformat(),
        "cargo_ready_date_latest": (date.today() + timedelta(days=5)).isoformat(),
        "service_level": "standard",
    }


def create_booking(client: TestClient, email: str = "broker-test@example.com") -> dict:
    response = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload(email))
    assert response.status_code == 201
    return response.json()["booking"]


def test_broker_link_is_idempotent_per_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "broker-idempotent@example.com")

    first = client.post("/broker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]})
    second = client.post("/broker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["token"] == second.json()["token"]


def test_broker_link_for_unknown_booking_returns_404() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post("/broker-links", headers=ADMIN_HEADERS, json={"booking_id": "B-9999"})
    assert response.status_code == 404


def test_expired_broker_token_rejected() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "broker-expired@example.com")

    link_response = client.post("/broker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]})
    token = link_response.json()["token"]

    link = next(item for item in store.broker_links.values() if item.token == token)
    link.expires_at = datetime.utcnow() - timedelta(days=1)
    store.broker_links[link.id] = link

    portal = client.get(f"/broker/{token}")
    assert portal.status_code == 404


def test_broker_portal_returns_customs_summary_and_importer_abn() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "broker-portal@example.com")

    client.put(
        f"/bookings/{booking['id']}/customs-profile",
        headers=ADMIN_HEADERS,
        json={"importer_abn": "12 345 678 901", "hs_code": "9403.60"},
    )

    link = client.post("/broker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()
    portal = client.get(f"/broker/{link['token']}")
    assert portal.status_code == 200
    body = portal.json()
    assert body["booking"]["id"] == booking["id"]
    assert body["booking"]["importer_abn"] == "12 345 678 901"
    assert body["customs"]["hs_code"] == "9403.60"
    assert body["customs"]["customs_status"] == "documents_required"
    assert isinstance(body["holds"], list)
    assert isinstance(body["events"], list)


def test_broker_clearance_update_writes_audit_with_portal_source() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "broker-clearance@example.com")
    link = client.post("/broker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()

    audit_before = len(store.audit_events)
    response = client.post(
        f"/broker/{link['token']}/clearance",
        json={
            "customs_status": "submitted",
            "customs_entry_number": "E-12345",
            "broker_notes": "Lodged with ABF this morning.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["customs"]["customs_status"] == "submitted"
    assert body["customs"]["customs_entry_number"] == "E-12345"
    assert body["customs"]["broker_notes"] == "Lodged with ABF this morning."
    assert len(store.audit_events) > audit_before
    broker_events = [
        evt for evt in store.audit_events.values()
        if evt.actor_id == "broker-portal" and evt.event_type == "broker_clearance_update"
    ]
    assert len(broker_events) == 1


def test_broker_rejects_held_status() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "broker-held@example.com")
    link = client.post("/broker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()

    response = client.post(
        f"/broker/{link['token']}/clearance",
        json={"customs_status": "held"},
    )
    assert response.status_code == 400


def test_broker_doc_upload_records_broker_portal_origin() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "broker-doc@example.com")
    link = client.post("/broker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()

    response = client.post(
        f"/broker/{link['token']}/documents",
        json={"document_type": "house_bill", "file_name": "broker-customs-decl.pdf"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["uploaded_by_id"] == "broker-portal"
    assert body["booking_id"] == booking["id"]


def test_cleared_releases_only_customs_hold_payment_hold_remains() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "broker-holds@example.com")
    booking_id = booking["id"]

    invoice = client.get(f"/bookings/{booking_id}/invoice", headers=IMPORTER_HEADERS).json()
    assert invoice["status"] == "issued"

    release = client.get(f"/bookings/{booking_id}/release-status", headers=IMPORTER_HEADERS).json()
    hold_types = {hold["hold_type"] for hold in release["holds"]}
    assert "customs_hold" in hold_types
    assert "unpaid_invoice" in hold_types

    link = client.post("/broker-links", headers=ADMIN_HEADERS, json={"booking_id": booking_id}).json()
    response = client.post(
        f"/broker/{link['token']}/clearance",
        json={"customs_status": "cleared", "customs_entry_number": "E-99001"},
    )
    assert response.status_code == 200
    cleared_holds = {hold["hold_type"] for hold in response.json()["holds"]}
    assert "customs_hold" not in cleared_holds
    assert "unpaid_invoice" in cleared_holds
