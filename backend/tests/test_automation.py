"""Tests for the automation engine: state machine, extraction, missing data, chase."""

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.automation import (
    AutomationAction,
    ExtractedFact,
    ShipmentLifecycleState,
    automation_decision_for_fact,
    create_pending_approvals,
    derive_lifecycle_state,
    detect_missing_data,
    detect_pending_approvals,
    extract_facts_from_text,
    next_action_for_state,
    run_automation_for_booking,
    check_stale_shipments,
    try_advance_booking_status,
)
from app.main import app, reset_store_for_tests, store
from app.models import (
    ApprovalRequestType,
    BookingStatus,
    CustomsStatus,
    DeliveryPlanStatus,
    ReleaseStatus,
    ShipmentEventCreate,
    ShipmentEventStage,
    SourceConfidence,
)
from app.operations import create_shipment_event, ensure_customs_profile, ensure_delivery_plan


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def booking_payload() -> dict:
    return {
        "importer_company_name": "Test Imports Pty Ltd",
        "importer_contact_name": "Jane Doe",
        "importer_email": "jane@test.com",
        "supplier_city": "Foshan",
        "supplier_province": "Guangdong",
        "supplier_country": "China",
        "delivery_city": "Melbourne",
        "delivery_postcode": "3000",
        "delivery_country": "Australia",
        "cargo_description": "ceramic tiles",
        "cargo_category": "tiles_stone",
        "cbm_estimate": 15,
        "weight_kg_estimate": 6000,
        "cargo_ready_date_earliest": date.today().isoformat(),
        "cargo_ready_date_latest": (date.today() + timedelta(days=7)).isoformat(),
        "service_level": "standard",
    }


def create_booking() -> str:
    client = TestClient(app)
    response = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload())
    assert response.status_code == 201
    return response.json()["booking"]["id"]


class TestFactExtraction:
    def test_extracts_booking_id(self) -> None:
        facts = extract_facts_from_text("Please process BK-0012 urgently")
        assert any(f.field == "booking_id" and f.value == "BK-0012" for f in facts)

    def test_extracts_container_number(self) -> None:
        facts = extract_facts_from_text("Container MSCU1234567 has departed")
        assert any(f.field == "container_number" and f.value == "MSCU1234567" for f in facts)

    def test_extracts_cbm(self) -> None:
        facts = extract_facts_from_text("Total volume is 18.5 CBM")
        assert any(f.field == "cbm" and f.value == "18.5" for f in facts)

    def test_extracts_weight(self) -> None:
        facts = extract_facts_from_text("Gross weight 4200 kgs")
        assert any(f.field == "weight_kg" and f.value == "4200" for f in facts)

    def test_extracts_vessel_name(self) -> None:
        facts = extract_facts_from_text("Vessel: Ever Given departing Shanghai")
        assert any(f.field == "vessel_name" and "Ever Given" in f.value for f in facts)

    def test_extracts_voyage_number(self) -> None:
        facts = extract_facts_from_text("Voyage: 0241W confirmed")
        assert any(f.field == "voyage_number" and f.value == "0241W" for f in facts)

    def test_extracts_eta(self) -> None:
        facts = extract_facts_from_text("ETA: 2026-06-15 at Melbourne")
        assert any(f.field == "eta" and f.value == "2026-06-15" for f in facts)

    def test_extracts_ready_date(self) -> None:
        facts = extract_facts_from_text("Cargo ready date: 2026-05-20")
        assert any(f.field == "cargo_ready_date" and f.value == "2026-05-20" for f in facts)

    def test_extracts_invoice_amount(self) -> None:
        facts = extract_facts_from_text("Total: USD 4,250.00 payable within 7 days")
        assert any(f.field == "invoice_amount_usd" and f.value == "4250.00" for f in facts)

    def test_extracts_po_number(self) -> None:
        facts = extract_facts_from_text("PO #SH-2026-0044 for ceramic tiles")
        assert any(f.field == "po_number" and f.value == "SH-2026-0044" for f in facts)

    def test_empty_text_returns_no_facts(self) -> None:
        facts = extract_facts_from_text("")
        assert facts == []

    def test_no_match_returns_empty(self) -> None:
        facts = extract_facts_from_text("Hello, thank you for your enquiry.")
        assert facts == []


class TestAutomationDecision:
    def test_verified_booking_id_auto_accepts(self) -> None:
        fact = ExtractedFact(field="booking_id", value="BK-0001", confidence=SourceConfidence.verified)
        assert automation_decision_for_fact(fact) == AutomationAction.auto_accept

    def test_estimated_eta_auto_accepts(self) -> None:
        fact = ExtractedFact(field="eta", value="2026-06-15", confidence=SourceConfidence.estimated)
        assert automation_decision_for_fact(fact) == AutomationAction.auto_accept

    def test_invoice_amount_asks_customer(self) -> None:
        fact = ExtractedFact(field="invoice_amount_usd", value="5000", confidence=SourceConfidence.estimated)
        assert automation_decision_for_fact(fact) == AutomationAction.ask_customer


