import os
from pathlib import Path
from datetime import date
from typing import Callable, List, Optional, TypeVar

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .algorithms import (
    CATEGORY_DENSITY_DEFAULTS,
    commit_container,
    confirm_booking,
    rank_carrier_options,
    release_reasons,
    run_release_checks,
    submit_booking,
)
from .auth import Principal, require_admin, require_cron, require_importer, require_inbound_webhook
from .automation import (
    AutomationResult,
    ExtractedFact,
    MissingDataItem,
    ShipmentLifecycleState,
    apply_extracted_facts,
    check_stale_shipments,
    derive_lifecycle_state,
    detect_missing_data,
    next_action_for_state,
    run_automation_for_booking,
    run_extraction_for_message,
    run_full_automation_cycle,
    try_advance_booking_status,
)
from .models import (
    AccountIntegration,
    AccountIntegrationProvider,
    AccountIntegrationUpdate,
    AccountProfile,
    AccountProfileUpdate,
    AdminTask,
    AdminTaskStatus,
    ApprovalDecisionRequest,
    ApprovalReviewRequest,
    ApprovalRequest,
    ApprovalStatus,
    AuditEvent,
    ActorRole,
    Booking,
    BookingChecklistResponse,
    BookingCreate,
    BookingStatus,
    CarrierOption,
    CommitContainerRequest,
    ConfirmBookingResponse,
    Container,
    CustomsProfile,
    CustomsProfileUpdate,
    DashboardSummary,
    DeliveryPlan,
    DeliveryPlanUpdate,
    DocumentDecisionRequest,
    DocumentStatus,
    DocumentUploadRequest,
    ImportProject,
    ImportProjectWorkspaceResponse,
    Invoice,
    Lane,
    MatchResult,
    Notification,
    OutboundMessage,
    OutboundMessageCreate,
    OutboundStatus,
    ProductionMilestone,
    ProductionMilestoneCompleteRequest,
    PurchaseOrder,
    PurchaseOrderCreate,
    QualityInspection,
    QualityInspectionResult,
    ReleaseHold,
    ReleaseCheckResult,
    ReleaseStatusResponse,
    SailingSearchResult,
    SEOOpportunity,
    SEOOpportunityCreate,
    SentinelErrorDefinition,
    ShipmentDocument,
    ShipmentEvent,
    ShipmentEventCreate,
    SourceMessage,
    SourceMessageCreate,
    SpaceOpportunity,
    SupplierDiscoveryRun,
    SupplierAccessLink,
    SupplierLead,
    SupplierLinkCreate,
    SupplierPayMarkPaidRequest,
    SupplierPayQuote,
    ShipmentSummary,
    ShipmentWorkspace,
    SupplierPayRequest,
    SupplierPayRequestCreate,
    SupplierPortalResponse,
    SupplierReadyRequest,
    SystemHealthResponse,
    BrokerAccessLink,
    BrokerClearanceUpdate,
    BrokerLinkCreate,
    BrokerPortalResponse,
    WarehouseAccessLink,
    WarehouseLinkCreate,
    WarehousePortalResponse,
    WarehouseReceiptUpdate,
    CarrierAccessLink,
    CarrierLinkCreate,
    CarrierEtaUpdate,
    CarrierEventUpdate,
    CarrierPortalResponse,
    TruckerAccessLink,
    TruckerLinkCreate,
    TruckerPortalResponse,
    TruckerStatusUpdate,
    InboundEmailWebhook,
    SourceMessageType,
    ImportProjectCreate,
    ImportProjectStatus,
    ImportProjectUpdate,
    SupplierVerificationUpdate,
    GrowthAttributionCreate,
    GrowthAttributionEvent,
    GrowthAttributionEventType,
    GrowthAttributionSummary,
)
from .customs import HSCodeSuggestion, best_suggestion, suggest_hs_code
from .invoices import ParsedInvoice, extract_invoice_from_pdf, extract_invoice_from_text
from .operations import (
    apply_parsed_invoice,
    approve_space_opportunity_listing,
    book_quality_inspection,
    checklist_for_booking,
    complete_production_milestone,
    create_shipment_event,
    create_supplier_link,
    create_purchase_order,
    clone_purchase_order,
    detect_fcl_spare_space,
    dispatch_outbound_message,
    landed_cost_summary,
    list_quality_inspections_for_booking,
    list_shipment_summaries,
    list_space_opportunities_for_booking,
    record_quality_inspection_result,
    record_warehouse_measurement,
    update_container_eta,
    create_supplier_pay_request,
    decide_document,
    decide_approval_request,
    ensure_account_integrations,
    ensure_account_profile,
    ensure_customs_profile,
    ensure_delivery_plan,
    ensure_invoice,
    events_for_booking,
    mark_invoice_paid,
    mark_supplier_pay_paid_outside_app,
    mark_delivery_delivered,
    release_status_for_booking,
    request_approval_review,
    sailing_search,
    shipment_workspace,
    create_seo_opportunity,
    create_supplier_discovery_run_from_opportunity,
    ensure_import_project_for_booking,
    import_project_workspace,
    ingest_source_message,
    queue_outbound_message,
    supplier_portal,
    supplier_portal_preview,
    supplier_ready,
    supplier_link_by_token,
    broker_clearance_update,
    broker_link_by_token,
    broker_portal,
    create_broker_link,
    create_warehouse_link,
    warehouse_link_by_token,
    warehouse_portal,
    warehouse_receipt_update,
    create_carrier_link,
    carrier_link_by_token,
    carrier_portal,
    carrier_eta_update,
    carrier_event_update,
    create_trucker_link,
    trucker_link_by_token,
    trucker_portal,
    trucker_status_update,
    create_import_project,
    update_import_project,
    clone_import_project,
    soft_delete_import_project,
    update_supplier_lead_verification,
    create_growth_event,
    filter_growth_attribution_events,
    summarise_growth_attribution,
    update_account_integration,
    update_account_profile,
    update_customs_profile,
    update_delivery_plan,
    upload_document,
    waive_release_hold,
    book_delivery_plan,
)
from .persistence import load_store_snapshot, save_store_snapshot, snapshot_enabled
from .providers import provider_readiness
from .sentinel import sentinel_error_definitions, system_health
from .seed import seed_data
from .store import Store


app = FastAPI(title="Ship Hoppa MCL Platform", version="0.1.0")


def allowed_origins() -> List[str]:
    configured_origins = os.getenv("SHIP_HOPPA_ALLOWED_ORIGINS")
    if configured_origins:
        return [origin.strip().rstrip("/") for origin in configured_origins.split(",") if origin.strip()]
    return ["http://localhost:5173", "http://127.0.0.1:5173"]


