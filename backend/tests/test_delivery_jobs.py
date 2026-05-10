from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def _booking_payload() -> dict:
    return {
        "importer_company_name": "Acme",
        "importer_contact_name": "Sam",
        "importer_email": "djob@example.com",
        "supplier_name": "Foshan Light",
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


def test_create_delivery_job_returns_booked_record() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)

    response = client.post(
        f"/bookings/{booking['id']}/delivery-jobs",
        headers=IMPORTER_HEADERS,
        json={
            "mode": "local_truck",
            "pickup_address": "Port Botany",
            "delivery_address": "1 Main St, Sydney",
            "equipment_required": ["tail_lift"],
            "quote_amount_usd": 320.0,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["booking_id"] == booking["id"]
    assert body["mode"] == "local_truck"
    assert body["status"] == "booked"
    assert body["quote_amount_usd"] == 320.0
    assert body["equipment_required"] == ["tail_lift"]


def test_create_delivery_job_404_for_unknown_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.post(
        "/bookings/UNKNOWN/delivery-jobs",
        headers=IMPORTER_HEADERS,
        json={"mode": "courier"},
    )
    assert response.status_code == 404


def test_list_delivery_jobs_returns_only_booking_jobs() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking_a = _new_booking(client)
    booking_b_resp = client.post(
        "/bookings",
        headers=IMPORTER_HEADERS,
        json={**_booking_payload(), "importer_email": "djob-b@example.com"},
    )
    booking_b = booking_b_resp.json()["booking"]

    client.post(
        f"/bookings/{booking_a['id']}/delivery-jobs",
        headers=IMPORTER_HEADERS,
        json={"mode": "local_truck"},
    )
    client.post(
        f"/bookings/{booking_a['id']}/delivery-jobs",
        headers=IMPORTER_HEADERS,
        json={"mode": "courier"},
    )
    client.post(
        f"/bookings/{booking_b['id']}/delivery-jobs",
        headers=IMPORTER_HEADERS,
        json={"mode": "pallet_freight"},
    )

    response = client.get(f"/bookings/{booking_a['id']}/delivery-jobs", headers=IMPORTER_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert all(item["booking_id"] == booking_a["id"] for item in body)


def test_patch_delivery_job_updates_fields_and_records_audit() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    create_resp = client.post(
        f"/bookings/{booking['id']}/delivery-jobs",
        headers=IMPORTER_HEADERS,
        json={"mode": "local_truck"},
    )
    job_id = create_resp.json()["id"]

    response = client.patch(
        f"/delivery-jobs/{job_id}",
        headers=IMPORTER_HEADERS,
        json={"status": "picked_up", "notes": "Driver collected"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "picked_up"
    assert body["notes"] == "Driver collected"

    audit_events = [
        e
        for e in store.audit_events.values()
        if e.entity_type == "delivery_job" and e.entity_id == job_id
    ]
    statuses = sorted(e.event_type for e in audit_events)
    assert "delivery_job_created" in statuses
    assert "delivery_job_status_changed" in statuses


def test_patch_delivery_job_returns_404_for_unknown_id() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.patch(
        "/delivery-jobs/UNKNOWN",
        headers=IMPORTER_HEADERS,
        json={"status": "delivered"},
    )
    assert response.status_code == 404


def test_patch_delivery_job_to_delivered_records_pod_document() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    job_id = client.post(
        f"/bookings/{booking['id']}/delivery-jobs",
        headers=IMPORTER_HEADERS,
        json={"mode": "courier"},
    ).json()["id"]

    response = client.patch(
        f"/delivery-jobs/{job_id}",
        headers=IMPORTER_HEADERS,
        json={"status": "delivered", "pod_document_id": "DOC-9999"},
    )
    assert response.status_code == 200
    assert response.json()["pod_document_id"] == "DOC-9999"
    assert response.json()["status"] == "delivered"


def test_patch_delivery_job_no_status_change_records_generic_audit_event() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    job_id = client.post(
        f"/bookings/{booking['id']}/delivery-jobs",
        headers=IMPORTER_HEADERS,
        json={"mode": "courier"},
    ).json()["id"]

    response = client.patch(
        f"/delivery-jobs/{job_id}",
        headers=IMPORTER_HEADERS,
        json={"notes": "Customer prefers Tuesday delivery"},
    )
    assert response.status_code == 200
    audit_types = [
        e.event_type
        for e in store.audit_events.values()
        if e.entity_type == "delivery_job" and e.entity_id == job_id
    ]
    assert "delivery_job_updated" in audit_types
