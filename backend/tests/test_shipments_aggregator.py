from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store
from app.models import (
    ActorRole,
    ApprovalRequestType,
    ApprovalStatus,
    DocumentUploadRequest,
    DocumentType,
    ShipmentEventCreate,
    ShipmentEventStage,
)
from app.operations import (
    create_approval_request,
    create_shipment_event,
    upload_document,
)


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}
CRON_HEADERS = {"Authorization": "Bearer shiphoppa-cron-dev"}


def booking_payload(email: str = "shipments-test@example.com") -> dict:
    return {
        "importer_company_name": "Acme Imports",
        "importer_contact_name": "Sam Trader",
        "importer_email": email,
        "supplier_name": "Foshan Light Co.",
        "supplier_city": "Foshan",
        "supplier_province": "Guangdong",
        "supplier_country": "China",
        "delivery_city": "Sydney",
        "delivery_postcode": "2000",
        "delivery_country": "Australia",
        "cargo_description": "lighting fixtures",
        "cargo_category": "homewares",
        "cbm_estimate": 18,
        "weight_kg_estimate": 3200,
        "cargo_ready_date_earliest": date.today().isoformat(),
        "cargo_ready_date_latest": (date.today() + timedelta(days=4)).isoformat(),
        "service_level": "standard",
    }


def _new_booking(client: TestClient, email: str = "shipments-test@example.com") -> dict:
    response = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload(email))
    assert response.status_code == 201
    return response.json()["booking"]


def test_shipments_list_returns_summary_objects_sorted_newest_first() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    first = _new_booking(client, "first@example.com")
    second = _new_booking(client, "second@example.com")

    response = client.get("/shipments", headers=IMPORTER_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 2

    new_ids = {first["id"], second["id"]}
    summaries = [s for s in body if s["booking"]["id"] in new_ids]
    assert summaries[0]["booking"]["id"] == second["id"]
    assert summaries[1]["booking"]["id"] == first["id"]

    for summary in summaries:
        assert "pending_approvals_count" in summary
        assert "documents_count" in summary
        assert "events_count" in summary
        assert "has_invoice" in summary


def test_shipments_list_requires_auth() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.get("/shipments")
    assert response.status_code == 401


def test_shipments_list_rejects_cron_role() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.get("/shipments", headers=CRON_HEADERS)
    assert response.status_code == 401


def test_shipment_workspace_returns_full_bundle_for_existing_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)

    response = client.get(f"/shipments/{booking['id']}/workspace", headers=IMPORTER_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["booking"]["id"] == booking["id"]
    assert isinstance(body["documents"], list)
    assert isinstance(body["events"], list)
    assert isinstance(body["approvals"], list)
    assert isinstance(body["purchase_orders"], list)
    assert isinstance(body["production_milestones"], list)
    assert isinstance(body["quality_inspections"], list)
    assert isinstance(body["supplier_pay_requests"], list)
    assert isinstance(body["supplier_pay_quotes"], list)
    assert isinstance(body["source_messages"], list)
    assert "release_status" in body
    assert body["release_status"]["booking_id"] == booking["id"]


def test_shipment_workspace_returns_404_for_unknown_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.get("/shipments/unknown-id/workspace", headers=IMPORTER_HEADERS)
    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found"


def test_shipment_workspace_invoice_and_delivery_plan_default_to_none() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)

    response = client.get(f"/shipments/{booking['id']}/workspace", headers=IMPORTER_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["invoice"] is None
    assert body["delivery_plan"] is None
    # Customs profile is auto-created with the booking workspace, so it is not None.
    assert body["customs_profile"] is not None
    assert body["customs_profile"]["booking_id"] == booking["id"]


def test_shipment_workspace_pending_approvals_count_excludes_decided_ones() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    booking_obj = store.bookings[booking["id"]]

    pending = create_approval_request(
        store,
        ApprovalRequestType.approve_customs_submission,
        title="Approve customs filing",
        summary="Confirm declared value",
        related_booking_id=booking_obj.id,
    )
    approved = create_approval_request(
        store,
        ApprovalRequestType.approve_release,
        title="Approve release",
        summary="Confirm release for delivery",
        related_booking_id=booking_obj.id,
    )
    approved.status = ApprovalStatus.approved
    store.approval_requests[approved.id] = approved

    response = client.get(f"/shipments/{booking['id']}/workspace", headers=IMPORTER_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["pending_approvals_count"] == 1
    statuses = sorted(a["status"] for a in body["approvals"])
    assert statuses == ["approved", "pending"]
    assert any(a["id"] == pending.id for a in body["approvals"])


def test_shipment_workspace_counts_documents_and_events() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    booking_obj = store.bookings[booking["id"]]

    upload_document(
        store,
        booking_obj.id,
        DocumentUploadRequest(
            document_type=DocumentType.commercial_invoice,
            file_name="test.pdf",
            mime_type="application/pdf",
        ),
        ActorRole.importer,
        "importer",
    )
    create_shipment_event(
        store,
        booking_obj.id,
        ShipmentEventCreate(stage=ShipmentEventStage.warehouse_received),
    )

    summary_resp = client.get("/shipments", headers=IMPORTER_HEADERS)
    summary = next(s for s in summary_resp.json() if s["booking"]["id"] == booking_obj.id)
    assert summary["documents_count"] >= 1
    assert summary["events_count"] >= 1
    assert summary["last_event_stage"] == ShipmentEventStage.warehouse_received.value