def allowed_origin_regex() -> Optional[str]:
    return os.getenv("SHIP_HOPPA_ALLOWED_ORIGIN_REGEX") or None

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_origin_regex=allowed_origin_regex(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def boot_store() -> Store:
    booted_store = Store()
    if snapshot_enabled() and load_store_snapshot(booted_store):
        return booted_store
    seed_data(booted_store)
    if snapshot_enabled():
        save_store_snapshot(booted_store)
    return booted_store


store = boot_store()
T = TypeVar("T")


def persist_store() -> None:
    if snapshot_enabled():
        save_store_snapshot(store)


def persist_result(result: T) -> T:
    persist_store()
    return result


def reset_store_for_tests() -> None:
    store.lanes.clear()
    store.importers.clear()
    store.account_profiles.clear()
    store.account_integrations.clear()
    store.bookings.clear()
    store.containers.clear()
    store.carrier_services.clear()
    store.sailing_options.clear()
    store.warehouses.clear()
    store.document_requirements.clear()
    store.shipment_documents.clear()
    store.shipment_events.clear()
    store.supplier_links.clear()
    store.broker_links.clear()
    store.warehouse_links.clear()
    store.carrier_links.clear()
    store.trucker_links.clear()
    store.invoices.clear()
    store.payment_records.clear()
    store.release_holds.clear()
    store.customs_profiles.clear()
    store.delivery_plans.clear()
    store.admin_tasks.clear()
    store.purchase_orders.clear()
    store.production_milestones.clear()
    store.quality_inspections.clear()
    store.supplier_pay_requests.clear()
    store.supplier_pay_quotes.clear()
    store.import_projects.clear()
    store.import_project_steps.clear()
    store.import_project_versions.clear()
    store.import_project_snapshots.clear()
    store.import_project_events.clear()
    store.import_project_files.clear()
    store.source_messages.clear()
    store.automation_runs.clear()
    store.approval_requests.clear()
    store.outbound_messages.clear()
    store.seo_opportunities.clear()
    store.supplier_discovery_runs.clear()
    store.supplier_leads.clear()
    store.growth_attribution_events.clear()
    store.notifications.clear()
    store.audit_events.clear()
    store.space_opportunities.clear()
    store.idempotency_records.clear()
    store._counters.clear()
    seed_data(store)


def idempotent(scope: str, key: Optional[str], producer: Callable[[], T]) -> T:
    if not key:
        return producer()
    scoped_key = f"{scope}:{key}"
    if scoped_key in store.idempotency_records:
        return store.idempotency_records[scoped_key]
    result = producer()
    store.idempotency_records[scoped_key] = result
    return result


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "ship-hoppa-api", "snapshot_persistence": snapshot_enabled()}


@app.get("/system/health", response_model=SystemHealthResponse)
def get_system_health(_principal: Principal = Depends(require_admin)) -> SystemHealthResponse:
    return system_health(store)


@app.get("/sentinel/error-codes", response_model=List[SentinelErrorDefinition])
def sentinel_error_codes(_principal: Principal = Depends(require_admin)) -> List[SentinelErrorDefinition]:
    return sentinel_error_definitions()


@app.get("/summary", response_model=DashboardSummary)
def summary(_principal: Principal = Depends(require_admin)) -> DashboardSummary:
    open_revenue = sum((booking.total_cost_usd or 0) for booking in store.bookings.values())
    outstanding = sum((booking.total_cost_usd or 0) for booking in store.bookings.values() if not booking.paid)
    notifications = sorted(store.notifications.values(), key=lambda item: item.created_at, reverse=True)[:8]
    audit_events = sorted(store.audit_events.values(), key=lambda item: item.created_at, reverse=True)[:10]
    return DashboardSummary(
        lanes=len(store.lanes),
        bookings=len(store.bookings),
        containers=len(store.containers),
        committed_containers=sum(1 for container in store.containers.values() if container.status == "committed"),
        import_projects=len(store.import_projects),
        source_messages=len(store.source_messages),
        supplier_leads=len(store.supplier_leads),
        open_approvals=sum(1 for approval in store.approval_requests.values() if approval.status == "pending"),
        open_revenue_usd=round(open_revenue, 2),
        outstanding_payments_usd=round(outstanding, 2),
        notifications=notifications,
        audit_events=audit_events,
        category_density_defaults={key.value: value for key, value in CATEGORY_DENSITY_DEFAULTS.items()},
    )


@app.get("/lanes", response_model=List[Lane])
def lanes(_principal: Principal = Depends(require_importer)) -> List[Lane]:
    return list(store.lanes.values())


@app.get("/account/profile", response_model=AccountProfile)
def account_profile(principal: Principal = Depends(require_importer)) -> AccountProfile:
    return persist_result(ensure_account_profile(store, principal.actor_id))


@app.put("/account/profile", response_model=AccountProfile)
def put_account_profile(
    payload: AccountProfileUpdate,
    principal: Principal = Depends(require_importer),
) -> AccountProfile:
    return persist_result(update_account_profile(store, principal.actor_id, payload))


@app.get("/account/integrations", response_model=List[AccountIntegration])
def account_integrations(principal: Principal = Depends(require_importer)) -> List[AccountIntegration]:
    return persist_result(ensure_account_integrations(store, principal.actor_id))


@app.put("/account/integrations/{provider}", response_model=AccountIntegration)
def put_account_integration(
    provider: AccountIntegrationProvider,
    payload: AccountIntegrationUpdate,
    principal: Principal = Depends(require_importer),
) -> AccountIntegration:
    try:
        return persist_result(update_account_integration(store, principal.actor_id, provider, payload))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/containers", response_model=List[Container])
def containers(_principal: Principal = Depends(require_admin)) -> List[Container]:
    return sorted(store.containers.values(), key=lambda item: item.target_sailing_date)


@app.get("/bookings", response_model=List[Booking])
def bookings(_principal: Principal = Depends(require_admin)) -> List[Booking]:
    return sorted(store.bookings.values(), key=lambda item: item.created_at, reverse=True)


@app.get("/shipments", response_model=List[ShipmentSummary])
def shipments(_principal: Principal = Depends(require_importer)) -> List[ShipmentSummary]:
    return list_shipment_summaries(store)


@app.get("/shipments/{booking_id}/workspace", response_model=ShipmentWorkspace)
def shipment_workspace_endpoint(
    booking_id: str,
    _principal: Principal = Depends(require_importer),
) -> ShipmentWorkspace:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return shipment_workspace(store, booking_id)


@app.get("/import-projects", response_model=List[ImportProject])
def import_projects(
    include_deleted: bool = False,
    _principal: Principal = Depends(require_importer),
) -> List[ImportProject]:
    deleted_statuses = {ImportProjectStatus.deleted_pending_retention, ImportProjectStatus.deleted}
    projects = [
        project for project in store.import_projects.values()
        if include_deleted or project.status not in deleted_statuses
    ]
    return sorted(projects, key=lambda item: item.updated_at, reverse=True)


@app.post("/import-projects", response_model=ImportProject, status_code=201)
def post_import_project(
    payload: ImportProjectCreate,
    principal: Principal = Depends(require_importer),
) -> ImportProject:
    return persist_result(create_import_project(store, payload, principal.role, principal.actor_id))


