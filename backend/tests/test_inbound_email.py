from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


INBOUND_HEADERS = {"Authorization": "Bearer shiphoppa-inbound-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def booking_payload(email: str = "inbound-test@example.com") -> dict:
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


def create_booking(client: TestClient, email: str = "inbound-test@example.com") -> dict:
    response = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload(email))
    assert response.status_code == 201
    return response.json()["booking"]


def test_inbound_email_without_token_returns_401() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post("/inbound/email", json={"from": {"email": "x@example.com"}, "subject": "test"})
    assert response.status_code == 401


def test_inbound_email_with_invalid_token_returns_401() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post(
        "/inbound/email",
        headers={"Authorization": "Bearer wrong-token"},
        json={"from": {"email": "x@example.com"}, "subject": "test"},
    )
    assert response.status_code == 401


def test_inbound_email_resend_shape_creates_source_message() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post(
        "/inbound/email",
        headers=INBOUND_HEADERS,
        json={
            "from": {"email": "supplier@example.com", "name": "Supplier Co"},
            "to": [{"email": "imports@shiphoppa.au", "name": "Imports"}],
            "subject": "Pro forma invoice for July order",
            "text": "Please find attached our pro forma invoice for the July shipment.",
            "attachments": [{"filename": "proforma.pdf"}],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["from_address"] == "supplier@example.com"
    assert body["subject"] == "Pro forma invoice for July order"
    assert "pro forma invoice" in body["body"]
    assert body["source_type"] == "forwarded_email"
    assert body["id"] in store.source_messages
    assert "proforma.pdf" in body["attachments"]


def test_inbound_email_mailgun_shape_creates_source_message() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post(
        "/inbound/email",
        headers=INBOUND_HEADERS,
        json={
            "sender": "factory@example.cn",
            "recipient": "imports@shiphoppa.au",
            "subject": "Production milestone update",
            "body-plain": "We finished QC checks today. Shipment ready Friday.",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["from_address"] == "factory@example.cn"
    assert "QC checks" in body["body"]
    assert body["to_addresses"] == ["imports@shiphoppa.au"]


def test_inbound_email_matches_to_existing_booking_by_id_in_body() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "inbound-match@example.com")

    response = client.post(
        "/inbound/email",
        headers=INBOUND_HEADERS,
        json={
            "from": {"email": "factory@example.cn"},
            "to": [{"email": "imports@shiphoppa.au"}],
            "subject": f"Update on {booking['id']}",
            "text": f"Hi team, an update on shipment {booking['id']}: cargo ready next week.",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["matched_shipment_id"] == booking["id"]


def test_inbound_email_html_only_body_uses_html_field() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post(
        "/inbound/email",
        headers=INBOUND_HEADERS,
        json={
            "from": {"email": "supplier@example.com"},
            "subject": "HTML-only update",
            "html": "<p>Production update with details.</p>",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "Production update" in body["body"]


def test_inbound_email_without_sender_returns_422() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post(
        "/inbound/email",
        headers=INBOUND_HEADERS,
        json={"subject": "no sender"},
    )
    assert response.status_code == 422
