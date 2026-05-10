from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store
from app.models import ApprovalRequestType, ApprovalStatus
from app.operations import create_approval_request


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def _booking_payload(email: str = "review@example.com") -> dict:
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


def _new_booking(client: TestClient) -> dict:
    response = client.post("/bookings", headers=IMPORTER_HEADERS, json=_booking_payload())
    assert response.status_code == 201
    return response.json()["booking"]


def test_request_review_sets_review_fields_and_keeps_status_pending() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    approval = create_approval_request(
        store,
        ApprovalRequestType.approve_customs_submission,
        title="Approve customs filing",
        summary="Confirm declared value",
        related_booking_id=booking["id"],
    )

    response = client.post(
        f"/approvals/{approval.id}/request-review",
        headers=IMPORTER_HEADERS,
        json={"reason": "Need ops to confirm declared value before submission"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == approval.id
    assert body["status"] == ApprovalStatus.pending.value
    assert body["review_requested_by"] == "dev-importer"
    assert body["review_requested_at"] is not None
    assert body["review_requested_reason"] == "Need ops to confirm declared value before submission"


def test_request_review_creates_admin_task_when_booking_linked() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = _new_booking(client)
    approval = create_approval_request(
        store,
        ApprovalRequestType.approve_customs_submission,
        title="Approve customs filing",
        summary="Confirm declared value",
        related_booking_id=booking["id"],
    )
    before = sum(1 for t in store.admin_tasks.values() if t.booking_id == booking["id"])

    response = client.post(
        f"/approvals/{approval.id}/request-review",
        headers=IMPORTER_HEADERS,
        json={"reason": "Confirm value"},
    )
    assert response.status_code == 200

    after = [t for t in store.admin_tasks.values() if t.booking_id == booking["id"] and t.task_type == "approval_review_requested"]
    assert len(after) == 1
    assert before < len(store.admin_tasks)


def test_request_review_no_admin_task_when_no_booking_linked() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    approval = create_approval_request(
        store,
        ApprovalRequestType.approve_customs_submission,
        title="Approve filing without booking",
        summary="Standalone approval",
    )
    before_count = len(store.admin_tasks)

    response = client.post(
        f"/approvals/{approval.id}/request-review",
        headers=IMPORTER_HEADERS,
        json={"reason": "Need ops review"},
    )
    assert response.status_code == 200
    assert response.json()["review_requested_reason"] == "Need ops review"
    assert len(store.admin_tasks) == before_count


def test_request_review_creates_audit_event_with_expected_metadata() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    approval = create_approval_request(
        store,
        ApprovalRequestType.approve_customs_submission,
        title="Approve filing",
        summary="Confirm declared value",
    )

    response = client.post(
        f"/approvals/{approval.id}/request-review",
        headers=IMPORTER_HEADERS,
        json={"reason": "double-check declared value"},
    )
    assert response.status_code == 200

    audit_events = [
        e for e in store.audit_events.values()
        if e.entity_type == "approval_request"
        and e.entity_id == approval.id
        and e.event_type == "approval_review_requested"
    ]
    assert len(audit_events) == 1
    event = audit_events[0]
    assert "reason" in event.metadata
    assert event.metadata["reason"] == "double-check declared value"
    assert "actor" in event.metadata


def test_request_review_returns_404_for_unknown_id() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.post(
        "/approvals/UNKNOWN/request-review",
        headers=IMPORTER_HEADERS,
        json={"reason": "test"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Approval not found"


def test_request_review_returns_400_when_already_decided() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    approval = create_approval_request(
        store,
        ApprovalRequestType.approve_customs_submission,
        title="Approve filing",
        summary="Confirm declared value",
    )
    approval.status = ApprovalStatus.approved
    store.approval_requests[approval.id] = approval

    response = client.post(
        f"/approvals/{approval.id}/request-review",
        headers=IMPORTER_HEADERS,
        json={"reason": "test"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Approval already decided"


def test_request_review_can_be_re_called_to_restamp_reason() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    approval = create_approval_request(
        store,
        ApprovalRequestType.approve_customs_submission,
        title="Approve filing",
        summary="Confirm declared value",
    )

    first = client.post(
        f"/approvals/{approval.id}/request-review",
        headers=IMPORTER_HEADERS,
        json={"reason": "first reason"},
    )
    assert first.status_code == 200
    assert first.json()["review_requested_reason"] == "first reason"

    second = client.post(
        f"/approvals/{approval.id}/request-review",
        headers=IMPORTER_HEADERS,
        json={"reason": "updated reason"},
    )
    assert second.status_code == 200
    assert second.json()["review_requested_reason"] == "updated reason"
    assert second.json()["status"] == ApprovalStatus.pending.value
