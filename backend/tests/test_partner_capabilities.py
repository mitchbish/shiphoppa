from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def _booking_payload() -> dict:
    return {
        "importer_company_name": "Acme",
        "importer_contact_name": "Sam",
        "importer_email": "partner@example.com",
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


def _new_partner(client: TestClient, name: str = "Best Trucking") -> dict:
    response = client.post(
        "/partners",
        headers=ADMIN_HEADERS,
        json={
            "partner_type": "trucker",
            "name": name,
            "contact_email": "ops@besttrucking.com",
            "preferred_channel": "email",
        },
    )
    assert response.status_code == 201
    return response.json()


def _new_booking(client: TestClient) -> dict:
    response = client.post("/bookings", headers=IMPORTER_HEADERS, json=_booking_payload())
    assert response.status_code == 201
    return response.json()["booking"]


def test_create_partner_profile_returns_active_record() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    body = _new_partner(client)
    assert body["name"] == "Best Trucking"
    assert body["partner_type"] == "trucker"
    assert body["active"] is True


def test_list_partners_returns_newest_first() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    _new_partner(client, "Older")
    _new_partner(client, "Newer")
    response = client.get("/partners", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["name"] == "Newer"


def test_patch_partner_marks_inactive_and_updates_fields() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    partner = _new_partner(client)
    response = client.patch(
        f"/partners/{partner['id']}",
        headers=ADMIN_HEADERS,
        json={"active": False, "notes": "Paused for review"},
    )
    assert response.status_code == 200
    assert response.json()["active"] is False
    assert response.json()["notes"] == "Paused for review"


def test_create_partner_capability_returns_record_and_404_for_unknown_partner() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    partner = _new_partner(client)

    response = client.post(
        f"/partners/{partner['id']}/capabilities",
        headers=ADMIN_HEADERS,
        json={
            "capability_type": "local_delivery",
            "service_regions": ["Sydney", "Melbourne"],
            "equipment": ["tail_lift"],
            "average_response_hours": 4.5,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["partner_id"] == partner["id"]
    assert body["service_regions"] == ["Sydney", "Melbourne"]

    bad = client.post(
        "/partners/UNKNOWN/capabilities",
        headers=ADMIN_HEADERS,
        json={"capability_type": "local_delivery"},
    )
    assert bad.status_code == 404


def test_get_partner_capabilities_filters_by_partner() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    a = _new_partner(client, "A")
    b = _new_partner(client, "B")
    client.post(
        f"/partners/{a['id']}/capabilities",
        headers=ADMIN_HEADERS,
        json={"capability_type": "local_delivery"},
    )
    client.post(
        f"/partners/{b['id']}/capabilities",
        headers=ADMIN_HEADERS,
        json={"capability_type": "warehouse_receipt"},
    )
    response = client.get(f"/partners/{a['id']}/capabilities", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["capability_type"] == "local_delivery"


def test_patch_partner_capability_updates_fields() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    partner = _new_partner(client)
    capability_id = client.post(
        f"/partners/{partner['id']}/capabilities",
        headers=ADMIN_HEADERS,
        json={"capability_type": "local_delivery"},
    ).json()["id"]

    response = client.patch(
        f"/partner-capabilities/{capability_id}",
        headers=ADMIN_HEADERS,
        json={"average_response_hours": 2.0, "active": False},
    )
    assert response.status_code == 200
    assert response.json()["average_response_hours"] == 2.0
    assert response.json()["active"] is False


def test_create_contingency_option_returns_proposed_status() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)

    response = client.post(
        f"/bookings/{booking['id']}/contingency-options",
        headers=ADMIN_HEADERS,
        json={
            "issue_type": "eta_slip",
            "option_type": "book_next_sailing",
            "plain_language_summary": "Carrier ETA slipped 5 days; better sailing departs Friday",
            "cost_impact_usd": 250.0,
            "time_impact_days": -3.0,
            "risk_level": "medium",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["booking_id"] == booking["id"]
    assert body["status"] == "proposed"
    assert body["risk_level"] == "medium"


def test_patch_contingency_option_status_records_audit() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    option_id = client.post(
        f"/bookings/{booking['id']}/contingency-options",
        headers=ADMIN_HEADERS,
        json={
            "issue_type": "cutoff_miss",
            "option_type": "book_next_sailing",
            "plain_language_summary": "Missed cutoff; rebook next sailing",
        },
    ).json()["id"]

    response = client.patch(
        f"/contingency-options/{option_id}",
        headers=ADMIN_HEADERS,
        json={"status": "approved"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    audit_types = [
        e.event_type
        for e in store.audit_events.values()
        if e.entity_type == "contingency_option" and e.entity_id == option_id
    ]
    assert "contingency_option_status_changed" in audit_types


def test_list_contingency_options_filters_by_booking_and_404_for_unknown() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    client.post(
        f"/bookings/{booking['id']}/contingency-options",
        headers=ADMIN_HEADERS,
        json={
            "issue_type": "production_delay",
            "option_type": "hold_for_review",
            "plain_language_summary": "Supplier flagged 7-day delay",
        },
    )
    response = client.get(
        f"/bookings/{booking['id']}/contingency-options",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert len(response.json()) == 1

    bad = client.get(
        "/bookings/UNKNOWN/contingency-options",
        headers=ADMIN_HEADERS,
    )
    assert bad.status_code == 404
