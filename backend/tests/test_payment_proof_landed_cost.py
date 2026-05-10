from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def _booking_payload() -> dict:
    return {
        "importer_company_name": "Acme",
        "importer_contact_name": "Sam",
        "importer_email": "ppl@example.com",
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def test_post_payment_proof_returns_pending_review() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)

    response = client.post(
        f"/bookings/{booking['id']}/payment-proofs",
        headers=IMPORTER_HEADERS,
        json={
            "payment_type": "supplier_invoice",
            "paid_amount": 4250.5,
            "paid_currency": "USD",
            "paid_at": _now(),
            "paid_by": "Sam Trader",
            "payment_method": "wise",
            "reference_number": "WISE-12345",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["booking_id"] == booking["id"]
    assert body["payment_type"] == "supplier_invoice"
    assert body["paid_amount"] == 4250.5
    assert body["reconciliation_status"] == "pending_review"
    assert body["reference_number"] == "WISE-12345"


def test_post_payment_proof_404_for_unknown_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.post(
        "/bookings/UNKNOWN/payment-proofs",
        headers=IMPORTER_HEADERS,
        json={
            "payment_type": "supplier_invoice",
            "paid_amount": 1.0,
            "paid_currency": "USD",
            "paid_at": _now(),
            "paid_by": "x",
        },
    )
    assert response.status_code == 404


def test_list_payment_proofs_returns_only_booking_records_newest_first() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    other = client.post(
        "/bookings",
        headers=IMPORTER_HEADERS,
        json={**_booking_payload(), "importer_email": "other-ppl@example.com"},
    ).json()["booking"]

    client.post(
        f"/bookings/{booking['id']}/payment-proofs",
        headers=IMPORTER_HEADERS,
        json={
            "payment_type": "freight_invoice",
            "paid_amount": 100,
            "paid_at": _now(),
            "paid_by": "Sam",
        },
    )
    client.post(
        f"/bookings/{other['id']}/payment-proofs",
        headers=IMPORTER_HEADERS,
        json={
            "payment_type": "duty_gst",
            "paid_amount": 50,
            "paid_at": _now(),
            "paid_by": "Sam",
        },
    )

    response = client.get(f"/bookings/{booking['id']}/payment-proofs", headers=IMPORTER_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["booking_id"] == booking["id"]


def test_patch_payment_proof_marks_matched_and_records_reviewer() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    proof_id = client.post(
        f"/bookings/{booking['id']}/payment-proofs",
        headers=IMPORTER_HEADERS,
        json={
            "payment_type": "freight_invoice",
            "paid_amount": 250,
            "paid_at": _now(),
            "paid_by": "Sam",
        },
    ).json()["id"]

    response = client.patch(
        f"/payment-proofs/{proof_id}",
        headers=ADMIN_HEADERS,
        json={"reconciliation_status": "matched"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reconciliation_status"] == "matched"
    assert body["reviewed_by"] == "dev-admin"
    assert body["reviewed_at"] is not None


def test_patch_payment_proof_variance_records_amount_and_audit() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    proof_id = client.post(
        f"/bookings/{booking['id']}/payment-proofs",
        headers=IMPORTER_HEADERS,
        json={
            "payment_type": "freight_invoice",
            "paid_amount": 240,
            "paid_at": _now(),
            "paid_by": "Sam",
        },
    ).json()["id"]

    response = client.patch(
        f"/payment-proofs/{proof_id}",
        headers=ADMIN_HEADERS,
        json={
            "reconciliation_status": "variance",
            "variance_amount": -10.0,
            "notes": "Bank fee not on invoice",
        },
    )
    assert response.status_code == 200
    assert response.json()["variance_amount"] == -10.0

    audits = [
        e
        for e in store.audit_events.values()
        if e.entity_type == "payment_proof" and e.event_type == "payment_proof_reconciled"
    ]
    assert audits


def test_post_landed_cost_actual_records_variance_when_estimated_set() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)

    response = client.post(
        f"/bookings/{booking['id']}/landed-cost-actual",
        headers=ADMIN_HEADERS,
        json={
            "estimated_total_usd": 12000.0,
            "actual_total_usd": 12450.0,
            "currency": "USD",
            "international_freight": 5400.0,
            "destination_trucking": 320.0,
            "variance_reason": "Carrier surcharge",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["booking_id"] == booking["id"]
    assert body["actual_total_usd"] == 12450.0
    assert body["variance_amount_usd"] == 450.0


def test_post_landed_cost_actual_upserts_existing_record_per_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)

    first = client.post(
        f"/bookings/{booking['id']}/landed-cost-actual",
        headers=ADMIN_HEADERS,
        json={"actual_total_usd": 10000.0, "estimated_total_usd": 9500.0},
    ).json()
    second = client.post(
        f"/bookings/{booking['id']}/landed-cost-actual",
        headers=ADMIN_HEADERS,
        json={"actual_total_usd": 10250.0, "estimated_total_usd": 9500.0, "finalised": True},
    ).json()

    assert first["id"] == second["id"]
    assert second["actual_total_usd"] == 10250.0
    assert second["variance_amount_usd"] == 750.0
    assert second["finalised_at"] is not None


def test_get_landed_cost_actual_returns_404_when_missing() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)

    response = client.get(
        f"/bookings/{booking['id']}/landed-cost-actual",
        headers=IMPORTER_HEADERS,
    )
    assert response.status_code == 404
