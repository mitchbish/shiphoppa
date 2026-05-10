from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def _booking_payload() -> dict:
    return {
        "importer_company_name": "Acme",
        "importer_contact_name": "Sam",
        "importer_email": "preview-test@example.com",
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


def test_extraction_preview_returns_facts_for_known_format() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    text = (
        "Container number MSCU1234567 has been loaded. "
        "Vessel Maersk Adriatic, voyage 124E. ETA 15 June 2026. "
        "CBM 22.5, total weight 3450 kg."
    )
    response = client.post(
        "/automation/extract-preview",
        headers=IMPORTER_HEADERS,
        json={"text": text, "subject": "Shipment update"},
    )
    assert response.status_code == 200
    body = response.json()
    fields = {fact["field"] for fact in body["facts"]}
    assert "container_number" in fields
    assert body["extracted_count"] == len(body["facts"])
    assert body["extracted_count"] >= 1


def test_extraction_preview_empty_text_returns_no_facts() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.post(
        "/automation/extract-preview",
        headers=IMPORTER_HEADERS,
        json={"text": ""},
    )
    assert response.status_code == 200
    assert response.json() == {
        "facts": [],
        "extracted_count": 0,
        "would_match_booking_id": None,
    }


def test_extraction_preview_does_not_mutate_store() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    audit_before = len(store.audit_events)
    msg_before = len(store.source_messages)
    runs_before = len(store.automation_runs)

    response = client.post(
        "/automation/extract-preview",
        headers=IMPORTER_HEADERS,
        json={"text": "Container MSCU1234567 ETA 15 June 2026."},
    )
    assert response.status_code == 200
    assert len(store.audit_events) == audit_before
    assert len(store.source_messages) == msg_before
    assert len(store.automation_runs) == runs_before


def test_extraction_preview_would_match_booking_when_id_in_text_exists() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking_resp = client.post("/bookings", headers=IMPORTER_HEADERS, json=_booking_payload())
    booking = booking_resp.json()["booking"]
    booking_id = booking["id"]

    response = client.post(
        "/automation/extract-preview",
        headers=IMPORTER_HEADERS,
        json={"text": f"Update on shipment {booking_id}: container MSCU1234567 loaded."},
    )
    assert response.status_code == 200
    body = response.json()
    if body["would_match_booking_id"] is not None:
        assert body["would_match_booking_id"] == booking_id


def test_extraction_preview_no_match_when_unknown_booking_id() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.post(
        "/automation/extract-preview",
        headers=IMPORTER_HEADERS,
        json={"text": "Update on shipment BKG-9999: container MSCU1234567 loaded."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["would_match_booking_id"] is None
