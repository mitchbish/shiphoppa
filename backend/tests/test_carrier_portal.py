from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def booking_payload(email: str = "carrier-test@example.com") -> dict:
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


def create_booking_with_container(client: TestClient, email: str = "carrier-test@example.com") -> dict:
    response = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload(email))
    assert response.status_code == 201
    body = response.json()
    booking = body["booking"]
    container_id = body.get("container", {}).get("id") or booking.get("container_id")
    if not booking.get("container_id") and container_id:
        booking["container_id"] = container_id
    return booking


def test_carrier_link_is_idempotent_per_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking_with_container(client, "carrier-idempotent@example.com")

    first = client.post("/carrier-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]})
    second = client.post("/carrier-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["token"] == second.json()["token"]


def test_carrier_link_for_unknown_booking_returns_404() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post("/carrier-links", headers=ADMIN_HEADERS, json={"booking_id": "B-9999"})
    assert response.status_code == 404


def test_expired_carrier_token_rejected() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking_with_container(client, "carrier-expired@example.com")

    link_response = client.post("/carrier-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]})
    token = link_response.json()["token"]

    link = next(item for item in store.carrier_links.values() if item.token == token)
    link.expires_at = datetime.utcnow() - timedelta(days=1)
    store.carrier_links[link.id] = link

    portal = client.get(f"/carrier/{token}")
    assert portal.status_code == 404


def test_carrier_portal_returns_container_eta() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking_with_container(client, "carrier-portal@example.com")

    link = client.post("/carrier-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()
    portal = client.get(f"/carrier/{link['token']}")
    assert portal.status_code == 200
    body = portal.json()
    assert body["booking"]["id"] == booking["id"]
    assert body["booking"]["container_id"] is not None
    assert body["booking"]["target_sailing_date"] is not None


def test_carrier_eta_update_triggers_existing_eta_automation() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking_with_container(client, "carrier-eta@example.com")
    container_id = booking["container_id"]

    # Set baseline so a 4-day delta will trigger the approval threshold.
    container = store.containers[container_id]
    baseline = container.estimated_arrival or date.today() + timedelta(days=30)
    container.baseline_estimated_arrival = baseline
    store.containers[container_id] = container

    link = client.post("/carrier-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()
    new_eta = baseline + timedelta(days=4)
    response = client.post(
        f"/carrier/{link['token']}/eta",
        json={"estimated_arrival": new_eta.isoformat(), "note": "Typhoon delay."},
    )
    assert response.status_code == 200
    refreshed = response.json()
    assert refreshed["booking"]["estimated_arrival"] == new_eta.isoformat()

    sailing_approvals = [
        ar for ar in store.approval_requests.values()
        if ar.request_type == "accept_sailing_change" and ar.related_booking_id == booking["id"]
    ]
    assert len(sailing_approvals) == 1

    audit = [
        evt for evt in store.audit_events.values()
        if evt.actor_id == "carrier-portal" and evt.event_type == "carrier_eta_update"
    ]
    assert len(audit) == 1


def test_carrier_event_whitelisted_stages_only() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking_with_container(client, "carrier-event@example.com")
    link = client.post("/carrier-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()

    rejected = client.post(
        f"/carrier/{link['token']}/event",
        json={"stage": "customs_cleared"},
    )
    assert rejected.status_code == 400

    accepted = client.post(
        f"/carrier/{link['token']}/event",
        json={"stage": "departed", "notes": "Vessel departed Yantian."},
    )
    assert accepted.status_code == 200
    events = accepted.json()["events"]
    assert any(event["stage"] == "departed" and event["source_name"] == "Carrier portal" for event in events)


def test_carrier_eta_rejected_without_container() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking_with_container(client, "carrier-no-container@example.com")

    # Strip the container_id to simulate an early-stage booking.
    booking_record = store.bookings[booking["id"]]
    booking_record.container_id = None
    store.bookings[booking["id"]] = booking_record

    link = client.post("/carrier-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()
    response = client.post(
        f"/carrier/{link['token']}/eta",
        json={"estimated_arrival": (date.today() + timedelta(days=40)).isoformat()},
    )
    assert response.status_code == 400
    assert "container" in response.json()["detail"].lower()


def test_carrier_doc_upload_records_carrier_portal_origin() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking_with_container(client, "carrier-doc@example.com")
    link = client.post("/carrier-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]}).json()

    response = client.post(
        f"/carrier/{link['token']}/documents",
        json={"document_type": "house_bill", "file_name": "house-bl.pdf"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["uploaded_by_id"] == "carrier-portal"
    assert body["booking_id"] == booking["id"]