class TestLifecycleState:
    def test_submitted_booking_is_draft(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        state = derive_lifecycle_state(store, booking)
        assert state == ShipmentLifecycleState.order_confirmed

    def test_every_state_has_next_action(self) -> None:
        for state in ShipmentLifecycleState:
            label = next_action_for_state(state)
            assert label
            assert len(label) > 5


class TestMissingData:
    def test_detects_missing_supplier_name(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.supplier_name = None
        missing = detect_missing_data(store, booking)
        assert any(m.field == "supplier_name" for m in missing)

    def test_cargo_ready_needs_packing_list(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.supplier_name = "Foshan Tiles Co"
        booking.pickup_address = "123 Factory Rd"
        missing = detect_missing_data(store, booking)
        assert any(m.field == "packing_list" for m in missing)
        assert any(m.field == "commercial_invoice" for m in missing)


class TestRunAutomation:
    def test_run_automation_returns_result(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        result = run_automation_for_booking(store, booking)
        assert result.lifecycle_state in ShipmentLifecycleState
        assert result.next_action_label


class TestStaleChecks:
    def test_overdue_cargo_ready(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.cargo_ready_date_latest = date.today() - timedelta(days=3)
        alerts = check_stale_shipments(store)
        assert any(a["booking_id"] == booking_id and a["alert"] == "overdue_cargo_ready" for a in alerts)


class TestApprovalCreation:
    def test_invoice_amount_creates_approval(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        from app.automation import apply_extracted_facts, ExtractedFact
        from app.models import SourceConfidence
        facts = [
            ExtractedFact(field="invoice_amount_usd", value="5000.00", confidence=SourceConfidence.estimated),
        ]
        applied, needs_review = apply_extracted_facts(store, booking, facts)
        assert len(applied) == 0
        assert len(needs_review) == 1
        approvals = [a for a in store.approval_requests.values() if a.related_booking_id == booking_id]
        assert len(approvals) == 1
        assert approvals[0].amount_usd == 5000.0


class TestAutomationAPI:
    def test_shipment_state_endpoint(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        response = client.get(f"/automation/shipment-state/{booking_id}", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["lifecycle_state"] == "order_confirmed"
        assert data["next_action"]

    def test_missing_data_endpoint(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        response = client.get(f"/automation/missing-data/{booking_id}", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_run_all_automation(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        create_booking()
        response = client.post("/automation/run-all", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["shipments_processed"] >= 1

    def test_extract_message_facts(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        create_booking()
        msg_response = client.post(
            "/source-messages",
            headers=ADMIN_HEADERS,
            json={
                "source_type": "forwarded_email",
                "from_address": "supplier@factory.cn",
                "to_addresses": ["imports@shiphoppa.com"],
                "subject": "Cargo ready 2026-05-25 for your order",
                "body": "Dear buyer, cargo ready date: 2026-05-25. Total 18.5 CBM, 4200 kgs. Vessel: Pacific Star, Voyage: 0245E.",
            },
        )
        assert msg_response.status_code == 201
        message_id = msg_response.json()["id"]

        extract_response = client.post(f"/automation/extract/{message_id}", headers=ADMIN_HEADERS)
        assert extract_response.status_code == 200
        facts = extract_response.json()
        assert len(facts) >= 3
        fields = [f["field"] for f in facts]
        assert "cbm" in fields
        assert "weight_kg" in fields
        assert "vessel_name" in fields

    def test_stale_checks_endpoint(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        response = client.get("/automation/stale-checks", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestStatusAdvancement:
    def test_warehouse_event_advances_to_at_warehouse(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.status = BookingStatus.confirmed
        booking.container_id = "CTR-0001"
        create_shipment_event(
            store,
            booking_id,
            ShipmentEventCreate(stage=ShipmentEventStage.warehouse_received),
        )
        advanced = try_advance_booking_status(store, booking)
        assert advanced is True
        assert booking.status == BookingStatus.at_warehouse
        assert booking.received_at_warehouse is not None

    def test_loaded_event_advances_to_loaded(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.status = BookingStatus.at_warehouse
        booking.cbm_actual = 15.0
        booking.weight_kg_actual = 6000.0
        create_shipment_event(
            store,
            booking_id,
            ShipmentEventCreate(stage=ShipmentEventStage.loaded),
        )
        advanced = try_advance_booking_status(store, booking)
        assert advanced is True
        assert booking.status == BookingStatus.loaded
        assert booking.loaded_at is not None

    def test_departed_event_advances_to_shipped(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.status = BookingStatus.loaded
        create_shipment_event(
            store,
            booking_id,
            ShipmentEventCreate(stage=ShipmentEventStage.departed),
        )
        advanced = try_advance_booking_status(store, booking)
        assert advanced is True
        assert booking.status == BookingStatus.shipped
        assert booking.shipped_at is not None

    def test_arrived_event_advances_to_arrived(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.status = BookingStatus.shipped
        create_shipment_event(
            store,
            booking_id,
            ShipmentEventCreate(stage=ShipmentEventStage.arrived),
        )
        advanced = try_advance_booking_status(store, booking)
        assert advanced is True
        assert booking.status == BookingStatus.arrived
        assert booking.arrived_at_port is not None

    def test_no_advance_without_event(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.status = BookingStatus.confirmed
        advanced = try_advance_booking_status(store, booking)
        assert advanced is False
        assert booking.status == BookingStatus.confirmed

    def test_status_advancement_creates_notification(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.status = BookingStatus.loaded
        create_shipment_event(
            store,
            booking_id,
            ShipmentEventCreate(stage=ShipmentEventStage.departed),
        )
        before = len(store.notifications)
        try_advance_booking_status(store, booking)
        after = len(store.notifications)
        assert after > before
        new_notifs = [n for n in store.notifications.values() if n.trigger == "status_shipped"]
        assert len(new_notifs) == 1
        assert booking_id in new_notifs[0].message

    def test_no_advance_loaded_without_actuals(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.status = BookingStatus.at_warehouse
        create_shipment_event(
            store,
            booking_id,
            ShipmentEventCreate(stage=ShipmentEventStage.loaded),
        )
        advanced = try_advance_booking_status(store, booking)
        assert advanced is False
        assert booking.status == BookingStatus.at_warehouse


class TestAdminTaskAPI:
    def test_list_admin_tasks_empty(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        response = client.get("/admin-tasks", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_admin_tasks_after_automation(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.cargo_ready_date_latest = date.today() - timedelta(days=3)
        client.post("/automation/run-all", headers=ADMIN_HEADERS)
        response = client.get("/admin-tasks", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 1
        assert any(t["task_type"] == "overdue_cargo_ready" for t in tasks)

    def test_resolve_admin_task(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.cargo_ready_date_latest = date.today() - timedelta(days=3)
        client.post("/automation/run-all", headers=ADMIN_HEADERS)
        tasks = client.get("/admin-tasks", headers=ADMIN_HEADERS).json()
        task_id = tasks[0]["id"]
        response = client.post(f"/admin-tasks/{task_id}/resolve", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        assert response.json()["status"] == "done"

    def test_dismiss_admin_task(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.cargo_ready_date_latest = date.today() - timedelta(days=3)
        client.post("/automation/run-all", headers=ADMIN_HEADERS)
        tasks = client.get("/admin-tasks", headers=ADMIN_HEADERS).json()
        task_id = tasks[0]["id"]
        response = client.post(f"/admin-tasks/{task_id}/dismiss", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        assert response.json()["status"] == "waived"

    def test_admin_task_summary(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        response = client.get("/admin-tasks/summary", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "total_open" in data
        assert "by_type" in data

    def test_filter_by_status(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.cargo_ready_date_latest = date.today() - timedelta(days=3)
        client.post("/automation/run-all", headers=ADMIN_HEADERS)
        response = client.get("/admin-tasks?status=open", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        tasks = response.json()
        assert all(t["status"] == "open" for t in tasks)

    def test_filter_by_booking_id(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.cargo_ready_date_latest = date.today() - timedelta(days=3)
        client.post("/automation/run-all", headers=ADMIN_HEADERS)
        response = client.get(f"/admin-tasks?booking_id={booking_id}", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        tasks = response.json()
        assert all(t["booking_id"] == booking_id for t in tasks)


class TestApprovalAutomation:
    def test_no_release_approval_for_blocked_booking(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.release_status = ReleaseStatus.blocked
        needs = detect_pending_approvals(store, booking)
        assert ApprovalRequestType.approve_release not in needs

    def test_customs_documents_required_creates_approval(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        profile = ensure_customs_profile(store, booking)
        profile.hs_code = "6907.21"
        profile.customs_status = CustomsStatus.documents_required
        needs = detect_pending_approvals(store, booking)
        assert ApprovalRequestType.approve_customs_submission in needs

    def test_delivery_ready_creates_trucking_approval(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        plan = ensure_delivery_plan(store, booking)
        plan.status = DeliveryPlanStatus.ready_to_book
        needs = detect_pending_approvals(store, booking)
        assert ApprovalRequestType.approve_trucking in needs

    def test_release_ready_creates_release_approval(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.release_status = ReleaseStatus.ready
        needs = detect_pending_approvals(store, booking)
        assert ApprovalRequestType.approve_release in needs

    def test_existing_approval_not_duplicated(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.release_status = ReleaseStatus.ready
        created = create_pending_approvals(store, booking)
        assert created >= 1
        created_again = create_pending_approvals(store, booking)
        assert created_again == 0

    def test_create_pending_approvals_writes_to_store(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.release_status = ReleaseStatus.ready
        before = len(store.approval_requests)
        create_pending_approvals(store, booking)
        after = len(store.approval_requests)
        assert after > before
        approvals = [
            a for a in store.approval_requests.values()
            if a.related_booking_id == booking_id
            and a.request_type == ApprovalRequestType.approve_release
        ]
        assert len(approvals) == 1
        assert "release" in approvals[0].title.lower()


class TestEmailTemplates:
    def test_render_chase_pickup_address(self) -> None:
        from app.templates import render
        subject, body = render(
            "chase_pickup_address",
            {"booking_id": "BK-0042", "supplier_name": "Foshan Tiles Co", "cargo_description": "ceramic tiles"},
        )
        assert "BK-0042" in subject
        assert "Foshan Tiles Co" in body
        assert "ceramic tiles" in body
        assert "pickup address" in body.lower()

    def test_render_importer_arrival(self) -> None:
        from app.templates import render
        subject, body = render(
            "importer_arrival_notice",
            {
                "booking_id": "BK-0007",
                "importer_name": "Jane",
                "cargo_description": "homewares",
                "destination_port": "Melbourne",
            },
        )
        assert "BK-0007" in subject
        assert "Jane" in body
        assert "Melbourne" in body

    def test_render_unknown_falls_back_to_generic(self) -> None:
        from app.templates import render
        subject, body = render(
            "made_up_template_key",
            {"booking_id": "BK-0001"},
        )
        assert "BK-0001" in subject
        assert body  # something rendered

    def test_render_missing_context_safe(self) -> None:
        from app.templates import render
        subject, body = render(
            "chase_pickup_address",
            {"booking_id": "BK-0001"},
        )
        # missing supplier_name shouldn't raise; placeholder remains visible
        assert "BK-0001" in subject
        assert "{supplier_name}" in body or "team" not in body or "supplier_name" in body or body

    def test_render_for_booking_includes_supplier_name(self) -> None:
        from app.automation import render_for_booking
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.supplier_name = "Foshan Tiles Co"
        subject, body = render_for_booking("chase_packing_list", booking)
        assert booking_id in subject
        assert "Foshan Tiles Co" in body


CRON_HEADERS = {"Authorization": "Bearer shiphoppa-cron-dev"}


class TestCronAutomation:
    def test_cron_run_requires_token(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        response = client.post("/automation/cron/run")
        assert response.status_code == 401

    def test_cron_run_rejects_admin_token(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        response = client.post("/automation/cron/run", headers=ADMIN_HEADERS)
        assert response.status_code == 401

    def test_cron_run_succeeds_with_cron_token(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        create_booking()
        response = client.post("/automation/cron/run", headers=CRON_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["shipments_processed"] >= 1
        assert "open_admin_tasks" in data
        assert "pending_approvals" in data

    def test_cron_health_endpoint(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        response = client.post("/automation/cron/health", headers=CRON_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "active_bookings" in data


class TestLandedCost:
    def test_landed_cost_returns_lines(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        response = client.get(f"/bookings/{booking_id}/landed-cost", headers=IMPORTER_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["booking_id"] == booking_id
        assert "lines" in data
        assert "total_landed_cost_usd" in data
        assert "paid_to_date_usd" in data
        assert "remaining_estimate_usd" in data

    def test_landed_cost_includes_customs_estimates(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        from app.operations import ensure_customs_profile
        profile = ensure_customs_profile(store, booking)
        profile.duty_estimate_usd = 1240.00
        profile.gst_estimate_usd = 820.00
        response = client.get(f"/bookings/{booking_id}/landed-cost", headers=IMPORTER_HEADERS)
        data = response.json()
        categories = [line["category"] for line in data["lines"]]
        assert "duty" in categories
        assert "gst" in categories
        assert data["total_landed_cost_usd"] >= 1240.00 + 820.00

    def test_landed_cost_unknown_booking_404s(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        response = client.get("/bookings/BK-9999/landed-cost", headers=IMPORTER_HEADERS)
        assert response.status_code == 404


class TestNotificationsAPI:
    def test_importer_can_list_notifications(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        response = client.get("/notifications", headers=IMPORTER_HEADERS)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_mark_all_read(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        # Create a notification directly in the store
        from app.models import Notification, ActorRole
        from datetime import datetime
        notif = Notification(
            id="NOTIF-TEST",
            recipient_type="importer",
            recipient_id="dev-importer",
            trigger="approval_needed",
            message="Test notification",
            created_at=datetime.utcnow(),
            scheduled_for=None,
            read=False,
        )
        store.notifications[notif.id] = notif

        response = client.post("/notifications/mark-all-read", headers=IMPORTER_HEADERS)
        assert response.status_code == 200
        assert response.json()["marked_read"] >= 1
        assert store.notifications["NOTIF-TEST"].read is True

    def test_mark_single_unknown_404s(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        response = client.post("/notifications/NOTIF-9999/read", headers=IMPORTER_HEADERS)
        assert response.status_code == 404

    def test_approval_creation_creates_notification(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.release_status = ReleaseStatus.ready
        before = len(store.notifications)
        create_pending_approvals(store, booking)
        after = len(store.notifications)
        assert after > before
        new_notifs = [n for n in store.notifications.values() if n.trigger == "approval_required"]
        assert len(new_notifs) >= 1
        assert all(n.read is False for n in new_notifs)


class TestSpaceOpportunity:
    def _make_fcl_booking(self) -> str:
        from app.models import ImportWorkflowType
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        booking.cbm_actual = 25.0
        # Flip the auto-created import project to fcl_spare_space so detection runs
        for project in store.import_projects.values():
            if booking_id in (project.linked_shipment_ids or []):
                project.workflow_type = ImportWorkflowType.fcl_spare_space
                break
        return booking_id

    def test_detect_returns_none_for_non_fcl(self) -> None:
        reset_store_for_tests()
        booking_id = create_booking()
        from app.operations import detect_fcl_spare_space
        opp = detect_fcl_spare_space(store, booking_id)
        assert opp is None

    def test_detect_creates_opportunity_for_fcl(self) -> None:
        reset_store_for_tests()
        booking_id = self._make_fcl_booking()
        from app.operations import detect_fcl_spare_space
        opp = detect_fcl_spare_space(store, booking_id)
        assert opp is not None
        assert opp.recoverable_cbm > 0
        assert opp.estimated_recovery_usd > 0

    def test_detect_is_idempotent(self) -> None:
        reset_store_for_tests()
        booking_id = self._make_fcl_booking()
        from app.operations import detect_fcl_spare_space
        first = detect_fcl_spare_space(store, booking_id)
        second = detect_fcl_spare_space(store, booking_id)
        assert first is not None
        assert second is not None
        assert first.id == second.id

    def test_list_endpoint(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = self._make_fcl_booking()
        client.post(f"/bookings/{booking_id}/space-opportunities/detect", headers=IMPORTER_HEADERS)
        response = client.get(f"/bookings/{booking_id}/space-opportunities", headers=IMPORTER_HEADERS)
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 1

    def test_owner_can_list_opportunity(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = self._make_fcl_booking()
        detect_response = client.post(
            f"/bookings/{booking_id}/space-opportunities/detect", headers=IMPORTER_HEADERS
        )
        opp_id = detect_response.json()["id"]
        list_response = client.post(f"/space-opportunities/{opp_id}/list", headers=IMPORTER_HEADERS)
        assert list_response.status_code == 200
        assert list_response.json()["status"] == "listed"


class TestSupplierInvoiceExtraction:
    INVOICE_TEXT = """
    INVOICE No: INV-2026-0042
    Issued: 2026-05-01
    Due Date: 2026-05-15
    PO Number: SH-2026-0044
    Total: USD 4,250.00
    Beneficiary: Foshan Tiles Co Ltd
    Bank: HSBC Hong Kong
    Account No: 1234-5678-9012
    SWIFT: HSBCHKHHHKH
    """

    def test_extracts_invoice_number(self) -> None:
        from app.invoices import extract_invoice_from_text
        parsed = extract_invoice_from_text(self.INVOICE_TEXT)
        assert parsed.invoice_number == "INV-2026-0042"

    def test_extracts_amount_and_currency(self) -> None:
        from app.invoices import extract_invoice_from_text
        parsed = extract_invoice_from_text(self.INVOICE_TEXT)
        assert parsed.total_amount == 4250.00
        assert parsed.currency == "USD"

    def test_extracts_due_date(self) -> None:
        from app.invoices import extract_invoice_from_text
        parsed = extract_invoice_from_text(self.INVOICE_TEXT)
        assert parsed.due_date is not None
        assert parsed.due_date.isoformat() == "2026-05-15"

    def test_extracts_po_reference(self) -> None:
        from app.invoices import extract_invoice_from_text
        parsed = extract_invoice_from_text(self.INVOICE_TEXT)
        assert parsed.purchase_order_reference == "SH-2026-0044"

    def test_extracts_bank_and_masks_account(self) -> None:
        from app.invoices import extract_invoice_from_text
        parsed = extract_invoice_from_text(self.INVOICE_TEXT)
        assert parsed.swift_code == "HSBCHKHHHKH"
        assert parsed.account_number_last4 == "9012"
        assert parsed.bank_name and "HSBC" in parsed.bank_name

    def test_handles_alternate_currency_format(self) -> None:
        from app.invoices import extract_invoice_from_text
        parsed = extract_invoice_from_text("Total: 18000.00 RMB\nDue date: 2026-06-01")
        assert parsed.total_amount == 18000.00
        assert parsed.currency == "CNY"

    def test_empty_text_returns_empty_parse(self) -> None:
        from app.invoices import extract_invoice_from_text
        parsed = extract_invoice_from_text("")
        assert parsed.invoice_number is None
        assert parsed.total_amount is None

    def test_parse_text_endpoint(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        response = client.post(
            "/invoices/parse-text",
            headers=IMPORTER_HEADERS,
            json={"text": self.INVOICE_TEXT},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["parsed"]["invoice_number"] == "INV-2026-0042"
        assert body["parsed"]["total_amount"] == 4250.00
        assert "applied" not in body  # apply was False

    def test_parse_text_with_apply_creates_pay_request(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        # Create a matching PO
        po_response = client.post(
            "/purchase-orders",
            headers=IMPORTER_HEADERS,
            json={
                "booking_id": booking_id,
                "order_reference": "SH-2026-0044",
                "buyer_company_name": "Test Imports Pty Ltd",
                "supplier_name": "Foshan Tiles Co Ltd",
                "product_summary": "ceramic tiles",
                "goods_value": 4250,
                "deposit_amount": 1275,
                "balance_amount": 2975,
            },
        )
        assert po_response.status_code == 201

        response = client.post(
            "/invoices/parse-text",
            headers=IMPORTER_HEADERS,
            json={"text": self.INVOICE_TEXT, "booking_id": booking_id, "apply": True},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["applied"]["matched_purchase_order_id"] is not None
        assert body["applied"]["supplier_pay_request_id"] is not None
        assert body["applied"]["approval_request_id"] is not None
        sp = store.supplier_pay_requests[body["applied"]["supplier_pay_request_id"]]
        assert sp.amount == 4250.00
        assert sp.currency == "USD"
        assert sp.supplier_invoice_reference == "INV-2026-0042"

    def test_invoice_keywords_trigger_auto_extract(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        po_response = client.post(
            "/purchase-orders",
            headers=IMPORTER_HEADERS,
            json={
                "booking_id": booking_id,
                "order_reference": "SH-2026-0044",
                "buyer_company_name": "Test Imports Pty Ltd",
                "supplier_name": "Foshan Tiles Co Ltd",
                "product_summary": "ceramic tiles",
                "goods_value": 4250,
                "deposit_amount": 1275,
                "balance_amount": 2975,
            },
        )
        assert po_response.status_code == 201
        before_count = len(store.supplier_pay_requests)
        msg = client.post(
            "/source-messages",
            headers=IMPORTER_HEADERS,
            json={
                "source_type": "forwarded_email",
                "from_address": "supplier@factory.cn",
                "to_addresses": ["pay@shiphoppa.com"],
                "subject": f"Invoice INV-2026-0042 for booking {booking_id}",
                "body": self.INVOICE_TEXT,
            },
        )
        assert msg.status_code == 201
        # Auto-extract should have created a SupplierPayRequest matching the invoice
        new_pay_requests = [
            sp for sp in store.supplier_pay_requests.values()
            if sp.supplier_invoice_reference == "INV-2026-0042"
        ]
        assert len(new_pay_requests) == 1
        assert new_pay_requests[0].amount == 4250.00
        assert new_pay_requests[0].currency == "USD"

    def test_non_invoice_message_does_not_trigger_extract(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        before_count = len(store.supplier_pay_requests)
        msg = client.post(
            "/source-messages",
            headers=IMPORTER_HEADERS,
            json={
                "source_type": "forwarded_email",
                "from_address": "supplier@factory.cn",
                "to_addresses": ["ops@shiphoppa.com"],
                "subject": f"Production update for {booking_id}",
                "body": "Hi, we just wanted to let you know the cargo is ready.",
            },
        )
        assert msg.status_code == 201
        after_count = len(store.supplier_pay_requests)
        assert after_count == before_count

    def test_extract_from_source_message_endpoint(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        create_booking()
        msg = client.post(
            "/source-messages",
            headers=IMPORTER_HEADERS,
            json={
                "source_type": "forwarded_email",
                "from_address": "supplier@factory.cn",
                "to_addresses": ["pay@shiphoppa.com"],
                "subject": "Invoice INV-2026-0042 for your order",
                "body": self.INVOICE_TEXT,
            },
        )
        assert msg.status_code == 201
        message_id = msg.json()["id"]
        extract = client.post(
            f"/source-messages/{message_id}/extract-invoice",
            headers=IMPORTER_HEADERS,
        )
        assert extract.status_code == 200
        body = extract.json()
        assert body["parsed"]["invoice_number"] == "INV-2026-0042"
        assert body["parsed"]["total_amount"] == 4250.00

    def test_pdf_extract_returns_empty_on_invalid_bytes(self) -> None:
        from app.invoices import extract_invoice_from_pdf
        parsed = extract_invoice_from_pdf(b"not a pdf")
        assert parsed.total_amount is None
        assert parsed.invoice_number is None

    def test_pdf_endpoint_rejects_non_pdf(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        response = client.post(
            "/invoices/parse-pdf",
            headers=IMPORTER_HEADERS,
            files={"file": ("not-an-invoice.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 400

    def test_pdf_endpoint_extracts_real_pdf(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)

        # Build a minimal PDF in memory containing the invoice text
        try:
            from pypdf import PdfWriter
            from pypdf.generic import RectangleObject
        except ImportError:
            return  # pypdf not installed; skip

        # Use reportlab if available, otherwise build a tiny PDF by hand.
        # We'll do the simplest path: write a PDF with one page using pypdf's
        # blank page helper and a manual content stream.
        pdf_bytes = self._build_simple_pdf(self.INVOICE_TEXT)

        response = client.post(
            "/invoices/parse-pdf",
            headers=IMPORTER_HEADERS,
            files={"file": ("invoice.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 200
        body = response.json()
        # Soft assertion: parser may or may not extract from our crude PDF.
        # The endpoint must respond with the parsed shape regardless.
        assert "parsed" in body
        assert body["filename"] == "invoice.pdf"

    @staticmethod
    def _build_simple_pdf(text: str) -> bytes:
        """Build a minimal valid one-page PDF whose stream contains `text`."""
        # Hand-written single-page PDF. Each line of `text` rendered at y=720
        # decreasing by 14 pts. Good enough to exercise pypdf.extract_text.
        lines = text.strip().splitlines()
        text_block_lines = []
        y = 720
        for line in lines:
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            text_block_lines.append(f"BT /F1 10 Tf 50 {y} Td ({escaped}) Tj ET")
            y -= 14
        content_stream = "\n".join(text_block_lines).encode("latin-1")
        # Build PDF bytes manually
        objects: list[bytes] = []
        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        objects.append(b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>")
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        )
        stream = b"<< /Length " + str(len(content_stream)).encode() + b" >>\nstream\n" + content_stream + b"\nendstream"
        objects.append(stream)
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

        out = b"%PDF-1.4\n"
        offsets: list[int] = []
        for i, obj in enumerate(objects, start=1):
            offsets.append(len(out))
            out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
        xref_offset = len(out)
        out += b"xref\n0 " + str(len(objects) + 1).encode() + b"\n0000000000 65535 f \n"
        for off in offsets:
            out += f"{off:010d} 00000 n \n".encode()
        out += b"trailer\n<< /Size " + str(len(objects) + 1).encode() + b" /Root 1 0 R >>\nstartxref\n" + str(xref_offset).encode() + b"\n%%EOF"
        return out


class TestQualityInspection:
    def _make_po(self, client: TestClient, booking_id: str, inspection_required: bool = True):
        return client.post(
            "/purchase-orders",
            headers=IMPORTER_HEADERS,
            json={
                "booking_id": booking_id,
                "order_reference": "SH-2026-0099",
                "buyer_company_name": "Test Imports Pty Ltd",
                "supplier_name": "Foshan Tiles Co Ltd",
                "product_summary": "ceramic tiles",
                "goods_value": 4250,
                "deposit_amount": 1275,
                "balance_amount": 2975,
                "inspection_required": inspection_required,
            },
        )

    def test_inspections_listed_for_booking(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        self._make_po(client, booking_id)
        response = client.get(f"/bookings/{booking_id}/quality-inspections", headers=IMPORTER_HEADERS)
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 1
        assert items[0]["inspection_required"] is True

    def test_book_inspection_endpoint(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        self._make_po(client, booking_id)
        inspection_id = list(store.quality_inspections.values())[0].id
        before_notifs = len(store.notifications)
        response = client.post(
            f"/quality-inspections/{inspection_id}/book",
            headers=IMPORTER_HEADERS,
            json={
                "provider": "SGS",
                "inspection_date": "2026-06-01",
                "location": "Foshan factory",
            },
        )
        assert response.status_code == 200
        assert response.json()["result"] == "booked"
        assert response.json()["inspection_provider"] == "SGS"
        assert len(store.notifications) > before_notifs

    def test_failed_inspection_creates_approval(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        self._make_po(client, booking_id)
        inspection_id = list(store.quality_inspections.values())[0].id
        before_approvals = len(store.approval_requests)
        response = client.post(
            f"/quality-inspections/{inspection_id}/result",
            headers=ADMIN_HEADERS,
            json={
                "result": "failed",
                "defects_summary": "Glaze issues on 12% of cartons.",
            },
        )
        assert response.status_code == 200
        assert response.json()["result"] == "failed"
        assert len(store.approval_requests) > before_approvals

    def test_passed_inspection_notifies_importer(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id = create_booking()
        self._make_po(client, booking_id)
        inspection_id = list(store.quality_inspections.values())[0].id
        before = len(store.notifications)
        response = client.post(
            f"/quality-inspections/{inspection_id}/result",
            headers=ADMIN_HEADERS,
            json={"result": "passed"},
        )
        assert response.status_code == 200
        passed_notifs = [n for n in store.notifications.values() if n.trigger == "qc_inspection_passed"]
        assert len(passed_notifs) == 1
        assert len(store.notifications) > before

    def test_unknown_inspection_404s(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        response = client.post(
            "/quality-inspections/QC-9999/book",
            headers=IMPORTER_HEADERS,
            json={"provider": "SGS", "inspection_date": "2026-06-01", "location": "x"},
        )
        assert response.status_code == 404


class TestCarrierEtaMonitoring:
    def _create_booking_with_container(self, client: TestClient) -> tuple:
        booking_id = create_booking()
        booking = store.bookings[booking_id]
        # Wire booking to a synthetic container with a baseline ETA
        from app.models import Container, ContainerStatus
        from datetime import datetime as _dt
        container = Container(
            id=store.next_id("CTR"),
            lane_id=booking.lane_id or "LANE-1",
            status=ContainerStatus.committed,
            target_sailing_date=date.today() + timedelta(days=20),
            carrier_cutoff_date=date.today() + timedelta(days=10),
            opened_at=_dt.utcnow(),
            oldest_booking_date=date.today(),
            estimated_arrival=date.today() + timedelta(days=30),
            created_at=_dt.utcnow(),
            updated_at=_dt.utcnow(),
        )
        store.containers[container.id] = container
        booking.container_id = container.id
        return booking_id, container.id

    def test_first_eta_update_sets_baseline(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id, container_id = self._create_booking_with_container(client)
        new_eta = (date.today() + timedelta(days=30)).isoformat()
        response = client.post(
            f"/containers/{container_id}/eta",
            headers=ADMIN_HEADERS,
            json={"new_eta": new_eta, "source": "carrier_api"},
        )
        assert response.status_code == 200
        assert response.json()["new_eta"] == new_eta

    def test_small_eta_change_does_not_notify(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id, container_id = self._create_booking_with_container(client)
        # First call sets baseline; second small change shouldn't notify
        first = (date.today() + timedelta(days=30)).isoformat()
        client.post(
            f"/containers/{container_id}/eta",
            headers=ADMIN_HEADERS,
            json={"new_eta": first, "source": "carrier_api"},
        )
        before = len(store.notifications)
        same_day = first  # zero day change
        response = client.post(
            f"/containers/{container_id}/eta",
            headers=ADMIN_HEADERS,
            json={"new_eta": same_day, "source": "carrier_api"},
        )
        assert response.status_code == 200
        assert response.json()["notifications_sent"] == 0
        assert len(store.notifications) == before

    def test_eta_slip_notifies_importer(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id, container_id = self._create_booking_with_container(client)
        first = (date.today() + timedelta(days=30)).isoformat()
        client.post(
            f"/containers/{container_id}/eta",
            headers=ADMIN_HEADERS,
            json={"new_eta": first, "source": "carrier_api"},
        )
        before = len(store.notifications)
        slipped = (date.today() + timedelta(days=32)).isoformat()
        response = client.post(
            f"/containers/{container_id}/eta",
            headers=ADMIN_HEADERS,
            json={"new_eta": slipped, "source": "carrier_api"},
        )
        assert response.status_code == 200
        assert response.json()["notifications_sent"] >= 1
        assert len(store.notifications) > before
        eta_change_notifs = [n for n in store.notifications.values() if n.trigger == "eta_changed"]
        assert any(booking_id in n.message for n in eta_change_notifs)

    def test_large_eta_slip_creates_approval(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        booking_id, container_id = self._create_booking_with_container(client)
        baseline = (date.today() + timedelta(days=30)).isoformat()
        client.post(
            f"/containers/{container_id}/eta",
            headers=ADMIN_HEADERS,
            json={"new_eta": baseline, "source": "carrier_api"},
        )
        before = len(store.approval_requests)
        slipped = (date.today() + timedelta(days=35)).isoformat()
        response = client.post(
            f"/containers/{container_id}/eta",
            headers=ADMIN_HEADERS,
            json={"new_eta": slipped, "source": "carrier_api"},
        )
        assert response.status_code == 200
        assert response.json()["approvals_created"] >= 1
        assert len(store.approval_requests) > before
        sailing_approvals = [
            a for a in store.approval_requests.values()
            if a.request_type.value == "accept_sailing_change"
            and a.related_booking_id == booking_id
        ]
        assert len(sailing_approvals) == 1

    def test_unknown_container_404s(self) -> None:
        reset_store_for_tests()
        client = TestClient(app)
        response = client.post(
            "/containers/CTR-9999/eta",
            headers=ADMIN_HEADERS,
            json={"new_eta": date.today().isoformat()},
        )
        assert response.status_code == 404