@app.patch("/import-projects/{project_id}", response_model=ImportProject)
def patch_import_project(
    project_id: str,
    payload: ImportProjectUpdate,
    principal: Principal = Depends(require_importer),
) -> ImportProject:
    try:
        return persist_result(update_import_project(store, project_id, payload, principal.role, principal.actor_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/import-projects/{project_id}/clone", response_model=ImportProject, status_code=201)
def post_clone_import_project(
    project_id: str,
    principal: Principal = Depends(require_importer),
    new_title: Optional[str] = None,
) -> ImportProject:
    try:
        return persist_result(clone_import_project(store, project_id, principal.role, principal.actor_id, new_title))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.delete("/import-projects/{project_id}", response_model=ImportProject)
def delete_import_project(
    project_id: str,
    principal: Principal = Depends(require_importer),
) -> ImportProject:
    try:
        return persist_result(soft_delete_import_project(store, project_id, principal.role, principal.actor_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/import-projects/{project_id}", response_model=ImportProjectWorkspaceResponse)
def get_import_project(project_id: str, _principal: Principal = Depends(require_importer)) -> ImportProjectWorkspaceResponse:
    if project_id not in store.import_projects:
        raise HTTPException(status_code=404, detail="Import project not found")
    return ImportProjectWorkspaceResponse(**import_project_workspace(store, project_id))


@app.get("/bookings/{booking_id}/import-project", response_model=ImportProjectWorkspaceResponse)
def booking_import_project(booking_id: str, _principal: Principal = Depends(require_importer)) -> ImportProjectWorkspaceResponse:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    project = ensure_import_project_for_booking(store, store.bookings[booking_id])
    return persist_result(ImportProjectWorkspaceResponse(**import_project_workspace(store, project.id)))


@app.get("/notifications", response_model=List[Notification])
def notifications(_principal: Principal = Depends(require_importer)) -> List[Notification]:
    return sorted(store.notifications.values(), key=lambda item: item.created_at, reverse=True)


@app.post("/notifications/mark-all-read")
def mark_all_notifications_read(_principal: Principal = Depends(require_importer)) -> dict:
    marked = 0
    for notification in store.notifications.values():
        if not notification.read:
            notification.read = True
            marked += 1
    return {"marked_read": marked}


@app.post("/notifications/{notification_id}/read", response_model=Notification)
def mark_notification_read(
    notification_id: str, _principal: Principal = Depends(require_importer)
) -> Notification:
    notification = store.notifications.get(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.read = True
    return notification


@app.get("/audit-events", response_model=List[AuditEvent])
def audit_events(
    actor_id: Optional[str] = None,
    actor_role: Optional[ActorRole] = None,
    event_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    since: Optional[date] = None,
    until: Optional[date] = None,
    limit: int = 200,
    _principal: Principal = Depends(require_admin),
) -> List[AuditEvent]:
    """Return audit events newest-first, with optional filtering by actor, event,
    entity, or date range. The default limit is 200; pass `limit=0` for all."""
    events = list(store.audit_events.values())
    if actor_id:
        events = [event for event in events if event.actor_id == actor_id]
    if actor_role:
        events = [event for event in events if event.actor_role == actor_role]
    if event_type:
        events = [event for event in events if event.event_type == event_type]
    if entity_type:
        events = [event for event in events if event.entity_type == entity_type]
    if entity_id:
        events = [event for event in events if event.entity_id == entity_id]
    if since:
        events = [event for event in events if event.created_at.date() >= since]
    if until:
        events = [event for event in events if event.created_at.date() <= until]
    events.sort(key=lambda item: item.created_at, reverse=True)
    if limit and limit > 0:
        events = events[:limit]
    return events


@app.get("/source-messages", response_model=List[SourceMessage])
def source_messages(_principal: Principal = Depends(require_importer)) -> List[SourceMessage]:
    return sorted(store.source_messages.values(), key=lambda item: item.received_at, reverse=True)


@app.get("/outbound-messages", response_model=List[OutboundMessage])
def outbound_messages(_principal: Principal = Depends(require_admin)) -> List[OutboundMessage]:
    return sorted(store.outbound_messages.values(), key=lambda item: item.created_at, reverse=True)


@app.post("/outbound-messages", response_model=OutboundMessage, status_code=201)
def post_outbound_message(
    payload: OutboundMessageCreate,
    principal: Principal = Depends(require_admin),
) -> OutboundMessage:
    try:
        return persist_result(queue_outbound_message(store, payload, principal.role, principal.actor_id))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.post("/outbound-messages/{message_id}/dispatch", response_model=OutboundMessage)
def post_dispatch_outbound_message(
    message_id: str,
    _principal: Principal = Depends(require_admin),
) -> OutboundMessage:
    try:
        return persist_result(dispatch_outbound_message(store, message_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/outbound-messages/dispatch-queue")
def post_dispatch_outbound_queue(
    limit: int = 50, _principal: Principal = Depends(require_admin)
) -> dict:
    """Try to dispatch up to `limit` queued outbound messages."""
    queued = [m for m in store.outbound_messages.values() if m.status == OutboundStatus.queued]
    queued.sort(key=lambda m: m.created_at)
    queued = queued[:limit]
    sent = 0
    failed = 0
    deferred = 0
    for msg in queued:
        result = dispatch_outbound_message(store, msg.id)
        if result.status == OutboundStatus.sent:
            sent += 1
        elif result.status == OutboundStatus.failed:
            failed += 1
        else:
            deferred += 1
    persist_store()
    return {"attempted": len(queued), "sent": sent, "failed": failed, "deferred": deferred}


@app.get("/system/providers")
def get_provider_readiness(_principal: Principal = Depends(require_admin)) -> dict:
    return provider_readiness()


class TestEmailRequest(BaseModel):
    to: str
    subject: str = "Ship Hoppa is live"
    body: str = "If you're reading this, the Resend wiring works."


class TestSmsRequest(BaseModel):
    to: str
    body: str = "Ship Hoppa SMS test."


@app.post("/system/test-provider/email")
def test_provider_email(payload: TestEmailRequest, _principal: Principal = Depends(require_admin)) -> dict:
    from .providers import send_email_via_resend
    return send_email_via_resend([payload.to], payload.subject, payload.body)


@app.post("/system/test-provider/sms")
def test_provider_sms(payload: TestSmsRequest, _principal: Principal = Depends(require_admin)) -> dict:
    from .providers import send_sms_via_twilio
    return send_sms_via_twilio(payload.to, payload.body)


@app.post("/source-messages", response_model=SourceMessage, status_code=201)
def create_source_message(
    payload: SourceMessageCreate,
    principal: Principal = Depends(require_importer),
) -> SourceMessage:
    return persist_result(ingest_source_message(store, payload, principal.role, principal.actor_id))


def _coerce_inbound_address(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        email = value.get("email")
        if isinstance(email, str):
            return email
    return None


def _coerce_inbound_addresses(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        results: List[str] = []
        for item in value:
            email = _coerce_inbound_address(item)
            if email:
                results.append(email)
        return results
    return []


def _coerce_inbound_attachments(value) -> List[str]:
    if not value:
        return []
    if not isinstance(value, list):
        return []
    names: List[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            names.append(item.strip())
        elif isinstance(item, dict):
            filename = item.get("filename") or item.get("name")
            if isinstance(filename, str) and filename.strip():
                names.append(filename.strip())
    return names


def _inbound_email_to_source_message(payload: InboundEmailWebhook) -> SourceMessageCreate:
    from_address = _coerce_inbound_address(payload.from_field) or payload.sender or ""
    if not from_address:
        raise HTTPException(status_code=422, detail="Inbound email has no sender address.")
    to_addresses = _coerce_inbound_addresses(payload.to)
    if not to_addresses and payload.recipient:
        to_addresses = [payload.recipient]
    body = payload.text or payload.body_plain or payload.html or payload.body_html or ""
    return SourceMessageCreate(
        source_type=SourceMessageType.forwarded_email,
        from_address=from_address,
        to_addresses=to_addresses,
        subject=payload.subject or "(no subject)",
        body=body,
        received_at=payload.received_at,
        attachment_names=_coerce_inbound_attachments(payload.attachments),
    )


@app.post("/inbound/email", response_model=SourceMessage, status_code=201)
def inbound_email(
    payload: InboundEmailWebhook,
    principal: Principal = Depends(require_inbound_webhook),
) -> SourceMessage:
    """
    Inbound email webhook. Receives JSON from Resend Inbound, Mailgun, or any
    forwarder that posts a compatible shape. Creates a SourceMessage and runs
    the existing matching / extraction automation.
    """
    source_payload = _inbound_email_to_source_message(payload)
    return persist_result(
        ingest_source_message(store, source_payload, ActorRole.system, principal.actor_id)
    )


@app.get("/approvals", response_model=List[ApprovalRequest])
def approvals(_principal: Principal = Depends(require_importer)) -> List[ApprovalRequest]:
    return sorted(store.approval_requests.values(), key=lambda item: item.created_at, reverse=True)


@app.post("/approvals/{approval_id}/approve", response_model=ApprovalRequest)
def approve_request(
    approval_id: str,
    payload: ApprovalDecisionRequest = ApprovalDecisionRequest(reason="Approved"),
    principal: Principal = Depends(require_importer),
) -> ApprovalRequest:
    try:
        return persist_result(
            decide_approval_request(
                store,
                approval_id,
                ApprovalStatus.approved,
                payload.reason or "Approved",
                payload.decided_by or principal.actor_id,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/approvals/{approval_id}/reject", response_model=ApprovalRequest)
def reject_request(
    approval_id: str,
    payload: ApprovalDecisionRequest = ApprovalDecisionRequest(reason="Rejected"),
    principal: Principal = Depends(require_importer),
) -> ApprovalRequest:
    try:
        return persist_result(
            decide_approval_request(
                store,
                approval_id,
                ApprovalStatus.rejected,
                payload.reason or "Rejected",
                payload.decided_by or principal.actor_id,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/approvals/{approval_id}/request-review", response_model=ApprovalRequest)
def request_approval_review_endpoint(
    approval_id: str,
    payload: ApprovalReviewRequest,
    principal: Principal = Depends(require_importer),
) -> ApprovalRequest:
    try:
        return persist_result(
            request_approval_review(store, approval_id, payload.reason, principal.actor_id)
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if message == "Approval not found" else 400
        raise HTTPException(status_code=status_code, detail=message)


@app.get("/purchase-orders", response_model=List[PurchaseOrder])
def purchase_orders(_principal: Principal = Depends(require_importer)) -> List[PurchaseOrder]:
    return sorted(store.purchase_orders.values(), key=lambda item: item.created_at, reverse=True)


@app.post("/purchase-orders", response_model=PurchaseOrder, status_code=201)
def post_purchase_order(
    payload: PurchaseOrderCreate,
    principal: Principal = Depends(require_importer),
) -> PurchaseOrder:
    try:
        return persist_result(create_purchase_order(store, payload, principal.actor_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/purchase-orders/{purchase_order_id}", response_model=PurchaseOrder)
def get_purchase_order(purchase_order_id: str, _principal: Principal = Depends(require_importer)) -> PurchaseOrder:
    if purchase_order_id not in store.purchase_orders:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return store.purchase_orders[purchase_order_id]


@app.post("/purchase-orders/{purchase_order_id}/clone", response_model=PurchaseOrder, status_code=201)
def clone_po(
    purchase_order_id: str,
    target_project_id: Optional[str] = None,
    new_order_reference: Optional[str] = None,
    principal: Principal = Depends(require_importer),
) -> PurchaseOrder:
    try:
        return persist_result(
            clone_purchase_order(
                store,
                purchase_order_id,
                principal.role,
                principal.actor_id,
                target_project_id=target_project_id,
                new_order_reference=new_order_reference,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# --- Quality inspection ---


class BookInspectionRequest(BaseModel):
    provider: str
    inspection_date: date
    location: str


class InspectionResultRequest(BaseModel):
    result: QualityInspectionResult
    defects_summary: Optional[str] = None


@app.get("/bookings/{booking_id}/quality-inspections", response_model=List[QualityInspection])
def booking_quality_inspections(
    booking_id: str, _principal: Principal = Depends(require_importer)
) -> List[QualityInspection]:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return list_quality_inspections_for_booking(store, booking_id)


@app.post("/quality-inspections/{inspection_id}/book", response_model=QualityInspection)
def post_book_inspection(
    inspection_id: str,
    payload: BookInspectionRequest,
    principal: Principal = Depends(require_importer),
) -> QualityInspection:
    try:
        return persist_result(
            book_quality_inspection(
                store,
                inspection_id,
                payload.provider,
                payload.inspection_date,
                payload.location,
                principal.actor_id,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/quality-inspections/{inspection_id}/result", response_model=QualityInspection)
def post_inspection_result(
    inspection_id: str,
    payload: InspectionResultRequest,
    principal: Principal = Depends(require_admin),
) -> QualityInspection:
    try:
        inspection, _approval = record_quality_inspection_result(
            store,
            inspection_id,
            payload.result,
            payload.defects_summary,
            principal.actor_id,
        )
        persist_store()
        return inspection
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/purchase-orders/{purchase_order_id}/milestones", response_model=List[ProductionMilestone])
def purchase_order_milestones(
    purchase_order_id: str,
    _principal: Principal = Depends(require_importer),
) -> List[ProductionMilestone]:
    if purchase_order_id not in store.purchase_orders:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return sorted(
        [
            milestone
            for milestone in store.production_milestones.values()
            if milestone.purchase_order_id == purchase_order_id
        ],
        key=lambda item: ((item.due_date or date.max), item.created_at),
    )


@app.post("/production-milestones/{milestone_id}/complete", response_model=ProductionMilestone)
def complete_milestone(
    milestone_id: str,
    payload: ProductionMilestoneCompleteRequest = ProductionMilestoneCompleteRequest(),
    principal: Principal = Depends(require_importer),
) -> ProductionMilestone:
    try:
        return persist_result(complete_production_milestone(store, milestone_id, payload, principal.actor_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/supplier-pay-requests", response_model=List[SupplierPayRequest])
def supplier_pay_requests(_principal: Principal = Depends(require_importer)) -> List[SupplierPayRequest]:
    return sorted(store.supplier_pay_requests.values(), key=lambda item: item.created_at, reverse=True)


@app.post(
    "/purchase-orders/{purchase_order_id}/supplier-pay-requests",
    response_model=SupplierPayRequest,
    status_code=201,
)
def post_supplier_pay_request(
    purchase_order_id: str,
    payload: SupplierPayRequestCreate,
    principal: Principal = Depends(require_importer),
) -> SupplierPayRequest:
    try:
        return persist_result(create_supplier_pay_request(store, purchase_order_id, payload, principal.actor_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/supplier-pay-requests/{supplier_pay_request_id}/quotes", response_model=List[SupplierPayQuote])
def supplier_pay_quotes(
    supplier_pay_request_id: str,
    _principal: Principal = Depends(require_importer),
) -> List[SupplierPayQuote]:
    if supplier_pay_request_id not in store.supplier_pay_requests:
        raise HTTPException(status_code=404, detail="Supplier Pay request not found")
    return sorted(
        [
            quote
            for quote in store.supplier_pay_quotes.values()
            if quote.supplier_pay_request_id == supplier_pay_request_id
        ],
        key=lambda item: item.estimated_total,
    )


@app.post("/supplier-pay-requests/{supplier_pay_request_id}/mark-paid", response_model=SupplierPayRequest)
def supplier_pay_mark_paid(
    supplier_pay_request_id: str,
    payload: SupplierPayMarkPaidRequest = SupplierPayMarkPaidRequest(),
    principal: Principal = Depends(require_importer),
) -> SupplierPayRequest:
    try:
        return persist_result(mark_supplier_pay_paid_outside_app(store, supplier_pay_request_id, payload, principal.actor_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/bookings", response_model=MatchResult, status_code=201)
def create_booking(
    payload: BookingCreate,
    idempotency_key: Optional[str] = Header(default=None),
    principal: Principal = Depends(require_importer),
) -> MatchResult:
    if payload.cargo_ready_date_latest < payload.cargo_ready_date_earliest:
        raise HTTPException(status_code=422, detail="Latest ready date must be after earliest ready date.")
    result = idempotent(
        "create-booking",
        idempotency_key,
        lambda: submit_booking(store, payload, actor_role=principal.role, actor_id=principal.actor_id),
    )
    return persist_result(result)


@app.post("/bookings/{booking_id}/confirm", response_model=ConfirmBookingResponse)
def confirm(
    booking_id: str,
    idempotency_key: Optional[str] = Header(default=None),
    _principal: Principal = Depends(require_importer),
) -> ConfirmBookingResponse:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    try:
        return persist_result(idempotent("confirm-booking", idempotency_key, lambda: confirm_booking(store, booking_id)))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.get("/containers/{container_id}/carrier-options", response_model=List[CarrierOption])
def carrier_options(container_id: str, _principal: Principal = Depends(require_admin)) -> List[CarrierOption]:
    if container_id not in store.containers:
        raise HTTPException(status_code=404, detail="Container not found")
    return rank_carrier_options(store, container_id)[:3]


@app.get("/containers/{container_id}/release-reasons", response_model=List[str])
def get_release_reasons(container_id: str, _principal: Principal = Depends(require_admin)) -> List[str]:
    if container_id not in store.containers:
        raise HTTPException(status_code=404, detail="Container not found")
    return release_reasons(store, store.containers[container_id])


@app.post("/containers/{container_id}/commit", response_model=ReleaseCheckResult)
def commit(
    container_id: str,
    payload: CommitContainerRequest = CommitContainerRequest(),
    idempotency_key: Optional[str] = Header(default=None),
    _principal: Principal = Depends(require_admin),
) -> ReleaseCheckResult:
    if container_id not in store.containers:
        raise HTTPException(status_code=404, detail="Container not found")
    result = idempotent("commit-container", idempotency_key, lambda: commit_container(store, container_id, payload))
    if not result.released:
        raise HTTPException(status_code=409, detail=result.reasons)
    return persist_result(result)


class ContainerEtaUpdateRequest(BaseModel):
    new_eta: date
    source: str = "manual_admin"


@app.post("/containers/{container_id}/eta")
def post_container_eta_update(
    container_id: str,
    payload: ContainerEtaUpdateRequest,
    principal: Principal = Depends(require_admin),
) -> dict:
    try:
        result = update_container_eta(
            store,
            container_id,
            payload.new_eta,
            principal.actor_id,
            source=payload.source,
        )
        persist_store()
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/ops/release-checks", response_model=List[ReleaseCheckResult])
def release_checks(_principal: Principal = Depends(require_admin)) -> List[ReleaseCheckResult]:
    return persist_result(run_release_checks(store))


@app.get("/bookings/{booking_id}/checklist", response_model=BookingChecklistResponse)
def booking_checklist(booking_id: str, _principal: Principal = Depends(require_importer)) -> BookingChecklistResponse:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return checklist_for_booking(store, booking_id)


@app.post("/bookings/{booking_id}/documents", response_model=ShipmentDocument, status_code=201)
def upload_booking_document(
    booking_id: str,
    payload: DocumentUploadRequest,
    principal: Principal = Depends(require_importer),
) -> ShipmentDocument:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return persist_result(upload_document(store, booking_id, payload, principal.role, principal.actor_id))


@app.post("/documents/{document_id}/approve", response_model=ShipmentDocument)
def approve_document(
    document_id: str,
    payload: DocumentDecisionRequest = DocumentDecisionRequest(),
    _principal: Principal = Depends(require_admin),
) -> ShipmentDocument:
    if document_id not in store.shipment_documents:
        raise HTTPException(status_code=404, detail="Document not found")
    return persist_result(decide_document(store, document_id, DocumentStatus.approved, payload, "ops"))


@app.post("/documents/{document_id}/reject", response_model=ShipmentDocument)
def reject_document(
    document_id: str,
    payload: DocumentDecisionRequest = DocumentDecisionRequest(),
    _principal: Principal = Depends(require_admin),
) -> ShipmentDocument:
    if document_id not in store.shipment_documents:
        raise HTTPException(status_code=404, detail="Document not found")
    return persist_result(decide_document(store, document_id, DocumentStatus.rejected, payload, "ops"))


@app.get("/bookings/{booking_id}/events", response_model=List[ShipmentEvent])
def booking_events(booking_id: str, _principal: Principal = Depends(require_importer)) -> List[ShipmentEvent]:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return events_for_booking(store, booking_id)


@app.post("/bookings/{booking_id}/events", response_model=ShipmentEvent, status_code=201)
def add_booking_event(
    booking_id: str,
    payload: ShipmentEventCreate,
    _principal: Principal = Depends(require_admin),
) -> ShipmentEvent:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return persist_result(create_shipment_event(store, booking_id, payload))


@app.get("/sailings", response_model=List[SailingSearchResult])
def sailings(_principal: Principal = Depends(require_importer)) -> List[SailingSearchResult]:
    return sailing_search(store)


@app.get("/growth/seo-opportunities", response_model=List[SEOOpportunity])
def seo_opportunities(_principal: Principal = Depends(require_admin)) -> List[SEOOpportunity]:
    return sorted(store.seo_opportunities.values(), key=lambda item: item.created_at, reverse=True)


@app.post("/growth/seo-opportunities", response_model=SEOOpportunity, status_code=201)
def post_seo_opportunity(
    payload: SEOOpportunityCreate,
    principal: Principal = Depends(require_admin),
) -> SEOOpportunity:
    return persist_result(create_seo_opportunity(store, payload, principal.actor_id))


@app.post("/growth/seo-opportunities/{opportunity_id}/discovery-runs", response_model=SupplierDiscoveryRun, status_code=201)
def post_supplier_discovery_run(
    opportunity_id: str,
    _principal: Principal = Depends(require_admin),
) -> SupplierDiscoveryRun:
    if opportunity_id not in store.seo_opportunities:
        raise HTTPException(status_code=404, detail="SEO opportunity not found")
    return persist_result(create_supplier_discovery_run_from_opportunity(store, store.seo_opportunities[opportunity_id]))


@app.get("/growth/supplier-discovery-runs", response_model=List[SupplierDiscoveryRun])
def supplier_discovery_runs(_principal: Principal = Depends(require_admin)) -> List[SupplierDiscoveryRun]:
    return sorted(store.supplier_discovery_runs.values(), key=lambda item: item.created_at, reverse=True)


@app.get("/growth/supplier-leads", response_model=List[SupplierLead])
def supplier_leads(_principal: Principal = Depends(require_admin)) -> List[SupplierLead]:
    return sorted(store.supplier_leads.values(), key=lambda item: item.created_at, reverse=True)


@app.patch("/growth/supplier-leads/{lead_id}/verification", response_model=SupplierLead)
def patch_supplier_lead_verification(
    lead_id: str,
    payload: SupplierVerificationUpdate,
    principal: Principal = Depends(require_admin),
) -> SupplierLead:
    try:
        return persist_result(
            update_supplier_lead_verification(store, lead_id, payload, principal.role, principal.actor_id)
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/growth/attribution-events", response_model=List[GrowthAttributionEvent])
def growth_attribution_events(
    event_type: Optional[GrowthAttributionEventType] = None,
    source: Optional[str] = None,
    channel: Optional[str] = None,
    template_key: Optional[str] = None,
    category: Optional[str] = None,
    region: Optional[str] = None,
    supplier_lead_id: Optional[str] = None,
    shipment_id: Optional[str] = None,
    since: Optional[date] = None,
    until: Optional[date] = None,
    limit: int = 200,
    _principal: Principal = Depends(require_admin),
) -> List[GrowthAttributionEvent]:
    events = filter_growth_attribution_events(
        store,
        event_type=event_type,
        source=source,
        channel=channel,
        template_key=template_key,
        category=category,
        region=region,
        supplier_lead_id=supplier_lead_id,
        shipment_id=shipment_id,
        since=since,
        until=until,
    )
    if limit and limit > 0:
        events = events[:limit]
    return events


@app.post("/growth/attribution-events", response_model=GrowthAttributionEvent, status_code=201)
def post_growth_attribution_event(
    payload: GrowthAttributionCreate,
    _principal: Principal = Depends(require_admin),
) -> GrowthAttributionEvent:
    return persist_result(
        create_growth_event(
            store,
            event_type=payload.event_type,
            source=payload.source,
            supplier_lead_id=payload.supplier_lead_id,
            shipment_id=payload.shipment_id,
            importer_organization_id=payload.importer_organization_id,
            campaign_id=payload.campaign_id,
            channel=payload.channel,
            template_key=payload.template_key,
            category=payload.category,
            region=payload.region,
            value_usd=payload.value_usd,
        )
    )


@app.get("/growth/attribution-summary", response_model=GrowthAttributionSummary)
def growth_attribution_summary(
    group_by: str = "source",
    event_type: Optional[GrowthAttributionEventType] = None,
    since: Optional[date] = None,
    until: Optional[date] = None,
    _principal: Principal = Depends(require_admin),
) -> GrowthAttributionSummary:
    try:
        return GrowthAttributionSummary(**summarise_growth_attribution(
            store, group_by, event_type=event_type, since=since, until=until,
        ))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/supplier-links", response_model=SupplierAccessLink, status_code=201)
def supplier_link(payload: SupplierLinkCreate, _principal: Principal = Depends(require_admin)) -> SupplierAccessLink:
    if payload.booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return persist_result(create_supplier_link(store, payload.booking_id))


@app.get("/bookings/{booking_id}/supplier-preview", response_model=SupplierPortalResponse)
def supplier_portal_preview_endpoint(
    booking_id: str,
    principal: Principal = Depends(require_importer),
) -> SupplierPortalResponse:
    try:
        return persist_result(supplier_portal_preview(store, booking_id, principal.actor_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/supplier/{token}", response_model=SupplierPortalResponse)
def get_supplier_portal(token: str) -> SupplierPortalResponse:
    try:
        return supplier_portal(store, token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/supplier/{token}/ready", response_model=SupplierPortalResponse)
def supplier_ready_update(token: str, payload: SupplierReadyRequest) -> SupplierPortalResponse:
    try:
        return persist_result(supplier_ready(store, token, payload))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/supplier/{token}/documents", response_model=ShipmentDocument, status_code=201)
def supplier_document(token: str, payload: DocumentUploadRequest) -> ShipmentDocument:
    try:
        link = supplier_link_by_token(store, token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return persist_result(upload_document(store, link.booking_id, payload, ActorRole.system, "supplier-portal"))


@app.post("/broker-links", response_model=BrokerAccessLink, status_code=201)
def broker_link(payload: BrokerLinkCreate, _principal: Principal = Depends(require_admin)) -> BrokerAccessLink:
    try:
        return persist_result(create_broker_link(store, payload.booking_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/broker/{token}", response_model=BrokerPortalResponse)
def get_broker_portal(token: str) -> BrokerPortalResponse:
    try:
        return broker_portal(store, token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/broker/{token}/clearance", response_model=BrokerPortalResponse)
def broker_clearance(token: str, payload: BrokerClearanceUpdate) -> BrokerPortalResponse:
    try:
        return persist_result(broker_clearance_update(store, token, payload))
    except ValueError as exc:
        message = str(exc)
        status_code = 400 if "may only" in message else 404
        raise HTTPException(status_code=status_code, detail=message)


@app.post("/broker/{token}/documents", response_model=ShipmentDocument, status_code=201)
def broker_document(token: str, payload: DocumentUploadRequest) -> ShipmentDocument:
    try:
        link = broker_link_by_token(store, token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return persist_result(upload_document(store, link.booking_id, payload, ActorRole.system, "broker-portal"))


@app.post("/warehouse-links", response_model=WarehouseAccessLink, status_code=201)
def warehouse_link(payload: WarehouseLinkCreate, _principal: Principal = Depends(require_admin)) -> WarehouseAccessLink:
    try:
        return persist_result(create_warehouse_link(store, payload.booking_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/warehouse/{token}", response_model=WarehousePortalResponse)
def get_warehouse_portal(token: str) -> WarehousePortalResponse:
    try:
        return warehouse_portal(store, token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/warehouse/{token}/receipt", response_model=WarehousePortalResponse)
def warehouse_receipt(token: str, payload: WarehouseReceiptUpdate) -> WarehousePortalResponse:
    try:
        return persist_result(warehouse_receipt_update(store, token, payload))
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/warehouse/{token}/documents", response_model=ShipmentDocument, status_code=201)
def warehouse_document(token: str, payload: DocumentUploadRequest) -> ShipmentDocument:
    try:
        link = warehouse_link_by_token(store, token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return persist_result(upload_document(store, link.booking_id, payload, ActorRole.system, "warehouse-portal"))


@app.post("/carrier-links", response_model=CarrierAccessLink, status_code=201)
def carrier_link(payload: CarrierLinkCreate, _principal: Principal = Depends(require_admin)) -> CarrierAccessLink:
    try:
        return persist_result(create_carrier_link(store, payload.booking_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/carrier/{token}", response_model=CarrierPortalResponse)
def get_carrier_portal(token: str) -> CarrierPortalResponse:
    try:
        return carrier_portal(store, token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/carrier/{token}/eta", response_model=CarrierPortalResponse)
def carrier_eta(token: str, payload: CarrierEtaUpdate) -> CarrierPortalResponse:
    try:
        return persist_result(carrier_eta_update(store, token, payload))
    except ValueError as exc:
        message = str(exc)
        status_code = 400 if ("delivered" in message or "not yet on a container" in message) else 404
        raise HTTPException(status_code=status_code, detail=message)


@app.post("/carrier/{token}/event", response_model=CarrierPortalResponse)
def carrier_event(token: str, payload: CarrierEventUpdate) -> CarrierPortalResponse:
    try:
        return persist_result(carrier_event_update(store, token, payload))
    except ValueError as exc:
        message = str(exc)
        status_code = 400 if "may only" in message else 404
        raise HTTPException(status_code=status_code, detail=message)


@app.post("/carrier/{token}/documents", response_model=ShipmentDocument, status_code=201)
def carrier_document(token: str, payload: DocumentUploadRequest) -> ShipmentDocument:
    try:
        link = carrier_link_by_token(store, token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return persist_result(upload_document(store, link.booking_id, payload, ActorRole.system, "carrier-portal"))


@app.post("/trucker-links", response_model=TruckerAccessLink, status_code=201)
def trucker_link(payload: TruckerLinkCreate, _principal: Principal = Depends(require_admin)) -> TruckerAccessLink:
    try:
        return persist_result(create_trucker_link(store, payload.booking_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/trucker/{token}", response_model=TruckerPortalResponse)
def get_trucker_portal(token: str) -> TruckerPortalResponse:
    try:
        return trucker_portal(store, token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/trucker/{token}/status", response_model=TruckerPortalResponse)
def trucker_status(token: str, payload: TruckerStatusUpdate) -> TruckerPortalResponse:
    try:
        return persist_result(trucker_status_update(store, token, payload))
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        message = str(exc)
        status_code = 400 if "may only" in message else 404
        raise HTTPException(status_code=status_code, detail=message)


@app.post("/trucker/{token}/pod", response_model=ShipmentDocument, status_code=201)
def trucker_pod(token: str, payload: DocumentUploadRequest) -> ShipmentDocument:
    try:
        link = trucker_link_by_token(store, token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return persist_result(upload_document(store, link.booking_id, payload, ActorRole.system, "trucker-portal"))


@app.get("/bookings/{booking_id}/invoice", response_model=Invoice)
def booking_invoice(booking_id: str, _principal: Principal = Depends(require_importer)) -> Invoice:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return persist_result(ensure_invoice(store, store.bookings[booking_id]))


@app.post("/invoices/{invoice_id}/mark-paid", response_model=Invoice)
def invoice_mark_paid(invoice_id: str, _principal: Principal = Depends(require_admin)) -> Invoice:
    if invoice_id not in store.invoices:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return persist_result(mark_invoice_paid(store, invoice_id, "ops"))


@app.get("/bookings/{booking_id}/release-status", response_model=ReleaseStatusResponse)
def booking_release_status(booking_id: str, _principal: Principal = Depends(require_importer)) -> ReleaseStatusResponse:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return release_status_for_booking(store, booking_id)


class WarehouseMeasurementRequest(BaseModel):
    actual_cbm: float
    actual_weight_kg: float
    rate_per_cbm_usd: float = 95.0


@app.post("/bookings/{booking_id}/warehouse-measurement")
def post_warehouse_measurement(
    booking_id: str,
    payload: WarehouseMeasurementRequest,
    principal: Principal = Depends(require_admin),
) -> dict:
    try:
        result = record_warehouse_measurement(
            store,
            booking_id,
            payload.actual_cbm,
            payload.actual_weight_kg,
            principal.actor_id,
            rate_per_cbm_usd=payload.rate_per_cbm_usd,
        )
        persist_store()
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/bookings/{booking_id}/landed-cost")
def booking_landed_cost(booking_id: str, _principal: Principal = Depends(require_importer)) -> dict:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return landed_cost_summary(store, booking_id)


# --- FCL Spare-Space ---


@app.get("/bookings/{booking_id}/space-opportunities", response_model=List[SpaceOpportunity])
def booking_space_opportunities(
    booking_id: str, _principal: Principal = Depends(require_importer)
) -> List[SpaceOpportunity]:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return list_space_opportunities_for_booking(store, booking_id)


@app.post("/bookings/{booking_id}/space-opportunities/detect", response_model=Optional[SpaceOpportunity])
def trigger_space_opportunity_detection(
    booking_id: str, _principal: Principal = Depends(require_importer)
) -> Optional[SpaceOpportunity]:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return detect_fcl_spare_space(store, booking_id)


@app.post("/space-opportunities/{opportunity_id}/list", response_model=SpaceOpportunity)
def list_space_opportunity(
    opportunity_id: str, principal: Principal = Depends(require_importer)
) -> SpaceOpportunity:
    try:
        return persist_result(approve_space_opportunity_listing(store, opportunity_id, principal.actor_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/release-holds/{hold_id}/waive", response_model=ReleaseHold)
def waive_hold(
    hold_id: str,
    payload: DocumentDecisionRequest = DocumentDecisionRequest(reason="Admin override"),
    _principal: Principal = Depends(require_admin),
) -> ReleaseHold:
    if hold_id not in store.release_holds:
        raise HTTPException(status_code=404, detail="Release hold not found")
    return persist_result(waive_release_hold(store, hold_id, payload.reason or "Admin override", "ops"))


@app.get("/bookings/{booking_id}/customs-profile", response_model=CustomsProfile)
def booking_customs_profile(booking_id: str, _principal: Principal = Depends(require_importer)) -> CustomsProfile:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return persist_result(ensure_customs_profile(store, store.bookings[booking_id]))


@app.put("/bookings/{booking_id}/customs-profile", response_model=CustomsProfile)
def put_customs_profile(
    booking_id: str,
    payload: CustomsProfileUpdate,
    _principal: Principal = Depends(require_admin),
) -> CustomsProfile:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return persist_result(update_customs_profile(store, booking_id, payload))


@app.get("/bookings/{booking_id}/hs-suggestions")
def booking_hs_suggestions(
    booking_id: str, _principal: Principal = Depends(require_importer)
) -> dict:
    booking = store.bookings.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    suggestions = suggest_hs_code(booking.cargo_description, booking.cargo_category)
    return {
        "booking_id": booking_id,
        "current_hs_code": booking.hs_code,
        "suggestions": [
            {
                "hs_code": s.hs_code,
                "description": s.description,
                "confidence": s.confidence.value,
                "rationale": s.rationale,
            }
            for s in suggestions
        ],
    }


@app.post("/bookings/{booking_id}/customs-profile/accept-hs-suggestion")
def accept_hs_suggestion(
    booking_id: str, _principal: Principal = Depends(require_importer)
) -> CustomsProfile:
    booking = store.bookings.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    suggestion = best_suggestion(booking.cargo_description, booking.cargo_category)
    if not suggestion:
        raise HTTPException(status_code=404, detail="No HS code suggestion available for this cargo.")
    profile = ensure_customs_profile(store, booking)
    profile.hs_code = suggestion.hs_code
    booking.hs_code = suggestion.hs_code
    persist_store()
    return profile


@app.get("/bookings/{booking_id}/delivery-plan", response_model=DeliveryPlan)
def booking_delivery_plan(booking_id: str, _principal: Principal = Depends(require_importer)) -> DeliveryPlan:
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return persist_result(ensure_delivery_plan(store, store.bookings[booking_id]))


@app.put("/bookings/{booking_id}/delivery-plan", response_model=DeliveryPlan)
def put_delivery_plan(
    booking_id: str,
    payload: DeliveryPlanUpdate,
    principal: Principal = Depends(require_importer),
) -> DeliveryPlan:
    try:
        return persist_result(update_delivery_plan(store, booking_id, payload, principal.actor_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/delivery-plans/{delivery_plan_id}/book", response_model=DeliveryPlan)
def delivery_plan_book(delivery_plan_id: str, principal: Principal = Depends(require_importer)) -> DeliveryPlan:
    try:
        return persist_result(book_delivery_plan(store, delivery_plan_id, principal.actor_id))
    except ValueError as exc:
        status_code = 409 if "cannot be booked" in str(exc) else 404
        raise HTTPException(status_code=status_code, detail=str(exc))


@app.post("/delivery-plans/{delivery_plan_id}/mark-delivered", response_model=DeliveryPlan)
def delivery_plan_delivered(delivery_plan_id: str, principal: Principal = Depends(require_importer)) -> DeliveryPlan:
    try:
        return persist_result(mark_delivery_delivered(store, delivery_plan_id, principal.actor_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# --- Automation Engine endpoints ---


@app.get("/automation/shipment-state/{booking_id}")
def get_shipment_state(booking_id: str, _principal: Principal = Depends(require_importer)) -> dict:
    booking = store.bookings.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    state = derive_lifecycle_state(store, booking)
    return {
        "booking_id": booking_id,
        "lifecycle_state": state.value,
        "next_action": next_action_for_state(state),
    }


@app.get("/automation/missing-data/{booking_id}", response_model=List[MissingDataItem])
def get_missing_data(booking_id: str, _principal: Principal = Depends(require_importer)) -> List[MissingDataItem]:
    booking = store.bookings.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return detect_missing_data(store, booking)


@app.post("/automation/run/{booking_id}", response_model=AutomationResult)
def run_booking_automation(booking_id: str, _principal: Principal = Depends(require_admin)) -> AutomationResult:
    booking = store.bookings.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    result = run_automation_for_booking(store, booking)
    persist_store()
    return result


@app.post("/automation/run-all")
def run_all_automation(_principal: Principal = Depends(require_admin)) -> dict:
    results = run_full_automation_cycle(store)
    persist_store()
    return {
        "shipments_processed": len(results),
        "total_chase_messages": sum(r.chase_messages_queued for r in results.values()),
        "total_missing_items": sum(len(r.missing_data) for r in results.values()),
        "states": {bid: r.lifecycle_state.value for bid, r in results.items()},
    }


@app.post("/automation/extract/{message_id}", response_model=List[ExtractedFact])
def extract_message_facts(message_id: str, _principal: Principal = Depends(require_admin)) -> List[ExtractedFact]:
    message = store.source_messages.get(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Source message not found")
    facts = run_extraction_for_message(store, message)
    persist_store()
    return facts


# --- Supplier invoice extractor ---


class InvoiceParseTextRequest(BaseModel):
    text: str
    booking_id: Optional[str] = None
    apply: bool = False


@app.post("/invoices/parse-text")
def parse_invoice_text(
    payload: InvoiceParseTextRequest, principal: Principal = Depends(require_importer)
) -> dict:
    parsed = extract_invoice_from_text(payload.text)
    result: dict = {"parsed": parsed.model_dump(mode="json")}
    if payload.apply:
        applied = apply_parsed_invoice(
            store, parsed, principal.actor_id, hint_booking_id=payload.booking_id
        )
        result["applied"] = applied
        persist_store()
    return result


@app.post("/invoices/parse-pdf")
async def parse_invoice_pdf(
    file: UploadFile = File(...),
    booking_id: Optional[str] = Form(default=None),
    apply: bool = Form(default=False),
    principal: Principal = Depends(require_importer),
) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF too large. Limit is 10 MB.")
    parsed = extract_invoice_from_pdf(contents)
    result: dict = {
        "filename": file.filename,
        "parsed": parsed.model_dump(mode="json"),
    }
    if not parsed.total_amount:
        result["warning"] = (
            "Could not extract a total amount. The PDF may be image-only "
            "(scanned) or use a layout the parser does not recognise."
        )
    if apply and parsed.total_amount:
        applied = apply_parsed_invoice(
            store, parsed, principal.actor_id, hint_booking_id=booking_id
        )
        result["applied"] = applied
        persist_store()
    return result


@app.post("/source-messages/{message_id}/extract-invoice")
def extract_invoice_from_message(
    message_id: str,
    apply: bool = False,
    booking_id: Optional[str] = None,
    principal: Principal = Depends(require_importer),
) -> dict:
    message = store.source_messages.get(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Source message not found")
    text = f"{message.subject or ''}\n{message.body or ''}"
    parsed = extract_invoice_from_text(text)
    result: dict = {"message_id": message_id, "parsed": parsed.model_dump(mode="json")}
    if apply:
        applied = apply_parsed_invoice(
            store,
            parsed,
            principal.actor_id,
            hint_booking_id=booking_id,
            source_message_id=message_id,
        )
        result["applied"] = applied
        persist_store()
    return result


@app.post("/automation/apply-facts/{booking_id}")
def apply_facts_to_booking(booking_id: str, facts: List[ExtractedFact], _principal: Principal = Depends(require_admin)) -> dict:
    booking = store.bookings.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    applied, needs_review = apply_extracted_facts(store, booking, facts)
    persist_store()
    return {
        "applied_count": len(applied),
        "needs_review_count": len(needs_review),
        "applied_fields": [f.field for f in applied],
        "review_fields": [f.field for f in needs_review],
    }


@app.post("/automation/advance-status/{booking_id}")
def advance_booking_status_endpoint(
    booking_id: str, _principal: Principal = Depends(require_admin)
) -> dict:
    booking = store.bookings.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    old_status = booking.status.value
    advanced = try_advance_booking_status(store, booking)
    return {
        "advanced": advanced,
        "old_status": old_status,
        "new_status": booking.status.value,
    }


@app.get("/automation/stale-checks")
def stale_shipment_checks(_principal: Principal = Depends(require_admin)) -> List[dict]:
    return check_stale_shipments(store)


# --- Scheduled cron-driven automation ---
# Use a separate token from admin/importer; Railway can hit this on a schedule
# without exposing the admin token. Set SHIP_HOPPA_CRON_TOKEN in production.

@app.post("/automation/cron/run")
def cron_run_automation(_principal: Principal = Depends(require_cron)) -> dict:
    results = run_full_automation_cycle(store)

    # After running automation, attempt to dispatch any queued outbound
    # messages. This makes the cron loop self-contained: chase emails get
    # generated, then sent (if live providers are enabled), every tick.
    queued = [m for m in store.outbound_messages.values() if m.status == OutboundStatus.queued]
    queued.sort(key=lambda m: m.created_at)
    dispatch_sent = 0
    dispatch_failed = 0
    dispatch_deferred = 0
    for msg in queued[:100]:  # cap per tick to keep cycles bounded
        result = dispatch_outbound_message(store, msg.id)
        if result.status == OutboundStatus.sent:
            dispatch_sent += 1
        elif result.status == OutboundStatus.failed:
            dispatch_failed += 1
        else:
            dispatch_deferred += 1

    persist_store()
    chases = sum(r.chase_messages_queued for r in results.values())
    missing = sum(len(r.missing_data) for r in results.values())
    open_admin = sum(1 for t in store.admin_tasks.values() if t.status == AdminTaskStatus.open)
    pending_approvals = sum(1 for a in store.approval_requests.values() if a.status == ApprovalStatus.pending)
    return {
        "shipments_processed": len(results),
        "total_chase_messages_queued": chases,
        "total_missing_items": missing,
        "open_admin_tasks": open_admin,
        "pending_approvals": pending_approvals,
        "outbound_dispatch": {
            "sent": dispatch_sent,
            "failed": dispatch_failed,
            "deferred": dispatch_deferred,
        },
        "states": {bid: r.lifecycle_state.value for bid, r in results.items()},
    }


@app.post("/automation/cron/health")
def cron_health(_principal: Principal = Depends(require_cron)) -> dict:
    """Lightweight ping for cron platform monitoring."""
    return {
        "ok": True,
        "active_bookings": sum(
            1 for b in store.bookings.values() if b.status != BookingStatus.delivered
        ),
        "pending_approvals": sum(
            1 for a in store.approval_requests.values() if a.status == ApprovalStatus.pending
        ),
    }


# --- Admin Task Queue ---


@app.get("/admin-tasks", response_model=List[AdminTask])
def list_admin_tasks(
    status: Optional[str] = None,
    booking_id: Optional[str] = None,
    _principal: Principal = Depends(require_admin),
) -> List[AdminTask]:
    tasks = list(store.admin_tasks.values())
    if status:
        tasks = [t for t in tasks if t.status.value == status]
    if booking_id:
        tasks = [t for t in tasks if t.booking_id == booking_id]
    return sorted(tasks, key=lambda t: t.created_at, reverse=True)


@app.post("/admin-tasks/{task_id}/resolve")
def resolve_admin_task(
    task_id: str, _principal: Principal = Depends(require_admin)
) -> AdminTask:
    task = store.admin_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Admin task not found")
    task.status = AdminTaskStatus.done
    from datetime import datetime
    task.updated_at = datetime.utcnow()
    return task


@app.post("/admin-tasks/{task_id}/dismiss")
def dismiss_admin_task(
    task_id: str, _principal: Principal = Depends(require_admin)
) -> AdminTask:
    task = store.admin_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Admin task not found")
    task.status = AdminTaskStatus.waived
    from datetime import datetime
    task.updated_at = datetime.utcnow()
    return task


@app.get("/admin-tasks/summary")
def admin_task_summary(_principal: Principal = Depends(require_admin)) -> dict:
    tasks = list(store.admin_tasks.values())
    open_tasks = [t for t in tasks if t.status == AdminTaskStatus.open]
    by_type: dict = {}
    for task in open_tasks:
        by_type[task.task_type] = by_type.get(task.task_type, 0) + 1
    return {
        "total_open": len(open_tasks),
        "total_done": sum(1 for t in tasks if t.status == AdminTaskStatus.done),
        "total_waived": sum(1 for t in tasks if t.status == AdminTaskStatus.waived),
        "by_type": by_type,
    }


# --- Frontend SPA static serving ---

_FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend_dist"

if _FRONTEND_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIR / "assets"), name="frontend-assets")

    @app.get("/{path:path}")
    def serve_frontend(path: str) -> FileResponse:
        file = _FRONTEND_DIR / path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(_FRONTEND_DIR / "index.html")
