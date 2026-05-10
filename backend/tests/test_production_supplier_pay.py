from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests


IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def booking_payload() -> dict:
    return {
        "importer_company_name": "Bayside Build Co.",
        "importer_contact_name": "Alex Morgan",
        "importer_email": "production@example.com",
        "supplier_name": "Foshan Fixtures Co.",
        "supplier_city": "Foshan",
        "supplier_province": "Guangdong",
        "supplier_country": "China",
        "delivery_city": "Brisbane",
        "delivery_postcode": "4101",
        "delivery_country": "Australia",
        "cargo_description": "bathroom vanities",
        "cargo_category": "bathroom_fittings",
        "cbm_estimate": 8,
        "weight_kg_estimate": 1900,
        "cargo_ready_date_earliest": date.today().isoformat(),
        "cargo_ready_date_latest": (date.today() + timedelta(days=6)).isoformat(),
        "service_level": "standard",
    }


def test_purchase_order_creates_production_and_supplier_pay_workspace() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload()).json()["booking"]

    response = client.post(
        "/purchase-orders",
        headers=IMPORTER_HEADERS,
        json={
            "booking_id": booking["id"],
            "order_reference": "PO-1001",
            "buyer_company_name": "Bayside Build Co.",
            "supplier_name": "Foshan Fixtures Co.",
            "supplier_contact_email": "sales@foshan-fixtures.example",
            "product_summary": "Bathroom vanities and mirrors",
            "goods_value": 12000,
            "deposit_amount": 3600,
            "balance_amount": 8400,
            "production_due_date": (date.today() + timedelta(days=21)).isoformat(),
            "cargo_ready_target_date": (date.today() + timedelta(days=24)).isoformat(),
            "inspection_required": True,
        },
    )

    assert response.status_code == 201
    purchase_order = response.json()
    assert purchase_order["status"] == "deposit_due"

    milestones = client.get(f"/purchase-orders/{purchase_order['id']}/milestones", headers=IMPORTER_HEADERS).json()
    assert {milestone["milestone_type"] for milestone in milestones} >= {
        "deposit_paid",
        "production_complete",
        "qc_passed",
        "goods_ready",
    }

    pay_requests = client.get("/supplier-pay-requests", headers=IMPORTER_HEADERS).json()
    assert len(pay_requests) == 1
    assert pay_requests[0]["payment_stage"] == "deposit"
    assert pay_requests[0]["status"] == "approval_required"
    assert pay_requests[0]["approval_request_id"]

    quotes = client.get(
        f"/supplier-pay-requests/{pay_requests[0]['id']}/quotes",
        headers=IMPORTER_HEADERS,
    ).json()
    assert len(quotes) == 2
    assert quotes[0]["estimated_total"] <= quotes[1]["estimated_total"]
    assert any(quote["selected"] for quote in quotes)

    workspace = client.get(f"/bookings/{booking['id']}/import-project", headers=IMPORTER_HEADERS).json()
    assert workspace["purchase_orders"][0]["id"] == purchase_order["id"]
    assert workspace["supplier_pay_requests"][0]["id"] == pay_requests[0]["id"]
    assert workspace["approvals"][0]["id"] == pay_requests[0]["approval_request_id"]


def test_supplier_pay_can_be_marked_paid_without_required_proof() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload()).json()["booking"]
    purchase_order = client.post(
        "/purchase-orders",
        headers=IMPORTER_HEADERS,
        json={
            "booking_id": booking["id"],
            "order_reference": "PO-1002",
            "buyer_company_name": "Bayside Build Co.",
            "supplier_name": "Foshan Fixtures Co.",
            "product_summary": "Bathroom vanities",
            "goods_value": 5000,
            "deposit_amount": 1000,
            "balance_amount": 4000,
        },
    ).json()
    pay_request = client.get("/supplier-pay-requests", headers=IMPORTER_HEADERS).json()[0]

    mark_paid = client.post(
        f"/supplier-pay-requests/{pay_request['id']}/mark-paid",
        headers=IMPORTER_HEADERS,
        json={"paid_by": "Alex Morgan", "notes": "Paid by normal bank transfer."},
    )

    assert mark_paid.status_code == 200
    paid_request = mark_paid.json()
    assert paid_request["status"] == "marked_paid_outside_app"
    assert paid_request["proof_storage_key"] is None

    approvals = client.get("/approvals", headers=IMPORTER_HEADERS).json()
    assert approvals[0]["status"] == "approved"

    milestones = client.get(f"/purchase-orders/{purchase_order['id']}/milestones", headers=IMPORTER_HEADERS).json()
    deposit = next(milestone for milestone in milestones if milestone["milestone_type"] == "deposit_paid")
    assert deposit["status"] == "complete"
