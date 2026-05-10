from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def _booking_payload() -> dict:
    return {
        "importer_company_name": "Acme",
        "importer_contact_name": "Sam",
        "importer_email": "ins@example.com",
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


def _new_booking(client: TestClient) -> dict:
    response = client.post("/bookings", headers=IMPORTER_HEADERS, json=_booking_payload())
    assert response.status_code == 201
    return response.json()["booking"]


def test_post_insurance_policy_creates_then_upserts_per_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)

    first = client.post(
        f"/bookings/{booking['id']}/insurance-policy",
        headers=ADMIN_HEADERS,
        json={"insurance_required": True, "insured_value": 12000.0, "currency": "USD", "provider": "Marsh"},
    )
    assert first.status_code == 201
    second = client.post(
        f"/bookings/{booking['id']}/insurance-policy",
        headers=ADMIN_HEADERS,
        json={"insurance_required": True, "insured_value": 12500.0, "currency": "USD", "provider": "Marsh", "premium_usd": 95.0},
    )
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["insured_value"] == 12500.0
    assert second.json()["premium_usd"] == 95.0


def test_get_insurance_policy_returns_404_when_missing() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    response = client.get(f"/bookings/{booking['id']}/insurance-policy", headers=IMPORTER_HEADERS)
    assert response.status_code == 404


def test_post_claim_returns_draft_status() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)

    response = client.post(
        f"/bookings/{booking['id']}/claims",
        headers=IMPORTER_HEADERS,
        json={"claim_type": "damage", "claim_amount_usd": 850.0, "notes": "Carton crushed in transit"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["claim_status"] == "draft"
    assert body["claim_type"] == "damage"
    assert body["claim_amount_usd"] == 850.0


def test_post_claim_404_for_unknown_booking_or_policy() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    bad_booking = client.post(
        "/bookings/UNKNOWN/claims",
        headers=IMPORTER_HEADERS,
        json={"claim_type": "damage", "claim_amount_usd": 1.0},
    )
    assert bad_booking.status_code == 404

    booking = _new_booking(client)
    bad_policy = client.post(
        f"/bookings/{booking['id']}/claims",
        headers=IMPORTER_HEADERS,
        json={
            "claim_type": "damage",
            "claim_amount_usd": 1.0,
            "insurance_policy_id": "INSPOL-9999",
        },
    )
    assert bad_policy.status_code == 404


def test_patch_claim_status_records_submitted_at_and_audit() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    claim_id = client.post(
        f"/bookings/{booking['id']}/claims",
        headers=IMPORTER_HEADERS,
        json={"claim_type": "damage", "claim_amount_usd": 500.0},
    ).json()["id"]

    response = client.patch(
        f"/claims/{claim_id}",
        headers=ADMIN_HEADERS,
        json={"claim_status": "submitted"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["claim_status"] == "submitted"
    assert body["submitted_at"] is not None
    assert body["resolved_at"] is None

    audits = [
        e
        for e in store.audit_events.values()
        if e.entity_type == "claim_record"
        and e.entity_id == claim_id
        and e.event_type == "claim_status_changed"
    ]
    assert audits


def test_patch_claim_to_paid_records_resolved_at() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    claim_id = client.post(
        f"/bookings/{booking['id']}/claims",
        headers=IMPORTER_HEADERS,
        json={"claim_type": "loss", "claim_amount_usd": 1200.0},
    ).json()["id"]

    response = client.patch(
        f"/claims/{claim_id}",
        headers=ADMIN_HEADERS,
        json={"claim_status": "paid", "recovery_amount_usd": 1000.0},
    )
    assert response.status_code == 200
    assert response.json()["claim_status"] == "paid"
    assert response.json()["resolved_at"] is not None
    assert response.json()["recovery_amount_usd"] == 1000.0


def test_get_claims_filters_by_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking_a = _new_booking(client)
    booking_b = client.post(
        "/bookings",
        headers=IMPORTER_HEADERS,
        json={**_booking_payload(), "importer_email": "ins-b@example.com"},
    ).json()["booking"]

    client.post(
        f"/bookings/{booking_a['id']}/claims",
        headers=IMPORTER_HEADERS,
        json={"claim_type": "damage", "claim_amount_usd": 100.0},
    )
    client.post(
        f"/bookings/{booking_b['id']}/claims",
        headers=IMPORTER_HEADERS,
        json={"claim_type": "shortage", "claim_amount_usd": 50.0},
    )

    response = client.get(f"/bookings/{booking_a['id']}/claims", headers=IMPORTER_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["claim_type"] == "damage"
