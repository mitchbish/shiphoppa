from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def booking_payload() -> dict:
    return {
        "importer_company_name": "Bayside Build Co.",
        "importer_contact_name": "Alex Morgan",
        "importer_email": "alex.api@example.com",
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


def test_booking_to_carrier_commit_api_flow() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    match_response = client.post(
        "/bookings",
        headers={**IMPORTER_HEADERS, "Idempotency-Key": "booking-flow-1"},
        json=booking_payload(),
    )
    assert match_response.status_code == 201
    match_data = match_response.json()
    assert match_data["container"]["id"] == "CON-FOUNDING"
    assert match_data["booking"]["total_cost_usd"] > 0
    assert match_data["booking"]["delivery_mode"] == "ship_hoppa_pickup"
    assert match_data["booking"]["warehouse_receipt_cutoff"]
    assert match_data["booking"]["latest_supplier_ready_date"]
    assert match_data["booking"]["pickup_fee_usd"] == 95
    assert match_data["container"]["sailing_source_confidence"] == "estimated"

    booking_id = match_data["booking"]["id"]
    confirm_response = client.post(f"/bookings/{booking_id}/confirm", headers=IMPORTER_HEADERS)
    assert confirm_response.status_code == 200
    assert "Ship Hoppa will coordinate pickup" in confirm_response.json()["supplier_instructions"]

    container_id = match_data["container"]["id"]
    options_response = client.get(f"/containers/{container_id}/carrier-options", headers=ADMIN_HEADERS)
    assert options_response.status_code == 200
    options = options_response.json()
    assert len(options) >= 1

    commit_response = client.post(
        f"/containers/{container_id}/commit",
        headers={**ADMIN_HEADERS, "Idempotency-Key": "commit-flow-1"},
        json={
            "carrier_service_id": options[0]["service_id"],
            "sailing_date": options[0]["sailing_date"],
        },
    )
    assert commit_response.status_code == 200
    assert commit_response.json()["released"] is True

    summary_response = client.get("/summary", headers=ADMIN_HEADERS)
    assert summary_response.status_code == 200
    assert summary_response.json()["committed_containers"] == 1
    assert summary_response.json()["audit_events"]


def test_self_delivery_confirmation_returns_warehouse_responsibility_terms() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    payload = {
        **booking_payload(),
        "importer_email": "self.delivery@example.com",
        "supplier_city": "Foshan",
        "delivery_mode": "self_delivery",
    }

    match_response = client.post("/bookings", headers=IMPORTER_HEADERS, json=payload)
    assert match_response.status_code == 201
    data = match_response.json()
    assert data["booking"]["pickup_fee_usd"] == 0

    confirm_response = client.post(f"/bookings/{data['booking']['id']}/confirm", headers=IMPORTER_HEADERS)
    assert confirm_response.status_code == 200
    instructions = confirm_response.json()["supplier_instructions"]
    assert "Ship Hoppa Foshan Warehouse" in instructions
    assert "responsible until warehouse receipt scan" in instructions


def test_admin_review_booking_cannot_be_confirmed_by_importer() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    payload = {
        **booking_payload(),
        "importer_email": "review.api@example.com",
        "supplier_city": "Huizhou",
        "supplier_province": "Guangdong",
    }

    match_response = client.post("/bookings", headers=IMPORTER_HEADERS, json=payload)
    assert match_response.status_code == 201
    data = match_response.json()
    assert data["booking"]["feasibility_status"] == "admin_review"

    confirm_response = client.post(f"/bookings/{data['booking']['id']}/confirm", headers=IMPORTER_HEADERS)
    assert confirm_response.status_code == 409
    assert "operations review" in confirm_response.json()["detail"]


def test_admin_endpoints_require_admin_role() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    assert client.get("/summary").status_code == 401
    assert client.get("/summary", headers=IMPORTER_HEADERS).status_code == 403
    assert client.get("/summary", headers=ADMIN_HEADERS).status_code == 200


def test_idempotency_prevents_duplicate_booking_submit() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    headers = {**IMPORTER_HEADERS, "Idempotency-Key": "same-booking"}

    first_response = client.post("/bookings", headers=headers, json=booking_payload())
    second_response = client.post("/bookings", headers=headers, json=booking_payload())

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json()["booking"]["id"] == second_response.json()["booking"]["id"]
    assert len(client.get("/bookings", headers=ADMIN_HEADERS).json()) == 2


def test_repeated_commit_has_no_duplicate_notifications() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    match_response = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload())
    container_id = match_response.json()["container"]["id"]
    options = client.get(f"/containers/{container_id}/carrier-options", headers=ADMIN_HEADERS).json()
    payload = {"carrier_service_id": options[0]["service_id"], "sailing_date": options[0]["sailing_date"]}

    first = client.post(f"/containers/{container_id}/commit", headers=ADMIN_HEADERS, json=payload)
    second = client.post(f"/containers/{container_id}/commit", headers=ADMIN_HEADERS, json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["reasons"] == ["Already committed; no side effects repeated"]
    notifications = client.get("/notifications", headers=ADMIN_HEADERS).json()
    release_notifications = [item for item in notifications if item["trigger"] == "container_released"]
    assert len(release_notifications) == 2
