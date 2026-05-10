from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def booking_payload(email: str = "trucker-test@example.com") -> dict:
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


def create_booking(client: TestClient, email: str = "trucker-test@example.com") -> dict:
    response = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload(email))
    assert response.status_code == 201
    return response.json()["booking"]


def clear_holds(client: TestClient, booking_id: str) -> None:
    """Resolve all release holds on a booking via the same path the importer uses."""
    missing = client.get(f"/bookings/{booking_id}/checklist", headers=IMPORTER_HEADERS).json()["missing_document_types"]
    for document_type in missing:
        doc = client.post(
            f"/bookings/{booking_id}/documents",
            headers=IMPORTER_HEADERS,
            json={"document_type": document_type, "file_name": f"{document_type}.pdf"},
        ).json()
        client.post(f"/documents/{doc['id']}/approve", headers=ADMIN_HEADERS, json={"reason": "Approved"})
    invoice = client.get(f"/bookings/{booking_id}/invoice", headers=IMPORTER_HEADERS).json()
    client.post(f"/invoices/{invoice['id']}/mark-paid", headers=ADMIN_HEADERS)
    client.put(
        f"/bookings/{booking_id}/customs-profile",
        headers=ADMIN_HEADERS,
        json={"customs_status": "cleared", "goods_value_usd": 12000},
    )


def test_trucker_link_is_idempotent_per_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "trucker-idempotent@example.com")

    first = client.post("/trucker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]})
    second = client.post("/trucker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["token"] == second.json()["token"]


def test_trucker_link_for_unknown_booking_returns_404() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post("/trucker-links", headers=ADMIN_HEADERS, json={"booking_id": "B-9999"})
    assert response.status_code == 404


def test_expired_trucker_token_rejected() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "trucker-expired@example.com")

    link_response = client.post("/trucker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]})
    token = link_response.json()["token"]

    link = next(item for item in store.trucker_links.values() if item.token == token)
    link.expires_at = datetime.utcnow() - timedelta(days=1)
    store.trucker_links[link.id] = link

    response = client.get(f"/trucker/{token}")
    assert response.status_code == 404


def test_trucker_portal_returns_delivery_profile_and_holds() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "trucker-portal@example.com")

    link = client.post("/trucker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()
    response = client.get(f"/trucker/{link['token']}")
    assert response.status_code == 200
    body = response.json()
    assert body["booking"]["id"] == booking["id"]
    assert body["booking"]["destination_address"]
    assert isinstance(body["holds"], list)
    assert "release_status" in body
    assert isinstance(body["can_deliver"], bool)


def test_trucker_status_update_creates_event_and_audit() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "trucker-status@example.com")
    link = client.post("/trucker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()

    response = client.post(
        f"/trucker/{link['token']}/status",
        json={"stage": "picked_up", "notes": "Loaded onto truck at Patrick terminal."},
    )
    assert response.status_code == 200
    body = response.json()
    assert any(event["stage"] == "picked_up" and event["source_name"] == "Trucker portal" for event in body["events"])
    audit = [
        evt for evt in store.audit_events.values()
        if evt.actor_id == "trucker-portal" and evt.event_type == "trucker_status_update"
    ]
    assert len(audit) == 1


def test_trucker_cannot_mark_delivered_while_release_blocked() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "trucker-blocked@example.com")
    link = client.post("/trucker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()

    response = client.post(
        f"/trucker/{link['token']}/status",
        json={"stage": "delivered"},
    )
    assert response.status_code == 400
    assert "release" in response.json()["detail"].lower()


def test_trucker_can_mark_delivered_when_release_clear() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "trucker-delivered@example.com")
    link = client.post("/trucker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()
    clear_holds(client, booking["id"])

    response = client.post(
        f"/trucker/{link['token']}/status",
        json={"stage": "delivered", "notes": "Delivered to receiving dock."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["booking"]["booking_status"] == "delivered"


def test_trucker_status_whitelisted_stages_only() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "trucker-whitelist@example.com")
    link = client.post("/trucker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()

    response = client.post(
        f"/trucker/{link['token']}/status",
        json={"stage": "customs_cleared"},
    )
    assert response.status_code == 400


def test_trucker_pod_upload_records_trucker_portal_origin() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "trucker-pod@example.com")
    link = client.post("/trucker-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()

    response = client.post(
        f"/trucker/{link['token']}/pod",
        json={"document_type": "delivery_order", "file_name": "pod-signed.pdf"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["uploaded_by_id"] == "trucker-portal"
    assert body["booking_id"] == booking["id"]
