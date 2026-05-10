from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def booking_payload(email: str = "warehouse-test@example.com", delivery_mode: str = "self_delivery") -> dict:
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
        "delivery_mode": delivery_mode,
    }


def create_booking(client: TestClient, email: str = "warehouse-test@example.com", delivery_mode: str = "self_delivery") -> dict:
    response = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload(email, delivery_mode))
    assert response.status_code == 201
    return response.json()["booking"]


def test_warehouse_link_is_idempotent_per_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "warehouse-idempotent@example.com")

    first = client.post("/warehouse-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]})
    second = client.post("/warehouse-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["token"] == second.json()["token"]


def test_warehouse_link_for_unknown_booking_returns_404() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post("/warehouse-links", headers=ADMIN_HEADERS, json={"booking_id": "B-9999"})
    assert response.status_code == 404


def test_expired_warehouse_token_rejected() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "warehouse-expired@example.com")

    link_response = client.post("/warehouse-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]})
    token = link_response.json()["token"]

    link = next(item for item in store.warehouse_links.values() if item.token == token)
    link.expires_at = datetime.utcnow() - timedelta(days=1)
    store.warehouse_links[link.id] = link

    portal = client.get(f"/warehouse/{token}")
    assert portal.status_code == 404


def test_warehouse_portal_returns_expected_cargo_and_delivery_mode() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "warehouse-portal@example.com")

    link = client.post("/warehouse-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()
    portal = client.get(f"/warehouse/{link['token']}")
    assert portal.status_code == 200
    body = portal.json()
    assert body["booking"]["id"] == booking["id"]
    assert body["booking"]["delivery_mode"] == "self_delivery"
    assert body["booking"]["cbm_estimate"] == 20
    assert body["booking"]["weight_kg_estimate"] == 3800
    assert isinstance(body["events"], list)


def test_warehouse_receipt_creates_event_and_audit_with_warehouse_portal_source() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "warehouse-receipt@example.com")
    link = client.post("/warehouse-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()

    audit_before = len(store.audit_events)
    response = client.post(
        f"/warehouse/{link['token']}/receipt",
        json={"actual_cbm": 19.8, "actual_weight_kg": 3750, "notes": "All boxes intact."},
    )
    assert response.status_code == 200
    events = response.json()["events"]
    assert any(event["stage"] == "warehouse_received" and event["source_name"] == "Warehouse portal" for event in events)
    receipt_audit = [
        evt for evt in store.audit_events.values()
        if evt.actor_id == "warehouse-portal" and evt.event_type == "warehouse_receipt_confirmed"
    ]
    assert len(receipt_audit) == 1
    assert len(store.audit_events) > audit_before


def test_warehouse_receipt_with_cbm_variance_triggers_approval() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "warehouse-variance@example.com")
    link = client.post("/warehouse-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()

    approvals_before = len(store.approval_requests)
    response = client.post(
        f"/warehouse/{link['token']}/receipt",
        json={"actual_cbm": 24.5, "actual_weight_kg": 4200},
    )
    assert response.status_code == 200
    variance_approvals = [
        ar for ar in store.approval_requests.values()
        if ar.request_type == "approve_invoice_variance" and ar.related_booking_id == booking["id"]
    ]
    assert len(variance_approvals) == 1
    assert len(store.approval_requests) > approvals_before


def test_pickup_mode_booking_rejects_warehouse_receipt() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "warehouse-pickup@example.com", delivery_mode="ship_hoppa_pickup")
    link = client.post("/warehouse-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()

    response = client.post(
        f"/warehouse/{link['token']}/receipt",
        json={"actual_cbm": 19.8, "actual_weight_kg": 3750},
    )
    assert response.status_code == 400
    assert "ship hoppa pickup" in response.json()["detail"].lower()


def test_warehouse_doc_upload_records_warehouse_portal_origin() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "warehouse-doc@example.com")
    link = client.post("/warehouse-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()

    response = client.post(
        f"/warehouse/{link['token']}/documents",
        json={"document_type": "supplier_photos", "file_name": "warehouse-cargo-photo.pdf"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["uploaded_by_id"] == "warehouse-portal"
    assert body["booking_id"] == booking["id"]
