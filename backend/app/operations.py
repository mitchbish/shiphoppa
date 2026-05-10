import base64
import secrets
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    AccountIntegration,
    AccountIntegrationProvider,
    AccountIntegrationStatus,
    AccountIntegrationUpdate,
    AccountProfile,
    AccountProfileUpdate,
    ActorRole,
    AdminTask,
    AdminTaskStatus,
    ApprovalRequest,
    ApprovalRequestType,
    ApprovalStatus,
    AutomationDecision,
    AutomationRun,
    AutomationType,
    AuditEvent,
    Booking,
    BookingChecklistResponse,
    BookingStatus,
    CargoCategory,
    ChecklistStatus,
    ContactMethod,
    CustomsBrokerPreference,
    CustomsProfile,
    CustomsProfileUpdate,
    CustomsStatus,
    DocumentDecisionRequest,
    DocumentRequirement,
    DocumentStatus,
    DocumentType,
    DeliveryMode,
    DeliveryPlan,
    DeliveryPlanStatus,
    DeliveryPlanUpdate,
    DocumentUploadRequest,
    ExtractionStatus,
    FileBackupStatus,
    GrowthAttributionEvent,
    GrowthAttributionEventType,
    ImportProject,
    ImportProjectCreate,
    ImportProjectEvent,
    ImportProjectFile,
    ImportProjectStatus,
    ImportProjectStepData,
    ImportProjectStepStatus,
    ImportProjectUpdate,
    ImportProjectVersion,
    ImportWorkflowType,
    Invoice,
    InvoiceLineItem,
    Notification,
    OutboundChannel,
    OutboundMessage,
    OutboundMessageCreate,
    OutboundProvider,
    OutboundStatus,
    PaymentRecord,
    PaymentStatus,
    ProductionMilestone,
    ProductionMilestoneCompleteRequest,
    ProductionMilestoneStatus,
    ProductionMilestoneType,
    ProjectActorType,
    PurchaseOrder,
    PurchaseOrderCreate,
    PurchaseOrderStatus,
    QualityInspection,
    QualityInspectionResult,
    ReleaseHold,
    ReleaseHoldStatus,
    ReleaseHoldType,
    ReleaseStatus,
    ReleaseStatusResponse,
    SailingSearchResult,
    SEOOpportunity,
    SEOOpportunityCreate,
    SEOOpportunityStatus,
    SupplierDiscoverySourceSet,
    ShipmentDocument,
    ShipmentEvent,
    ShipmentEventCreate,
    ShipmentEventStage,
    SourceConfidence,
    SourceMessage,
    SourceMessageCreate,
    SourceType,
    SpaceOpportunity,
    SpaceOpportunityStatus,
    SupplierDiscoveryRun,
    SupplierDiscoveryRunStatus,
    SupplierLead,
    SupplierLeadSource,
    SupplierOutreachStatus,
    SupplierVerificationStatus,
    SupplierVerificationUpdate,
    SupplierAccessLink,
    SupplierBookingSummary,
    SupplierPayProvider,
    SupplierPayQuote,
    SupplierPayQuoteStatus,
    SupplierPayRequest,
    SupplierPayRequestCreate,
    SupplierPayRequestStatus,
    SupplierPayStage,
    SupplierPayMarkPaidRequest,
    SupplierPortalResponse,
    SupplierReadyRequest,
    BrokerAccessLink,
    BrokerBookingSummary,
    BrokerClearanceUpdate,
    BrokerCustomsSummary,
    BrokerPortalResponse,
    WarehouseAccessLink,
    WarehouseBookingSummary,
    WarehousePortalResponse,
    WarehouseReceiptUpdate,
    CarrierAccessLink,
    CarrierBookingSummary,
    CarrierEtaUpdate,
    CarrierEventUpdate,
    CarrierPortalResponse,
)
from .store import Store


STORAGE_ROOT = Path(__file__).resolve().parents[1] / "storage" / "documents"

DOCUMENT_LABELS = {
    DocumentType.commercial_invoice: "Commercial invoice",
    DocumentType.packing_list: "Packing list",
    DocumentType.supplier_photos: "Supplier cargo photos",
    DocumentType.product_specs: "Product specifications",
    DocumentType.fumigation_ispm: "Fumigation / ISPM 15 evidence",
    DocumentType.shipping_instructions: "Shipping instructions",
    DocumentType.house_bill: "House bill of lading",
    DocumentType.arrival_notice: "Arrival notice",
    DocumentType.delivery_order: "Delivery order",
}


def now_utc() -> datetime:
    return datetime.utcnow().replace(microsecond=0)


def normalize_datetime(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(microsecond=0)
    return value.astimezone(timezone.utc).replace(tzinfo=None, microsecond=0)


def shipment_event_sort_key(event: ShipmentEvent) -> datetime:
    return normalize_datetime(event.occurred_at or event.estimated_at or event.created_at) or datetime.min


def round_money(value: float) -> float:
    return round(value + 0.0000001, 2)


def create_audit_event(
    store: Store,
    actor_role: ActorRole,
    actor_id: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    message: str,
    metadata: Optional[dict] = None,
) -> AuditEvent:
    event = AuditEvent(
        id=store.next_id("AUD"),
        actor_role=actor_role,
        actor_id=actor_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        message=message,
        metadata=metadata or {},
        created_at=now_utc(),
    )
    store.audit_events[event.id] = event
    return event


def _default_profile_from_importer(store: Store, actor_id: str) -> AccountProfile:
    importer = next(iter(store.importers.values()), None)
    timestamp = now_utc()
    return AccountProfile(
        id=store.next_id("ACP"),
        owner_actor_id=actor_id,
        importer_company_name=importer.company_name if importer else "Bayside Build Co.",
        importer_contact_name=importer.contact_name if importer else "Alex Morgan",
        importer_email=importer.email if importer else "alex@baysidebuild.example",
        importer_phone=importer.phone if importer else "+61 400 555 010",
        delivery_city="Brisbane",
        delivery_postcode="4101",
        delivery_country="Australia",
        default_supplier_city=importer.default_supplier_city if importer else "Dongguan",
        default_supplier_province="Guangdong",
        default_supplier_country="China",
        default_delivery_mode=DeliveryMode.ship_hoppa_pickup,
        importer_abn=importer.abn if importer else None,
        created_at=timestamp,
        updated_at=timestamp,
    )


def ensure_account_profile(store: Store, actor_id: str) -> AccountProfile:
    for profile in store.account_profiles.values():
        if profile.owner_actor_id == actor_id:
            return profile

    profile = _default_profile_from_importer(store, actor_id)
    store.account_profiles[profile.id] = profile
    return profile


def update_account_profile(store: Store, actor_id: str, payload: AccountProfileUpdate) -> AccountProfile:
    profile = ensure_account_profile(store, actor_id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(profile, key, value)
    profile.updated_at = now_utc()
    store.account_profiles[profile.id] = profile
    create_audit_event(
        store,
        ActorRole.importer,
        actor_id,
        "account_profile_updated",
        "account_profile",
        profile.id,
        "Account profile defaults updated.",
        metadata={"updated_fields": sorted(updates.keys())},
    )
    return profile


def _account_integration_templates() -> list[dict]:
    return [
        {
            "provider": AccountIntegrationProvider.alibaba,
            "display_name": "Alibaba / 1688",
            "category": "Marketplace order import",
            "connection_mode": "prompt_when_order_source_matches",
            "prompt_when": [
                "The buyer says the order came from Alibaba or 1688.",
                "An order reference, pro forma, or Trade Assurance thread can save typing.",
            ],
            "notes": "Optional. Prompt only when it removes manual order entry.",
        },
        {
            "provider": AccountIntegrationProvider.email_inbox,
            "display_name": "Email inbox",
            "category": "Email ingestion",
            "connection_mode": "connect_google_microsoft_or_forward",
            "prompt_when": [
                "Supplier invoices, production updates, or attachments are still arriving by email.",
                "The user wants Ship Hoppa to extract order and shipping data without changing supplier behaviour.",
            ],
            "notes": "Supports the future Google/Microsoft connected inbox and forwarding address workflow.",
        },
        {
            "provider": AccountIntegrationProvider.accounting,
            "display_name": "Accounting",
            "category": "Reconciliation",
            "connection_mode": "prompt_before_export",
            "prompt_when": [
                "Supplier pay, freight invoices, duty, GST, and delivery costs need to reconcile.",
                "The importer wants accounting export instead of manual data entry.",
            ],
            "notes": "Connector-ready for Xero, QuickBooks, and the Launchpad accounting layer.",
        },
        {
            "provider": AccountIntegrationProvider.supplier_pay,
            "display_name": "Supplier Pay",
            "category": "Payments and FX",
            "connection_mode": "quote_before_payment",
            "prompt_when": [
                "The importer needs to pay a supplier deposit or balance.",
                "Wise, OFX, or manual bank transfer can be compared before payment.",
            ],
            "notes": "Mark as paid outside the app stays supported.",
        },
        {
            "provider": AccountIntegrationProvider.object_storage,
            "display_name": "Railway storage + R2 backup",
            "category": "Secure document storage",
            "connection_mode": "system_managed",
            "prompt_when": [
                "Documents, photos, invoices, inspection reports, and source emails need permanent storage.",
                "A backup copy must be retained in secure object storage.",
            ],
            "notes": "Designed for Railway primary storage with Cloudflare R2 backup.",
        },
    ]


def ensure_account_integrations(store: Store, actor_id: str) -> List[AccountIntegration]:
    existing = {integration.provider: integration for integration in store.account_integrations.values() if integration.owner_actor_id == actor_id}
    timestamp = now_utc()
    for template in _account_integration_templates():
        provider = template["provider"]
        if provider in existing:
            continue
        status = (
            AccountIntegrationStatus.connected
            if provider == AccountIntegrationProvider.object_storage
            else AccountIntegrationStatus.not_connected
        )
        integration = AccountIntegration(
            id=store.next_id("ACI"),
            owner_actor_id=actor_id,
            status=status,
            last_verified_at=timestamp if status == AccountIntegrationStatus.connected else None,
            created_at=timestamp,
            updated_at=timestamp,
            **template,
        )
        store.account_integrations[integration.id] = integration
        existing[provider] = integration

    return sorted(existing.values(), key=lambda item: item.display_name)


def update_account_integration(
    store: Store,
    actor_id: str,
    provider: AccountIntegrationProvider,
    payload: AccountIntegrationUpdate,
) -> AccountIntegration:
    integrations = ensure_account_integrations(store, actor_id)
    integration = next((item for item in integrations if item.provider == provider), None)
    if not integration:
        raise ValueError("Account integration not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(integration, key, value)
    if integration.status == AccountIntegrationStatus.connected and integration.last_verified_at is None:
        integration.last_verified_at = now_utc()
    integration.updated_at = now_utc()
    store.account_integrations[integration.id] = integration
    create_audit_event(
        store,
        ActorRole.importer,
        actor_id,
        "account_integration_updated",
        "account_integration",
        integration.id,
        f"{integration.display_name} integration updated.",
        metadata={"provider": provider.value, "status": integration.status.value},
    )
    return integration


def default_outbound_provider(channel: OutboundChannel) -> OutboundProvider:
    if channel == OutboundChannel.email:
        return OutboundProvider.resend
    if channel == OutboundChannel.sms:
        return OutboundProvider.twilio
    return OutboundProvider.manual


def dispatch_outbound_message(store: Store, message_id: str) -> OutboundMessage:
    """
    Try to send a queued outbound message via its real provider. Updates
    status to sent/failed and writes the provider response back. Safe to
    call when SHIP_HOPPA_LIVE_PROVIDERS is off; in that case the message
    stays queued and the audit event records "deferred".
    """
    from . import providers

    message = store.outbound_messages.get(message_id)
    if not message:
        raise ValueError(f"OutboundMessage {message_id} not found")
    if message.status != OutboundStatus.queued:
        return message

    if message.channel == OutboundChannel.email:
        result = providers.send_email_via_resend(
            to_addresses=[message.recipient_id],
            subject=message.subject or "(no subject)",
            body=message.body_snapshot,
        )
    elif message.channel == OutboundChannel.sms:
        result = providers.send_sms_via_twilio(
            to_phone=message.recipient_id,
            body=message.body_snapshot,
        )
    else:
        result = {
            "sent": False,
            "provider": "manual",
            "detail": "Channel does not have an automated provider.",
            "provider_message_id": None,
            "error_code": None,
        }

    timestamp = now_utc()
    if result["sent"]:
        message.status = OutboundStatus.sent
        message.sent_at = timestamp
        message.provider_message_id = result.get("provider_message_id")
        message.failure_code = None
        message.sentinel_error_code = None
    elif result.get("deferred"):
        # Provider not configured or live flag disabled — leave queued for later.
        pass
    elif result.get("error_code"):
        message.status = OutboundStatus.failed
        message.failure_code = result["detail"][:200]
        message.sentinel_error_code = result["error_code"]

    create_audit_event(
        store,
        ActorRole.system,
        "outbound_dispatcher",
        "outbound_message_dispatched",
        "outbound_message",
        message.id,
        f"Dispatch attempt: {result['detail']}",
        {
            "provider": result["provider"],
            "sent": result["sent"],
            "error_code": result.get("error_code"),
        },
    )
    return message


def queue_outbound_message(
    store: Store,
    request: OutboundMessageCreate,
    actor_role: ActorRole,
    actor_id: str,
) -> OutboundMessage:
    if request.related_supplier_lead_id:
        lead = store.supplier_leads.get(request.related_supplier_lead_id)
        if not lead:
            raise ValueError("Supplier lead not found")
        if lead.do_not_contact or lead.opt_out_at:
            raise ValueError("Supplier lead has opted out or is marked do not contact")

    timestamp = now_utc()
    message = OutboundMessage(
        id=store.next_id("OUT"),
        recipient_type=request.recipient_type,
        recipient_id=request.recipient_id,
        channel=request.channel,
        provider=request.provider or default_outbound_provider(request.channel),
        template_key=request.template_key,
        template_version=request.template_version,
        campaign_id=request.campaign_id,
        subject=request.subject,
        body_snapshot=request.body_snapshot,
        compliance_basis=request.compliance_basis,
        suppression_checked_at=timestamp,
        related_supplier_lead_id=request.related_supplier_lead_id,
        related_shipment_id=request.related_shipment_id,
        created_at=timestamp,
    )
    store.outbound_messages[message.id] = message

    if request.related_supplier_lead_id:
        lead = store.supplier_leads[request.related_supplier_lead_id]
        if lead.outreach_status in {SupplierOutreachStatus.discovered, SupplierOutreachStatus.needs_human_review}:
            lead.outreach_status = SupplierOutreachStatus.approved_for_contact
            lead.updated_at = timestamp
            store.supplier_leads[lead.id] = lead

    create_audit_event(
        store,
        actor_role,
        actor_id,
        "outbound_message_queued",
        "outbound_message",
        message.id,
        f"{message.channel.value.title()} message queued for {message.recipient_type.value}.",
        {
            "provider": message.provider.value,
            "template_key": message.template_key,
            "related_supplier_lead_id": message.related_supplier_lead_id,
            "related_shipment_id": message.related_shipment_id,
        },
    )
    return message


def create_admin_task(store: Store, booking: Booking, task_type: str, title: str) -> AdminTask:
    for task in store.admin_tasks.values():
        if task.booking_id == booking.id and task.task_type == task_type and task.status == AdminTaskStatus.open:
            return task
    timestamp = now_utc()
    task = AdminTask(
        id=store.next_id("TASK"),
        booking_id=booking.id,
        task_type=task_type,
        title=title,
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.admin_tasks[task.id] = task
    return task


PROJECT_STEP_SPECS = [
    ("intake", 1, "Shipment intake"),
    ("order", 2, "Order details"),
    ("production", 3, "Production tracking"),
    ("documents", 4, "Documents"),
    ("shipping", 5, "Shipping plan"),
    ("money", 6, "Money and approvals"),
    ("customs", 7, "Customs"),
    ("delivery", 8, "Final delivery"),
    ("space", 9, "Space options"),
]


def upsert_project_step(
    store: Store,
    project: ImportProject,
    step_key: str,
    status: ImportProjectStepStatus,
    data: Optional[dict] = None,
    source_reference: Optional[str] = None,
) -> ImportProjectStepData:
    matching_spec = next((spec for spec in PROJECT_STEP_SPECS if spec[0] == step_key), None)
    if not matching_spec:
        raise ValueError("Unknown project step")
    _, step_number, label = matching_spec
    source_refs = [source_reference] if source_reference else []
    existing = next(
        (
            step
            for step in store.import_project_steps.values()
            if step.import_project_id == project.id and step.step_key == step_key
        ),
        None,
    )
    if existing:
        existing.status = status
        existing.data = {**existing.data, "label": label, **(data or {})}
        existing.source_references = sorted(set(existing.source_references + source_refs))
        existing.updated_at = now_utc()
        store.import_project_steps[existing.id] = existing
        return existing
    step = ImportProjectStepData(
        id=store.next_id("IPS"),
        import_project_id=project.id,
        step_key=step_key,
        step_number=step_number,
        data={"label": label, **(data or {})},
        status=status,
        source_references=source_refs,
        updated_at=now_utc(),
    )
    store.import_project_steps[step.id] = step
    return step


def import_project_for_booking(store: Store, booking_id: str) -> Optional[ImportProject]:
    for project in store.import_projects.values():
        if booking_id in project.linked_shipment_ids and project.status == ImportProjectStatus.active:
            return project
    return None


def create_import_project_event(
    store: Store,
    project_id: str,
    event_type: str,
    actor_type: ProjectActorType,
    actor_id: str,
    event_reference: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> ImportProjectEvent:
    event = ImportProjectEvent(
        id=store.next_id("IPE"),
        import_project_id=project_id,
        event_type=event_type,
        event_reference=event_reference,
        actor_type=actor_type,
        actor_id=actor_id,
        metadata=metadata or {},
        occurred_at=now_utc(),
    )
    store.import_project_events[event.id] = event
    return event


def append_import_project_version(
    store: Store,
    project_id: str,
    changed_by: str,
    action: str,
    step_key: Optional[str] = None,
    source_reference: Optional[str] = None,
    before_summary: Optional[str] = None,
    after_summary: Optional[str] = None,
) -> ImportProjectVersion:
    existing_versions = [
        version for version in store.import_project_versions.values() if version.import_project_id == project_id
    ]
    version = ImportProjectVersion(
        id=store.next_id("IPV"),
        import_project_id=project_id,
        version_number=len(existing_versions) + 1,
        changed_by=changed_by,
        action=action,
        step_key=step_key,
        source_reference=source_reference,
        before_summary=before_summary,
        after_summary=after_summary,
        created_at=now_utc(),
    )
    store.import_project_versions[version.id] = version
    return version


def project_next_action(booking: Booking) -> str:
    if booking.admin_review_required:
        return "Ship Hoppa operations needs to review this import before it can move forward."
    if booking.status == BookingStatus.submitted:
        return "Find the best shipping option."
    if booking.status == BookingStatus.matched:
        return "Confirm the selected container and send supplier instructions."
    if booking.checklist_status != ChecklistStatus.complete:
        return "Upload and approve the required documents."
    if booking.payment_status != PaymentStatus.paid:
        return "Review and pay the shipment invoice."
    if booking.release_status == ReleaseStatus.blocked:
        return "Clear shipment holds before release."
    return "Track the shipment to delivery."


def sync_project_steps_for_booking(store: Store, project: ImportProject, booking: Booking) -> None:
    existing = {
        step.step_key: step
        for step in store.import_project_steps.values()
        if step.import_project_id == project.id
    }
    source_refs = [booking.id]
    for step_key, step_number, label in PROJECT_STEP_SPECS:
        if step_key == "intake":
            status = ImportProjectStepStatus.complete
        elif step_key == "shipping" and booking.container_id:
            status = ImportProjectStepStatus.in_progress
        elif step_key == "documents":
            status = ImportProjectStepStatus.complete if booking.checklist_status == ChecklistStatus.complete else ImportProjectStepStatus.in_progress
        elif step_key == "money":
            status = ImportProjectStepStatus.complete if booking.payment_status == PaymentStatus.paid else ImportProjectStepStatus.in_progress
        elif step_key == "customs":
            profile = next((item for item in store.customs_profiles.values() if item.booking_id == booking.id), None)
            status = (
                ImportProjectStepStatus.complete
                if profile and profile.customs_status == CustomsStatus.cleared
                else ImportProjectStepStatus.in_progress
            )
        elif step_key == "delivery" and booking.status == BookingStatus.delivered:
            status = ImportProjectStepStatus.complete
        elif step_key == "space" and booking.container_id:
            status = ImportProjectStepStatus.in_progress
        else:
            status = ImportProjectStepStatus.not_started

        data = {
            "label": label,
            "booking_id": booking.id,
            "next_action": project_next_action(booking) if step_key == project.current_step else None,
        }
        if step_key in existing:
            step = existing[step_key]
            step.data = {**step.data, **data}
            step.status = status
            step.source_references = sorted(set(step.source_references + source_refs))
            step.updated_at = now_utc()
        else:
            step = ImportProjectStepData(
                id=store.next_id("IPS"),
                import_project_id=project.id,
                step_key=step_key,
                step_number=step_number,
                data=data,
                status=status,
                source_references=source_refs,
                updated_at=now_utc(),
            )
        store.import_project_steps[step.id] = step


def create_import_project(
    store: Store,
    request: ImportProjectCreate,
    actor_role: ActorRole,
    actor_id: str,
    organization_id: Optional[str] = None,
    owner_user_id: Optional[str] = None,
) -> ImportProject:
    timestamp = now_utc()
    project = ImportProject(
        id=store.next_id("IPR"),
        organization_id=organization_id or actor_id,
        owner_user_id=owner_user_id or actor_id,
        workflow_type=request.workflow_type,
        title=request.title,
        description=request.description,
        summary=request.summary or "",
        next_action=request.next_action,
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.import_projects[project.id] = project
    append_import_project_version(
        store,
        project.id,
        actor_id,
        "project_created",
        after_summary=project.summary,
    )
    create_import_project_event(
        store,
        project.id,
        "project_created",
        ProjectActorType.user if actor_role == ActorRole.importer else ProjectActorType.admin,
        actor_id,
        metadata={"title": project.title},
    )
    create_audit_event(
        store,
        actor_role,
        actor_id,
        "import_project_created",
        "import_project",
        project.id,
        f"Created import project '{project.title}'.",
    )
    return project


def update_import_project(
    store: Store,
    project_id: str,
    request: ImportProjectUpdate,
    actor_role: ActorRole,
    actor_id: str,
) -> ImportProject:
    project = store.import_projects.get(project_id)
    if not project:
        raise ValueError("Import project not found")
    data = request.model_dump(exclude_unset=True)
    if not data:
        return project
    before_summary = project.summary
    for key, value in data.items():
        setattr(project, key, value)
    project.updated_at = now_utc()
    if request.status == ImportProjectStatus.archived and project.archived_at is None:
        project.archived_at = now_utc()
    store.import_projects[project.id] = project
    append_import_project_version(
        store,
        project.id,
        actor_id,
        "project_updated",
        before_summary=before_summary,
        after_summary=project.summary,
    )
    create_audit_event(
        store,
        actor_role,
        actor_id,
        "import_project_updated",
        "import_project",
        project.id,
        f"Updated import project '{project.title}'.",
    )
    return project


def clone_import_project(
    store: Store,
    source_project_id: str,
    actor_role: ActorRole,
    actor_id: str,
    new_title: Optional[str] = None,
) -> ImportProject:
    source = store.import_projects.get(source_project_id)
    if not source:
        raise ValueError("Source import project not found")
    timestamp = now_utc()
    title = new_title or f"Copy of {source.title}"
    project = ImportProject(
        id=store.next_id("IPR"),
        organization_id=source.organization_id,
        owner_user_id=source.owner_user_id,
        workflow_type=source.workflow_type,
        workflow_version=source.workflow_version,
        title=title,
        description=source.description,
        summary=source.summary,
        current_step="intake",
        next_action=source.next_action,
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.import_projects[project.id] = project
    append_import_project_version(
        store,
        project.id,
        actor_id,
        "project_cloned",
        source_reference=source.id,
        after_summary=project.summary,
    )
    create_import_project_event(
        store,
        project.id,
        "project_cloned",
        ProjectActorType.user if actor_role == ActorRole.importer else ProjectActorType.admin,
        actor_id,
        metadata={"source_project_id": source.id, "new_title": title},
    )
    create_audit_event(
        store,
        actor_role,
        actor_id,
        "import_project_cloned",
        "import_project",
        project.id,
        f"Cloned import project from {source.id}.",
    )
    return project


def soft_delete_import_project(
    store: Store,
    project_id: str,
    actor_role: ActorRole,
    actor_id: str,
) -> ImportProject:
    project = store.import_projects.get(project_id)
    if not project:
        raise ValueError("Import project not found")
    if project.status in {ImportProjectStatus.deleted_pending_retention, ImportProjectStatus.deleted}:
        return project
    project.status = ImportProjectStatus.deleted_pending_retention
    project.deleted_at = now_utc()
    project.updated_at = now_utc()
    store.import_projects[project.id] = project
    append_import_project_version(
        store,
        project.id,
        actor_id,
        "project_soft_deleted",
        after_summary=project.summary,
    )
    create_audit_event(
        store,
        actor_role,
        actor_id,
        "import_project_soft_deleted",
        "import_project",
        project.id,
        f"Soft-deleted import project {project.id}.",
    )
    return project


def ensure_import_project_for_booking(store: Store, booking: Booking, actor_id: str = "system") -> ImportProject:
    existing = import_project_for_booking(store, booking.id)
    importer = store.importers.get(booking.importer_id)
    title = f"{booking.supplier_city} to {booking.delivery_city} import"
    if booking.supplier_name:
        title = f"{booking.supplier_name} -> {booking.delivery_city}"
    workflow_type = ImportWorkflowType.mcl_shared_space if booking.container_id else ImportWorkflowType.standard_import
    summary = (
        f"{booking.cargo_category.value.replace('_', ' ')} shipment from "
        f"{booking.supplier_city}, {booking.supplier_country} to {booking.delivery_city}, {booking.delivery_country}."
    )
    if existing:
        before_summary = existing.summary
        existing.title = title
        existing.workflow_type = workflow_type
        existing.summary = summary
        existing.current_step = "shipping" if booking.container_id else "intake"
        existing.next_action = project_next_action(booking)
        existing.updated_at = now_utc()
        store.import_projects[existing.id] = existing
        if before_summary != existing.summary:
            append_import_project_version(
                store,
                existing.id,
                actor_id,
                "project_synced_from_booking",
                source_reference=booking.id,
                before_summary=before_summary,
                after_summary=existing.summary,
            )
        sync_project_steps_for_booking(store, existing, booking)
        return existing

    timestamp = now_utc()
    project = ImportProject(
        id=store.next_id("IPR"),
        organization_id=booking.importer_id,
        owner_user_id=importer.email if importer else booking.importer_id,
        workflow_type=workflow_type,
        title=title,
        description=booking.cargo_description,
        current_step="shipping" if booking.container_id else "intake",
        next_action=project_next_action(booking),
        summary=summary,
        linked_shipment_ids=[booking.id],
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.import_projects[project.id] = project
    sync_project_steps_for_booking(store, project, booking)
    append_import_project_version(
        store,
        project.id,
        actor_id,
        "project_created_from_booking",
        source_reference=booking.id,
        after_summary=project.summary,
    )
    create_import_project_event(
        store,
        project.id,
        "project_created",
        ProjectActorType.system,
        actor_id,
        event_reference=booking.id,
        metadata={"booking_id": booking.id, "workflow_type": project.workflow_type.value},
    )
    return project


def import_project_workspace(store: Store, project_id: str):
    project = store.import_projects[project_id]
    linked_booking_ids = set(project.linked_shipment_ids)
    project_purchase_orders = [
        order for order in store.purchase_orders.values() if order.import_project_id == project_id
    ]
    purchase_order_ids = {order.id for order in project_purchase_orders}
    project_supplier_pay_requests = [
        request for request in store.supplier_pay_requests.values() if request.import_project_id == project_id
    ]
    supplier_pay_request_ids = {request.id for request in project_supplier_pay_requests}
    return {
        "project": project,
        "steps": sorted(
            [step for step in store.import_project_steps.values() if step.import_project_id == project_id],
            key=lambda step: step.step_number,
        ),
        "versions": sorted(
            [version for version in store.import_project_versions.values() if version.import_project_id == project_id],
            key=lambda version: version.version_number,
        ),
        "events": sorted(
            [event for event in store.import_project_events.values() if event.import_project_id == project_id],
            key=lambda event: event.occurred_at,
        ),
        "files": sorted(
            [file for file in store.import_project_files.values() if file.import_project_id == project_id],
            key=lambda file: file.created_at,
            reverse=True,
        ),
        "bookings": [store.bookings[booking_id] for booking_id in project.linked_shipment_ids if booking_id in store.bookings],
        "purchase_orders": sorted(project_purchase_orders, key=lambda order: order.created_at, reverse=True),
        "production_milestones": sorted(
            [
                milestone
                for milestone in store.production_milestones.values()
                if milestone.purchase_order_id in purchase_order_ids
            ],
            key=lambda milestone: ((milestone.due_date or date.max), milestone.created_at),
        ),
        "quality_inspections": sorted(
            [
                inspection
                for inspection in store.quality_inspections.values()
                if inspection.purchase_order_id in purchase_order_ids
            ],
            key=lambda inspection: inspection.created_at,
            reverse=True,
        ),
        "supplier_pay_requests": sorted(
            project_supplier_pay_requests,
            key=lambda request: request.created_at,
            reverse=True,
        ),
        "supplier_pay_quotes": sorted(
            [
                quote
                for quote in store.supplier_pay_quotes.values()
                if quote.supplier_pay_request_id in supplier_pay_request_ids
            ],
            key=lambda quote: quote.created_at,
            reverse=True,
        ),
        "source_messages": sorted(
            [message for message in store.source_messages.values() if message.matched_import_project_id == project_id],
            key=lambda message: message.received_at,
            reverse=True,
        ),
        "automation_runs": sorted(
            [
                run
                for run in store.automation_runs.values()
                if run.input_reference == project_id or run.output_reference == project_id
            ],
            key=lambda run: run.created_at,
            reverse=True,
        ),
        "approvals": sorted(
            [
                approval
                for approval in store.approval_requests.values()
                if approval.related_import_project_id == project_id
                or (approval.related_booking_id and approval.related_booking_id in linked_booking_ids)
            ],
            key=lambda approval: approval.created_at,
            reverse=True,
        ),
    }


def match_source_message_to_booking(store: Store, request: SourceMessageCreate) -> Optional[Booking]:
    haystack = f"{request.subject}\n{request.body}".lower()
    for booking in store.bookings.values():
        if booking.id.lower() in haystack:
            return booking
    for booking in store.bookings.values():
        supplier_name = (booking.supplier_name or "").strip().lower()
        if supplier_name and supplier_name in haystack:
            return booking
        importer = store.importers.get(booking.importer_id)
        if importer and importer.email.lower() == request.from_address.strip().lower():
            return booking
    return None


def create_automation_run(
    store: Store,
    automation_type: AutomationType,
    input_reference: str,
    decision: AutomationDecision,
    reason: str,
    output_reference: Optional[str] = None,
    confidence: SourceConfidence = SourceConfidence.estimated,
    created_tasks: Optional[List[str]] = None,
    created_approvals: Optional[List[str]] = None,
    audit_event_id: Optional[str] = None,
) -> AutomationRun:
    run = AutomationRun(
        id=store.next_id("AUTO"),
        automation_type=automation_type,
        input_reference=input_reference,
        output_reference=output_reference,
        confidence=confidence,
        decision=decision,
        reason=reason,
        created_tasks=created_tasks or [],
        created_approvals=created_approvals or [],
        audit_event_id=audit_event_id,
        created_at=now_utc(),
    )
    store.automation_runs[run.id] = run
    return run


def project_for_purchase_order_request(store: Store, request: PurchaseOrderCreate, actor_id: str) -> ImportProject:
    if request.booking_id:
        if request.booking_id not in store.bookings:
            raise ValueError("Booking not found")
        return ensure_import_project_for_booking(store, store.bookings[request.booking_id], actor_id)
    if request.import_project_id:
        if request.import_project_id not in store.import_projects:
            raise ValueError("Import project not found")
        return store.import_projects[request.import_project_id]
    raise ValueError("Purchase order must be linked to a booking or import project")


def default_milestone_due_dates(request: PurchaseOrderCreate) -> dict:
    production_due = request.production_due_date
    ready_target = request.cargo_ready_target_date or production_due
    today = date.today()
    return {
        ProductionMilestoneType.deposit_paid: today,
        ProductionMilestoneType.production_started: today + timedelta(days=2),
        ProductionMilestoneType.production_complete: production_due,
        ProductionMilestoneType.qc_passed: (production_due + timedelta(days=2)) if production_due else None,
        ProductionMilestoneType.balance_due: production_due,
        ProductionMilestoneType.goods_ready: ready_target,
    }


def create_default_production_milestones(
    store: Store,
    order: PurchaseOrder,
    request: PurchaseOrderCreate,
) -> List[ProductionMilestone]:
    due_dates = default_milestone_due_dates(request)
    specs = [
        (ProductionMilestoneType.deposit_paid, "Deposit paid", "buyer", bool(order.deposit_amount)),
        (ProductionMilestoneType.production_started, "Production started", "supplier", True),
        (ProductionMilestoneType.production_complete, "Production complete", "supplier", True),
        (ProductionMilestoneType.qc_passed, "Quality check passed", "inspector", request.inspection_required),
        (ProductionMilestoneType.balance_due, "Balance payment due", "buyer", bool(order.balance_amount)),
        (ProductionMilestoneType.goods_ready, "Goods ready for pickup", "supplier", True),
    ]
    milestones: List[ProductionMilestone] = []
    for milestone_type, label, owner, enabled in specs:
        if not enabled:
            continue
        milestone = ProductionMilestone(
            id=store.next_id("MS"),
            purchase_order_id=order.id,
            milestone_type=milestone_type,
            label=label,
            due_date=due_dates.get(milestone_type),
            owner=owner,
            status=ProductionMilestoneStatus.pending,
            buyer_approval_required=milestone_type in {
                ProductionMilestoneType.deposit_paid,
                ProductionMilestoneType.balance_due,
            },
            created_at=now_utc(),
            updated_at=now_utc(),
        )
        store.production_milestones[milestone.id] = milestone
        milestones.append(milestone)
    return milestones


def create_quality_inspection(
    store: Store,
    order: PurchaseOrder,
    request: PurchaseOrderCreate,
) -> QualityInspection:
    inspection = QualityInspection(
        id=store.next_id("QC"),
        purchase_order_id=order.id,
        inspection_required=request.inspection_required,
        inspection_date=request.production_due_date,
        inspection_location="Supplier factory" if request.inspection_required else None,
        result=QualityInspectionResult.pending if request.inspection_required else QualityInspectionResult.not_required,
        buyer_approval_required=request.inspection_required,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    store.quality_inspections[inspection.id] = inspection
    return inspection


def book_quality_inspection(
    store: Store,
    inspection_id: str,
    provider: str,
    inspection_date: date,
    location: str,
    actor_id: str,
) -> QualityInspection:
    inspection = store.quality_inspections.get(inspection_id)
    if not inspection:
        raise ValueError(f"QualityInspection {inspection_id} not found")
    inspection.inspection_provider = provider
    inspection.inspection_date = inspection_date
    inspection.inspection_location = location
    inspection.result = QualityInspectionResult.booked
    inspection.updated_at = now_utc()
    create_audit_event(
        store,
        ActorRole.importer,
        actor_id,
        "qc_inspection_booked",
        "quality_inspection",
        inspection.id,
        f"Inspection booked with {provider} on {inspection_date}.",
        {"provider": provider, "date": inspection_date.isoformat(), "location": location},
    )
    create_notification(
        store,
        recipient_type="importer",
        recipient_id="dev-importer",
        trigger="qc_inspection_booked",
        message=f"Inspector {provider} booked for {inspection_date}.",
    )
    return inspection


def record_quality_inspection_result(
    store: Store,
    inspection_id: str,
    result: QualityInspectionResult,
    defects_summary: Optional[str],
    actor_id: str,
) -> Tuple[QualityInspection, Optional[ApprovalRequest]]:
    inspection = store.quality_inspections.get(inspection_id)
    if not inspection:
        raise ValueError(f"QualityInspection {inspection_id} not found")
    inspection.result = result
    if defects_summary is not None:
        inspection.defects_summary = defects_summary
    inspection.updated_at = now_utc()

    create_audit_event(
        store,
        ActorRole.admin,
        actor_id,
        "qc_inspection_result_recorded",
        "quality_inspection",
        inspection.id,
        f"Inspection result: {result.value}.",
        {"result": result.value, "defects": defects_summary},
    )

    approval: Optional[ApprovalRequest] = None
    order = store.purchase_orders.get(inspection.purchase_order_id)
    if result in (QualityInspectionResult.failed, QualityInspectionResult.rework_required) and order:
        approval = create_approval_request(
            store,
            ApprovalRequestType.approve_invoice_variance,  # reuses existing money/legal type for now
            f"Inspection {result.value.replace('_', ' ')} for {order.supplier_name}",
            (
                f"The third-party inspection for {order.supplier_name} cargo returned "
                f"{result.value.replace('_', ' ')}. {defects_summary or 'No detailed defect summary provided.'} "
                "Approve to accept and ship anyway, or reject to hold the cargo."
            ),
            related_import_project_id=order.import_project_id,
            related_booking_id=order.booking_id,
            source_reference=inspection.id,
        )
    elif result == QualityInspectionResult.passed:
        create_notification(
            store,
            recipient_type="importer",
            recipient_id="dev-importer",
            trigger="qc_inspection_passed",
            message=f"Inspection passed for {order.supplier_name if order else 'shipment'}. Cargo can ship.",
        )

    return inspection, approval


def list_quality_inspections_for_booking(store: Store, booking_id: str) -> List[QualityInspection]:
    pos = [po.id for po in store.purchase_orders.values() if po.booking_id == booking_id]
    return [qc for qc in store.quality_inspections.values() if qc.purchase_order_id in pos]


# --- Warehouse cargo measurement variance ---

CBM_VARIANCE_THRESHOLD = 0.10  # 10%
WEIGHT_VARIANCE_THRESHOLD = 0.10
MIN_VARIANCE_USD = 25.0  # below this, don't bother creating an approval


def record_warehouse_measurement(
    store: Store,
    booking_id: str,
    actual_cbm: float,
    actual_weight_kg: float,
    actor_id: str,
    rate_per_cbm_usd: float = 95.0,
) -> Dict[str, Any]:
    """
    Record actual cargo dimensions at the warehouse and detect billing
    variance. If the variance exceeds the threshold and the cost delta is
    material, create an approve_invoice_variance approval and notify the
    importer.
    """
    booking = store.bookings.get(booking_id)
    if not booking:
        raise ValueError(f"Booking {booking_id} not found")

    booked_cbm = booking.cbm_estimate or 0.0
    booked_weight = booking.weight_kg_estimate or 0.0

    booking.cbm_actual = actual_cbm
    booking.weight_kg_actual = actual_weight_kg
    booking.received_at_warehouse = booking.received_at_warehouse or now_utc()

    cbm_variance = (actual_cbm - booked_cbm) / booked_cbm if booked_cbm > 0 else 0.0
    weight_variance = (actual_weight_kg - booked_weight) / booked_weight if booked_weight > 0 else 0.0

    cbm_cost_delta = round_money((actual_cbm - booked_cbm) * rate_per_cbm_usd)
    needs_variance_approval = (
        abs(cbm_variance) >= CBM_VARIANCE_THRESHOLD
        or abs(weight_variance) >= WEIGHT_VARIANCE_THRESHOLD
    )

    approval_id: Optional[str] = None
    if needs_variance_approval and abs(cbm_cost_delta) >= MIN_VARIANCE_USD:
        approval = create_approval_request(
            store,
            ApprovalRequestType.approve_invoice_variance,
            f"Cargo measurement variance for {booking_id}",
            (
                f"Warehouse measured {actual_cbm:.2f} CBM and {actual_weight_kg:.0f} kg "
                f"versus booked {booked_cbm:.2f} CBM and {booked_weight:.0f} kg. "
                f"Estimated freight delta: USD {cbm_cost_delta:+,.2f}. "
                "Approve to bill the new amount, or reject to dispute."
            ),
            amount_usd=abs(cbm_cost_delta),
            related_booking_id=booking_id,
        )
        approval_id = approval.id

    create_audit_event(
        store,
        ActorRole.system,
        actor_id,
        "warehouse_measurement_recorded",
        "booking",
        booking_id,
        f"Warehouse measured cargo: {actual_cbm:.2f} CBM / {actual_weight_kg:.0f} kg.",
        {
            "actual_cbm": actual_cbm,
            "actual_weight_kg": actual_weight_kg,
            "booked_cbm": booked_cbm,
            "booked_weight_kg": booked_weight,
            "cbm_variance_pct": round(cbm_variance * 100, 2),
            "weight_variance_pct": round(weight_variance * 100, 2),
            "cbm_cost_delta_usd": cbm_cost_delta,
        },
    )

    if needs_variance_approval:
        create_notification(
            store,
            recipient_type="importer",
            recipient_id="dev-importer",
            trigger="warehouse_variance",
            message=(
                f"Cargo for {booking_id} measured "
                f"{cbm_variance * 100:+.0f}% on volume. Review the variance approval."
            ),
        )

    return {
        "booking_id": booking_id,
        "actual_cbm": actual_cbm,
        "actual_weight_kg": actual_weight_kg,
        "booked_cbm": booked_cbm,
        "booked_weight_kg": booked_weight,
        "cbm_variance_pct": round(cbm_variance * 100, 2),
        "weight_variance_pct": round(weight_variance * 100, 2),
        "cbm_cost_delta_usd": cbm_cost_delta,
        "needs_variance_approval": needs_variance_approval,
        "approval_request_id": approval_id,
    }


# --- Carrier ETA monitoring ---

ETA_NOTIFY_THRESHOLD_DAYS = 1
ETA_APPROVAL_THRESHOLD_DAYS = 3


def update_container_eta(
    store: Store,
    container_id: str,
    new_eta: date,
    actor_id: str,
    source: str = "carrier_api",
) -> Dict[str, Any]:
    """
    Update a container's ETA. If the baseline is empty, set it. If the new
    ETA differs from the previous by >= ETA_NOTIFY_THRESHOLD_DAYS, notify
    importers on every booking in the container. If it slipped >= 3 days
    past the baseline, also create an approve-sailing-change approval.
    Returns a result dict.
    """
    container = store.containers.get(container_id)
    if not container:
        raise ValueError(f"Container {container_id} not found")

    previous = container.estimated_arrival
    baseline = container.baseline_estimated_arrival
    if baseline is None:
        container.baseline_estimated_arrival = new_eta

    container.estimated_arrival = new_eta
    container.eta_last_changed_at = now_utc()

    delta_days_from_previous = (new_eta - previous).days if previous else 0
    delta_days_from_baseline = (new_eta - container.baseline_estimated_arrival).days

    notifications_sent = 0
    approvals_created = 0
    related_booking_ids: List[str] = []
    for booking in store.bookings.values():
        if booking.container_id == container_id:
            related_booking_ids.append(booking.id)

    if previous and abs(delta_days_from_previous) >= ETA_NOTIFY_THRESHOLD_DAYS:
        for booking_id in related_booking_ids:
            create_notification(
                store,
                recipient_type="importer",
                recipient_id="dev-importer",
                trigger="eta_changed",
                message=(
                    f"ETA for {booking_id} changed from {previous.isoformat()} to "
                    f"{new_eta.isoformat()} ({'+' if delta_days_from_previous >= 0 else ''}"
                    f"{delta_days_from_previous} days)."
                ),
            )
            notifications_sent += 1

    if abs(delta_days_from_baseline) >= ETA_APPROVAL_THRESHOLD_DAYS:
        for booking_id in related_booking_ids:
            existing = next(
                (
                    a for a in store.approval_requests.values()
                    if a.related_booking_id == booking_id
                    and a.request_type == ApprovalRequestType.accept_sailing_change
                    and a.status == ApprovalStatus.pending
                ),
                None,
            )
            if not existing:
                create_approval_request(
                    store,
                    ApprovalRequestType.accept_sailing_change,
                    f"Confirm sailing change for {booking_id}",
                    (
                        f"The carrier moved the arrival to {new_eta.isoformat()} "
                        f"(originally {container.baseline_estimated_arrival.isoformat()}, "
                        f"a {delta_days_from_baseline} day shift). "
                        "Confirm the new dates work or request alternatives."
                    ),
                    related_booking_id=booking_id,
                )
                approvals_created += 1

    create_audit_event(
        store,
        ActorRole.system,
        actor_id,
        "container_eta_updated",
        "container",
        container_id,
        f"ETA updated to {new_eta.isoformat()} (source: {source}).",
        {
            "previous_eta": previous.isoformat() if previous else None,
            "new_eta": new_eta.isoformat(),
            "baseline_eta": container.baseline_estimated_arrival.isoformat() if container.baseline_estimated_arrival else None,
            "delta_days_from_previous": delta_days_from_previous,
            "delta_days_from_baseline": delta_days_from_baseline,
            "source": source,
        },
    )

    return {
        "container_id": container_id,
        "previous_eta": previous.isoformat() if previous else None,
        "new_eta": new_eta.isoformat(),
        "baseline_eta": container.baseline_estimated_arrival.isoformat() if container.baseline_estimated_arrival else None,
        "delta_days_from_previous": delta_days_from_previous,
        "delta_days_from_baseline": delta_days_from_baseline,
        "notifications_sent": notifications_sent,
        "approvals_created": approvals_created,
        "affected_booking_ids": related_booking_ids,
    }


def create_notification(
    store: Store,
    recipient_type: str,
    recipient_id: str,
    trigger: str,
    message: str,
) -> Notification:
    notification = Notification(
        id=store.next_id("NOTIF"),
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        trigger=trigger,
        message=message,
        created_at=now_utc(),
    )
    store.notifications[notification.id] = notification
    return notification


def create_approval_request(
    store: Store,
    request_type: ApprovalRequestType,
    title: str,
    summary: str,
    amount_usd: Optional[float] = None,
    related_import_project_id: Optional[str] = None,
    related_booking_id: Optional[str] = None,
    source_reference: Optional[str] = None,
) -> ApprovalRequest:
    approval = ApprovalRequest(
        id=store.next_id("APPROVAL"),
        request_type=request_type,
        title=title,
        plain_language_summary=summary,
        amount_usd=round_money(amount_usd) if amount_usd is not None else None,
        related_import_project_id=related_import_project_id,
        related_booking_id=related_booking_id,
        source_reference=source_reference,
        created_at=now_utc(),
    )
    store.approval_requests[approval.id] = approval
    create_notification(
        store,
        recipient_type="importer",
        recipient_id="dev-importer",
        trigger="approval_required",
        message=title,
    )
    return approval


def supplier_pay_quotes_for_request(store: Store, supplier_pay_request_id: str) -> List[SupplierPayQuote]:
    return sorted(
        [
            quote
            for quote in store.supplier_pay_quotes.values()
            if quote.supplier_pay_request_id == supplier_pay_request_id
        ],
        key=lambda quote: quote.estimated_total,
    )


def generate_supplier_pay_quotes(store: Store, request: SupplierPayRequest) -> List[SupplierPayQuote]:
    existing = supplier_pay_quotes_for_request(store, request.id)
    if existing:
        return existing
    provider_specs = [
        (SupplierPayProvider.wise, 0.006, 8.0),
        (SupplierPayProvider.ofx, 0.0075, 5.0),
    ]
    quotes: List[SupplierPayQuote] = []
    for provider, variable_fee, fixed_fee in provider_specs:
        provider_fee = round_money(request.amount * variable_fee + fixed_fee)
        total = round_money(request.amount + provider_fee)
        quote = SupplierPayQuote(
            id=store.next_id("SPQ"),
            supplier_pay_request_id=request.id,
            provider=provider,
            provider_reference=f"estimate-{provider.value}-{request.id}",
            source_type=SourceType.manual_admin,
            source_name="Estimated provider comparison until live Wise/OFX APIs are connected",
            amount=round_money(request.amount),
            source_currency=request.currency,
            target_currency=request.currency,
            fx_rate=1,
            provider_fee=provider_fee,
            estimated_total=total,
            expires_at=now_utc() + timedelta(hours=24),
            created_at=now_utc(),
        )
        store.supplier_pay_quotes[quote.id] = quote
        quotes.append(quote)
    selected = min(quotes, key=lambda quote: quote.estimated_total)
    selected.selected = True
    selected.status = SupplierPayQuoteStatus.selected
    store.supplier_pay_quotes[selected.id] = selected
    request.selected_quote_id = selected.id
    request.status = SupplierPayRequestStatus.approval_required
    request.updated_at = now_utc()
    store.supplier_pay_requests[request.id] = request
    return sorted(quotes, key=lambda quote: quote.estimated_total)


def create_supplier_pay_request(
    store: Store,
    purchase_order_id: str,
    request: SupplierPayRequestCreate,
    actor_id: str,
) -> SupplierPayRequest:
    if purchase_order_id not in store.purchase_orders:
        raise ValueError("Purchase order not found")
    order = store.purchase_orders[purchase_order_id]
    timestamp = now_utc()
    pay_request = SupplierPayRequest(
        id=store.next_id("SPR"),
        purchase_order_id=order.id,
        import_project_id=order.import_project_id,
        booking_id=order.booking_id,
        payment_stage=request.payment_stage,
        supplier_name=order.supplier_name,
        supplier_invoice_reference=request.supplier_invoice_reference,
        amount=round_money(request.amount),
        currency=request.currency,
        status=SupplierPayRequestStatus.quote_ready,
        requested_by=actor_id,
        notes=request.notes,
        bank_details_fingerprint=request.bank_details_fingerprint,
        bank_details_changed=request.bank_details_changed,
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.supplier_pay_requests[pay_request.id] = pay_request
    quotes = generate_supplier_pay_quotes(store, pay_request)
    selected_quote = quotes[0]
    approval = create_approval_request(
        store,
        ApprovalRequestType.approve_supplier_payment,
        f"Approve {request.payment_stage.value} payment to {order.supplier_name}",
        (
            f"Pay {request.currency} {request.amount:,.2f} to {order.supplier_name}. "
            f"Recommended provider: {selected_quote.provider.value.upper()} "
            f"with estimated total {selected_quote.target_currency} {selected_quote.estimated_total:,.2f}."
        ),
        amount_usd=selected_quote.estimated_total,
        related_import_project_id=order.import_project_id,
        related_booking_id=order.booking_id,
        source_reference=pay_request.id,
    )
    pay_request.approval_request_id = approval.id
    pay_request.status = SupplierPayRequestStatus.approval_required
    pay_request.updated_at = now_utc()
    store.supplier_pay_requests[pay_request.id] = pay_request
    create_automation_run(
        store,
        AutomationType.supplier_pay_quote,
        pay_request.id,
        AutomationDecision.customer_approval_required,
        "Generated provider comparison and supplier payment approval request.",
        output_reference=selected_quote.id,
        confidence=SourceConfidence.estimated,
        created_approvals=[approval.id],
    )
    create_import_project_event(
        store,
        order.import_project_id,
        "supplier_pay_request_created",
        ProjectActorType.system,
        actor_id,
        event_reference=pay_request.id,
        metadata={"approval_request_id": approval.id, "selected_quote_id": selected_quote.id},
    )
    project = store.import_projects[order.import_project_id]
    project.current_step = "money"
    project.next_action = "Approve the supplier payment or mark it paid outside Ship Hoppa."
    project.updated_at = now_utc()
    store.import_projects[project.id] = project
    upsert_project_step(
        store,
        project,
        "money",
        ImportProjectStepStatus.in_progress,
        {"next_action": project.next_action},
        pay_request.id,
    )
    return pay_request


def create_purchase_order(store: Store, request: PurchaseOrderCreate, actor_id: str) -> PurchaseOrder:
    project = project_for_purchase_order_request(store, request, actor_id)
    timestamp = now_utc()
    order = PurchaseOrder(
        id=store.next_id("PO"),
        import_project_id=project.id,
        booking_id=request.booking_id,
        order_reference=request.order_reference,
        buyer_company_name=request.buyer_company_name,
        supplier_name=request.supplier_name,
        supplier_contact_email=request.supplier_contact_email,
        supplier_contact_phone=request.supplier_contact_phone,
        product_summary=request.product_summary,
        incoterm=request.incoterm,
        currency=request.currency,
        goods_value=round_money(request.goods_value),
        deposit_amount=round_money(request.deposit_amount),
        balance_amount=round_money(request.balance_amount),
        production_due_date=request.production_due_date,
        cargo_ready_target_date=request.cargo_ready_target_date,
        status=PurchaseOrderStatus.deposit_due if request.deposit_amount else PurchaseOrderStatus.order_confirmed,
        source_message_id=request.source_message_id,
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.purchase_orders[order.id] = order
    if order.id not in project.linked_purchase_order_ids:
        project.linked_purchase_order_ids.append(order.id)
    project.current_step = "production"
    project.next_action = "Track production, supplier readiness, and any supplier payment approvals."
    project.updated_at = now_utc()
    store.import_projects[project.id] = project
    create_default_production_milestones(store, order, request)
    create_quality_inspection(store, order, request)
    upsert_project_step(
        store,
        project,
        "order",
        ImportProjectStepStatus.complete,
        {"purchase_order_id": order.id, "order_reference": order.order_reference},
        order.id,
    )
    upsert_project_step(
        store,
        project,
        "production",
        ImportProjectStepStatus.in_progress,
        {"next_action": project.next_action, "purchase_order_id": order.id},
        order.id,
    )
    append_import_project_version(
        store,
        project.id,
        actor_id,
        "purchase_order_created",
        step_key="order",
        source_reference=order.id,
        after_summary=f"Purchase order {order.order_reference} added for {order.supplier_name}.",
    )
    create_import_project_event(
        store,
        project.id,
        "purchase_order_created",
        ProjectActorType.user,
        actor_id,
        event_reference=order.id,
        metadata={"supplier_name": order.supplier_name, "goods_value": order.goods_value},
    )
    if order.deposit_amount:
        create_supplier_pay_request(
            store,
            order.id,
            SupplierPayRequestCreate(
                payment_stage=SupplierPayStage.deposit,
                amount=order.deposit_amount,
                currency=order.currency,
                supplier_invoice_reference=order.order_reference,
                notes="Auto-created from purchase order deposit amount.",
            ),
            actor_id,
        )
    return order


def complete_production_milestone(
    store: Store,
    milestone_id: str,
    request: ProductionMilestoneCompleteRequest,
    actor_id: str,
) -> ProductionMilestone:
    if milestone_id not in store.production_milestones:
        raise ValueError("Production milestone not found")
    milestone = store.production_milestones[milestone_id]
    order = store.purchase_orders[milestone.purchase_order_id]
    milestone.status = ProductionMilestoneStatus.complete
    milestone.completed_at = now_utc()
    milestone.evidence_document_id = request.evidence_document_id
    milestone.notes = request.notes or milestone.notes
    milestone.updated_at = now_utc()
    store.production_milestones[milestone.id] = milestone

    if milestone.milestone_type == ProductionMilestoneType.deposit_paid:
        order.status = PurchaseOrderStatus.deposit_paid
    elif milestone.milestone_type == ProductionMilestoneType.production_started:
        order.status = PurchaseOrderStatus.in_production
    elif milestone.milestone_type == ProductionMilestoneType.production_complete:
        inspection = next(
            (item for item in store.quality_inspections.values() if item.purchase_order_id == order.id),
            None,
        )
        order.status = PurchaseOrderStatus.ready_for_qc if inspection and inspection.inspection_required else PurchaseOrderStatus.ready_to_ship
    elif milestone.milestone_type == ProductionMilestoneType.qc_passed:
        order.status = PurchaseOrderStatus.ready_to_ship
        inspection = next(
            (item for item in store.quality_inspections.values() if item.purchase_order_id == order.id),
            None,
        )
        if inspection:
            inspection.result = QualityInspectionResult.passed
            inspection.updated_at = now_utc()
            store.quality_inspections[inspection.id] = inspection
    elif milestone.milestone_type == ProductionMilestoneType.goods_ready:
        order.status = PurchaseOrderStatus.ready_to_ship
    order.updated_at = now_utc()
    store.purchase_orders[order.id] = order

    project = store.import_projects[order.import_project_id]
    create_import_project_event(
        store,
        project.id,
        "production_milestone_completed",
        ProjectActorType.user,
        actor_id,
        event_reference=milestone.id,
        metadata={"milestone_type": milestone.milestone_type.value, "purchase_order_id": order.id},
    )
    append_import_project_version(
        store,
        project.id,
        actor_id,
        "production_milestone_completed",
        step_key="production",
        source_reference=milestone.id,
        after_summary=f"{milestone.label} completed for {order.order_reference}.",
    )
    return milestone


def approval_for_supplier_pay(store: Store, approval_id: str) -> Optional[SupplierPayRequest]:
    return next(
        (
            request
            for request in store.supplier_pay_requests.values()
            if request.approval_request_id == approval_id
        ),
        None,
    )


def decide_approval_request(store: Store, approval_id: str, status: ApprovalStatus, reason: str, actor_id: str) -> ApprovalRequest:
    if approval_id not in store.approval_requests:
        raise ValueError("Approval not found")
    approval = store.approval_requests[approval_id]
    approval.status = status
    approval.decided_at = now_utc()
    approval.decided_by = actor_id
    store.approval_requests[approval.id] = approval

    pay_request = approval_for_supplier_pay(store, approval.id)
    if pay_request:
        pay_request.status = (
            SupplierPayRequestStatus.approved if status == ApprovalStatus.approved else SupplierPayRequestStatus.rejected
        )
        pay_request.notes = f"{pay_request.notes or ''}\nApproval decision: {reason}".strip()
        pay_request.updated_at = now_utc()
        store.supplier_pay_requests[pay_request.id] = pay_request
        create_import_project_event(
            store,
            pay_request.import_project_id,
            "supplier_pay_approval_decided",
            ProjectActorType.user,
            actor_id,
            event_reference=approval.id,
            metadata={"status": status.value, "supplier_pay_request_id": pay_request.id},
        )
    create_audit_event(
        store,
        ActorRole.importer,
        actor_id,
        "approval_decided",
        "approval_request",
        approval.id,
        reason or f"Approval {status.value}.",
        {"status": status.value},
    )
    return approval


def mark_supplier_pay_paid_outside_app(
    store: Store,
    supplier_pay_request_id: str,
    request: SupplierPayMarkPaidRequest,
    actor_id: str,
) -> SupplierPayRequest:
    if supplier_pay_request_id not in store.supplier_pay_requests:
        raise ValueError("Supplier Pay request not found")
    pay_request = store.supplier_pay_requests[supplier_pay_request_id]
    pay_request.status = SupplierPayRequestStatus.marked_paid_outside_app
    pay_request.marked_paid_at = now_utc()
    pay_request.paid_outside_app_by = request.paid_by
    pay_request.proof_storage_key = request.proof_storage_key
    pay_request.notes = request.notes or pay_request.notes
    pay_request.updated_at = now_utc()
    store.supplier_pay_requests[pay_request.id] = pay_request

    if pay_request.approval_request_id and pay_request.approval_request_id in store.approval_requests:
        approval = store.approval_requests[pay_request.approval_request_id]
        if approval.status == ApprovalStatus.pending:
            approval.status = ApprovalStatus.approved
            approval.decided_at = now_utc()
            approval.decided_by = actor_id
            store.approval_requests[approval.id] = approval

    order = store.purchase_orders[pay_request.purchase_order_id]
    milestone_type = (
        ProductionMilestoneType.deposit_paid
        if pay_request.payment_stage == SupplierPayStage.deposit
        else ProductionMilestoneType.balance_due
    )
    milestone = next(
        (
            item
            for item in store.production_milestones.values()
            if item.purchase_order_id == order.id and item.milestone_type == milestone_type
        ),
        None,
    )
    if milestone and milestone.status != ProductionMilestoneStatus.complete:
        complete_production_milestone(
            store,
            milestone.id,
            ProductionMilestoneCompleteRequest(notes="Payment marked as paid outside Ship Hoppa."),
            actor_id,
        )
    create_import_project_event(
        store,
        pay_request.import_project_id,
        "supplier_pay_marked_paid_outside_app",
        ProjectActorType.user,
        actor_id,
        event_reference=pay_request.id,
        metadata={"paid_by": request.paid_by, "proof_provided": bool(request.proof_storage_key)},
    )
    return pay_request


def ingest_source_message(
    store: Store,
    request: SourceMessageCreate,
    actor_role: ActorRole,
    actor_id: str,
) -> SourceMessage:
    timestamp = now_utc()
    matched_booking = match_source_message_to_booking(store, request)
    matched_project = ensure_import_project_for_booking(store, matched_booking, actor_id) if matched_booking else None
    message = SourceMessage(
        id=store.next_id("SRC"),
        source_type=request.source_type,
        from_address=request.from_address,
        to_addresses=request.to_addresses,
        subject=request.subject,
        body=request.body,
        received_at=normalize_datetime(request.received_at) or timestamp,
        attachments=request.attachment_names,
        matched_import_project_id=matched_project.id if matched_project else None,
        matched_shipment_id=matched_booking.id if matched_booking else None,
        extraction_status=ExtractionStatus.matched if matched_booking else ExtractionStatus.needs_review,
        confidence=SourceConfidence.verified if matched_booking else SourceConfidence.estimated,
        created_at=timestamp,
    )
    store.source_messages[message.id] = message
    if matched_project:
        create_import_project_event(
            store,
            matched_project.id,
            "source_message_ingested",
            ProjectActorType.user if actor_role == ActorRole.importer else ProjectActorType.admin,
            actor_id,
            event_reference=message.id,
            metadata={"subject": message.subject, "matched_booking_id": matched_booking.id if matched_booking else None},
        )
        append_import_project_version(
            store,
            matched_project.id,
            actor_id,
            "source_message_matched",
            source_reference=message.id,
            after_summary=f"Matched source message '{message.subject}' to project.",
        )
    audit = create_audit_event(
        store,
        actor_role,
        actor_id,
        "source_message_ingested",
        "source_message",
        message.id,
        "Inbound source message was ingested and matched." if matched_booking else "Inbound source message needs matching review.",
        {"matched_booking_id": message.matched_shipment_id, "matched_project_id": message.matched_import_project_id},
    )
    create_automation_run(
        store,
        AutomationType.match_message,
        message.id,
        AutomationDecision.auto_accepted if matched_booking else AutomationDecision.admin_review_required,
        "Matched by booking id, supplier name or importer email." if matched_booking else "No booking or supplier match found.",
        output_reference=matched_project.id if matched_project else None,
        confidence=message.confidence,
        audit_event_id=audit.id,
    )

    if matched_booking and looks_like_invoice(request.subject, request.body):
        from .invoices import extract_invoice_from_text
        text = f"{request.subject or ''}\n{request.body or ''}"
        parsed = extract_invoice_from_text(text)
        if parsed.total_amount and parsed.currency:
            apply_parsed_invoice(
                store,
                parsed,
                actor_id,
                hint_booking_id=matched_booking.id,
                source_message_id=message.id,
            )

    return message


INVOICE_KEYWORDS = (
    "invoice",
    "proforma",
    "amount due",
    "balance due",
    "payment due",
    "remit",
    "swift",
    "iban",
    "tax invoice",
    "commercial invoice",
)


def looks_like_invoice(subject: Optional[str], body: Optional[str]) -> bool:
    """Lightweight heuristic for whether an inbound message contains a payable
    invoice. Used to gate automatic invoice extraction on ingest."""
    haystack = f"{subject or ''}\n{body or ''}".lower()
    if not haystack.strip():
        return False
    matches = sum(1 for keyword in INVOICE_KEYWORDS if keyword in haystack)
    return matches >= 2


def create_growth_event(
    store: Store,
    event_type: GrowthAttributionEventType,
    source: str,
    supplier_lead_id: Optional[str] = None,
    channel: Optional[str] = None,
    category: Optional[str] = None,
    region: Optional[str] = None,
    campaign_id: Optional[str] = None,
    shipment_id: Optional[str] = None,
    value_usd: Optional[float] = None,
) -> GrowthAttributionEvent:
    event = GrowthAttributionEvent(
        id=store.next_id("GROW"),
        event_type=event_type,
        supplier_lead_id=supplier_lead_id,
        shipment_id=shipment_id,
        campaign_id=campaign_id,
        source=source,
        channel=channel,
        category=category,
        region=region,
        value_usd=value_usd,
        occurred_at=now_utc(),
    )
    store.growth_attribution_events[event.id] = event
    return event


def update_supplier_lead_verification(
    store: Store,
    lead_id: str,
    request: SupplierVerificationUpdate,
    actor_role: ActorRole,
    actor_id: str,
) -> SupplierLead:
    lead = store.supplier_leads.get(lead_id)
    if not lead:
        raise ValueError("Supplier lead not found")
    previous_status = lead.verification_status
    lead.verification_status = request.verification_status
    if request.verification_notes is not None:
        lead.verification_notes = request.verification_notes
    if request.verification_status == SupplierVerificationStatus.verified:
        lead.verified_at = now_utc()
        lead.verified_by = actor_id
    elif request.verification_status == SupplierVerificationStatus.rejected:
        lead.do_not_contact = True
    lead.updated_at = now_utc()
    store.supplier_leads[lead.id] = lead
    create_audit_event(
        store,
        actor_role,
        actor_id,
        "supplier_lead_verification_updated",
        "supplier_lead",
        lead.id,
        f"Verification status moved from {previous_status.value} to {lead.verification_status.value}.",
        {
            "previous_status": previous_status.value,
            "new_status": lead.verification_status.value,
        },
    )
    return lead


def create_supplier_lead_from_discovery(
    store: Store,
    discovery_run: SupplierDiscoveryRun,
    source_url: str,
) -> SupplierLead:
    city_slug = (discovery_run.target_city or "China").replace(" ", "")
    category_label = discovery_run.product_category.replace("_", " ").title()
    lead = SupplierLead(
        id=store.next_id("LEAD"),
        company_name=f"{city_slug} {category_label} Export Co.",
        country=discovery_run.target_country.value.replace("_", " ").title(),
        city=discovery_run.target_city,
        product_categories=[discovery_run.product_category],
        discovery_source=SupplierLeadSource.seo_engine,
        discovery_source_url=source_url,
        company_website=source_url,
        public_contact_source_url=source_url,
        public_contact_captured_at=now_utc(),
        preferred_language="zh-CN" if discovery_run.target_country.value == "china" else "en",
        exports_to_regions=["Australia", "United States"],
        overseas_buyer_signals=["SEO segment indicates overseas buyer workflow pain"],
        bulky_goods_fit=True,
        lead_score=72,
        fit_reason="Matches a high-intent SEO supplier segment and needs human source verification before outreach.",
        compliance_basis="Admin/SEO seeded discovery segment; first contact requires review before sending.",
        contact_method_allowed=ContactMethod.none,
        outreach_status=SupplierOutreachStatus.needs_human_review,
        supplier_discovery_run_id=discovery_run.id,
        notes="Private draft lead created by guarded supplier acquisition autopilot.",
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    store.supplier_leads[lead.id] = lead
    create_growth_event(
        store,
        GrowthAttributionEventType.lead_discovered,
        source="seo_engine",
        supplier_lead_id=lead.id,
        category=discovery_run.product_category,
        region=discovery_run.target_city,
    )
    return lead


def create_supplier_discovery_run_from_opportunity(
    store: Store,
    opportunity: SEOOpportunity,
) -> SupplierDiscoveryRun:
    timestamp = now_utc()
    query_terms = opportunity.keyword_cluster or [
        term
        for term in [
            opportunity.category,
            opportunity.city,
            opportunity.lane,
            "export supplier",
            "overseas buyer",
        ]
        if term
    ]
    run = SupplierDiscoveryRun(
        id=store.next_id("DISC"),
        seo_opportunity_id=opportunity.id,
        target_country=opportunity.target_country,
        target_city=opportunity.city,
        product_category=opportunity.category,
        lane=opportunity.lane,
        source_set=SupplierDiscoverySourceSet.mixed,
        query_terms=query_terms,
        source_rules=[
            "Use permitted public business sources only.",
            "Store source URL and contact basis before outreach.",
            "Require human approval for first contact until source/template is proven.",
        ],
        run_status=SupplierDiscoveryRunStatus.running,
        compliance_review_required=True,
        started_at=timestamp,
        created_at=timestamp,
    )
    store.supplier_discovery_runs[run.id] = run
    source_url = f"internal://seo-opportunities/{opportunity.id}"
    lead = create_supplier_lead_from_discovery(store, run, source_url)
    run.leads_found = 1
    run.leads_enriched = 1
    run.leads_approved_for_contact = 0
    run.run_status = SupplierDiscoveryRunStatus.completed
    run.completed_at = now_utc()
    store.supplier_discovery_runs[run.id] = run
    opportunity.related_supplier_discovery_run_id = run.id
    opportunity.status = SEOOpportunityStatus.brief_ready
    opportunity.updated_at = now_utc()
    store.seo_opportunities[opportunity.id] = opportunity
    create_automation_run(
        store,
        AutomationType.supplier_discovery,
        opportunity.id,
        AutomationDecision.admin_review_required,
        "Created a private draft supplier lead in review-first mode.",
        output_reference=lead.id,
        confidence=SourceConfidence.estimated,
    )
    return run


def create_seo_opportunity(store: Store, request: SEOOpportunityCreate, actor_id: str) -> SEOOpportunity:
    timestamp = now_utc()
    opportunity = SEOOpportunity(
        id=store.next_id("SEO"),
        target_country=request.target_country,
        audience=request.audience,
        category=request.category,
        city=request.city,
        lane=request.lane,
        keyword_cluster=request.keyword_cluster,
        search_intent=request.search_intent,
        source=request.source,
        opportunity_score=request.opportunity_score,
        page_type=request.page_type,
        status=SEOOpportunityStatus.discovered,
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.seo_opportunities[opportunity.id] = opportunity
    create_audit_event(
        store,
        ActorRole.admin,
        actor_id,
        "seo_opportunity_created",
        "seo_opportunity",
        opportunity.id,
        f"SEO opportunity created for {opportunity.category}.",
        {"target_country": opportunity.target_country.value, "city": opportunity.city},
    )
    if request.create_discovery_run:
        create_supplier_discovery_run_from_opportunity(store, opportunity)
    return store.seo_opportunities[opportunity.id]


def requirement_specs(booking: Booking) -> List[tuple[DocumentType, bool, str]]:
    specs: List[tuple[DocumentType, bool, str]] = [
        (DocumentType.commercial_invoice, True, "Required for customs value and supplier details."),
        (DocumentType.packing_list, True, "Required to verify packages, CBM, and weight."),
        (DocumentType.supplier_photos, True, "Required for warehouse proof and damage control."),
        (DocumentType.shipping_instructions, booking.status != BookingStatus.submitted, "Required once the booking is confirmed."),
        (DocumentType.house_bill, False, "Issued after carrier/forwarder documentation is confirmed."),
        (DocumentType.arrival_notice, False, "Added near destination arrival."),
        (DocumentType.delivery_order, False, "Added when freight is released."),
    ]
    if booking.cargo_category in {
        CargoCategory.furniture,
        CargoCategory.homewares,
        CargoCategory.bathroom_fittings,
        CargoCategory.lighting,
        CargoCategory.automotive,
        CargoCategory.other,
    }:
        specs.append((DocumentType.product_specs, True, "Required to classify goods and check restrictions."))
    if booking.cargo_category in {CargoCategory.furniture, CargoCategory.homewares, CargoCategory.garden}:
        specs.append((DocumentType.fumigation_ispm, True, "Timber packaging may require ISPM 15/fumigation evidence."))
    return specs


def ensure_document_requirements(store: Store, booking: Booking) -> List[DocumentRequirement]:
    timestamp = now_utc()
    existing = {
        req.document_type: req
        for req in store.document_requirements.values()
        if req.booking_id == booking.id
    }
    requirements: List[DocumentRequirement] = []
    for doc_type, required, reason in requirement_specs(booking):
        if doc_type in existing:
            requirement = existing[doc_type]
            requirement.required = required
            requirement.reason = reason
            if not required and requirement.status == DocumentStatus.required:
                requirement.status = DocumentStatus.waived
            if required and requirement.status == DocumentStatus.waived and doc_type in {
                DocumentType.shipping_instructions,
                DocumentType.product_specs,
                DocumentType.fumigation_ispm,
            }:
                requirement.status = DocumentStatus.required
            requirement.updated_at = timestamp
        else:
            requirement = DocumentRequirement(
                id=store.next_id("REQ"),
                booking_id=booking.id,
                document_type=doc_type,
                label=DOCUMENT_LABELS[doc_type],
                required=required,
                reason=reason,
                status=DocumentStatus.required if required else DocumentStatus.waived,
                created_at=timestamp,
                updated_at=timestamp,
            )
        store.document_requirements[requirement.id] = requirement
        requirements.append(requirement)
    return sorted(requirements, key=lambda item: DOCUMENT_LABELS[item.document_type])


def documents_for_booking(store: Store, booking_id: str) -> List[ShipmentDocument]:
    return sorted(
        [doc for doc in store.shipment_documents.values() if doc.booking_id == booking_id],
        key=lambda item: item.created_at,
        reverse=True,
    )


def update_booking_health(store: Store, booking: Booking) -> Booking:
    requirements = ensure_document_requirements(store, booking)
    active_required = [req for req in requirements if req.required]
    missing = [
        req
        for req in active_required
        if req.status not in {DocumentStatus.approved, DocumentStatus.waived}
    ]
    if not missing:
        booking.checklist_status = ChecklistStatus.complete
    elif any(req.status == DocumentStatus.uploaded for req in missing):
        booking.checklist_status = ChecklistStatus.in_review
    else:
        booking.checklist_status = ChecklistStatus.incomplete

    events = events_for_booking(store, booking.id)
    if events:
        booking.tracking_status = events[-1].stage

    invoice = invoice_for_booking(store, booking.id)
    if invoice:
        booking.payment_status = invoice.status

    active_holds = [hold for hold in store.release_holds.values() if hold.booking_id == booking.id and hold.status == ReleaseHoldStatus.active]
    booking.release_status = ReleaseStatus.ready if not active_holds else ReleaseStatus.blocked
    booking.exception_count = len(missing) + len(active_holds)
    booking.updated_at = now_utc()
    store.bookings[booking.id] = booking
    return booking


def checklist_for_booking(store: Store, booking_id: str) -> BookingChecklistResponse:
    booking = store.bookings[booking_id]
    requirements = ensure_document_requirements(store, booking)
    docs = documents_for_booking(store, booking_id)
    approved_types = {doc.document_type for doc in docs if doc.status == DocumentStatus.approved}
    missing = [
        req.document_type
        for req in requirements
        if req.required and req.status not in {DocumentStatus.approved, DocumentStatus.waived} and req.document_type not in approved_types
    ]
    update_release_holds(store, booking)
    booking = update_booking_health(store, booking)
    return BookingChecklistResponse(
        booking_id=booking_id,
        checklist_status=booking.checklist_status,
        requirements=requirements,
        documents=docs,
        missing_document_types=missing,
    )


def save_document_content(document_id: str, request: DocumentUploadRequest) -> tuple[str, int]:
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    safe_name = request.file_name.replace("/", "_").replace("\\", "_")
    storage_path = STORAGE_ROOT / f"{document_id}-{safe_name}"
    if request.content_base64:
        payload = base64.b64decode(request.content_base64)
    else:
        payload = f"Ship Hoppa document placeholder for {safe_name}\n".encode("utf-8")
    storage_path.write_bytes(payload)
    return str(storage_path.relative_to(STORAGE_ROOT.parent)), len(payload)


def upload_document(
    store: Store,
    booking_id: str,
    request: DocumentUploadRequest,
    actor_role: ActorRole,
    actor_id: str,
) -> ShipmentDocument:
    booking = store.bookings[booking_id]
    timestamp = now_utc()
    document_id = store.next_id("DOC")
    storage_key, size_bytes = save_document_content(document_id, request)
    document = ShipmentDocument(
        id=document_id,
        booking_id=booking_id,
        document_type=request.document_type,
        file_name=request.file_name,
        storage_key=storage_key,
        mime_type=request.mime_type,
        size_bytes=size_bytes,
        uploaded_by_role=actor_role,
        uploaded_by_id=actor_id,
        notes=request.notes,
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.shipment_documents[document.id] = document
    project = ensure_import_project_for_booking(store, booking, actor_id)
    project_file = ImportProjectFile(
        id=store.next_id("IPF"),
        import_project_id=project.id,
        shipment_id=booking_id,
        folder="documents",
        filename=request.file_name,
        content_type=request.mime_type,
        size_bytes=size_bytes,
        storage_key=f"{project.id}/documents/{request.file_name}",
        backup_storage_key=f"{project.id}/documents/{now_utc().strftime('%Y-%m-%dT%H-%M-%S')}_{request.file_name}",
        archive_storage_key=f"{project.id}/documents/{now_utc().strftime('%Y-%m-%dT%H-%M-%S')}_{request.file_name}",
        archive_created_at=now_utc(),
        backup_status=FileBackupStatus.pending,
        uploaded_by=actor_id,
        document_id=document.id,
        created_at=timestamp,
    )
    store.import_project_files[project_file.id] = project_file
    create_import_project_event(
        store,
        project.id,
        "project_file_added",
        ProjectActorType.user if actor_role == ActorRole.importer else ProjectActorType.admin,
        actor_id,
        event_reference=project_file.id,
        metadata={"document_id": document.id, "filename": request.file_name},
    )
    for requirement in ensure_document_requirements(store, booking):
        if requirement.document_type == request.document_type and requirement.status != DocumentStatus.approved:
            requirement.status = DocumentStatus.uploaded
            requirement.updated_at = timestamp
            store.document_requirements[requirement.id] = requirement
    create_admin_task(store, booking, "review_document", f"Review {DOCUMENT_LABELS[request.document_type]} for {booking.id}")
    create_audit_event(
        store,
        actor_role,
        actor_id,
        "document_uploaded",
        "booking",
        booking_id,
        f"{DOCUMENT_LABELS[request.document_type]} uploaded for booking {booking_id}.",
        {"document_id": document.id, "storage_key": storage_key, "import_project_file_id": project_file.id},
    )
    update_release_holds(store, booking)
    update_booking_health(store, booking)
    return document


def decide_document(
    store: Store,
    document_id: str,
    status: DocumentStatus,
    request: DocumentDecisionRequest,
    actor_id: str,
) -> ShipmentDocument:
    document = store.shipment_documents[document_id]
    timestamp = now_utc()
    document.status = status
    document.reviewed_by = actor_id
    document.reviewed_at = timestamp
    document.review_note = request.reason
    document.updated_at = timestamp
    store.shipment_documents[document.id] = document
    for requirement in ensure_document_requirements(store, store.bookings[document.booking_id]):
        if requirement.document_type == document.document_type:
            requirement.status = status
            requirement.updated_at = timestamp
            store.document_requirements[requirement.id] = requirement
    create_audit_event(
        store,
        ActorRole.admin,
        actor_id,
        f"document_{status.value}",
        "document",
        document.id,
        f"{DOCUMENT_LABELS[document.document_type]} {status.value} for booking {document.booking_id}.",
        {"reason": request.reason},
    )
    update_release_holds(store, store.bookings[document.booking_id])
    update_booking_health(store, store.bookings[document.booking_id])
    return document


def create_shipment_event(store: Store, booking_id: str, payload: ShipmentEventCreate) -> ShipmentEvent:
    booking = store.bookings[booking_id]
    event = ShipmentEvent(
        id=store.next_id("EVT"),
        booking_id=booking_id,
        container_id=booking.container_id,
        stage=payload.stage,
        label=payload.label or DOCUMENT_LABELS.get(payload.stage, payload.stage.value.replace("_", " ").title()),
        source_type=payload.source_type,
        source_name=payload.source_name,
        confidence=payload.confidence,
        occurred_at=normalize_datetime(payload.occurred_at),
        estimated_at=normalize_datetime(payload.estimated_at),
        notes=payload.notes,
        created_at=now_utc(),
    )
    store.shipment_events[event.id] = event
    booking.tracking_status = event.stage
    booking.updated_at = now_utc()
    store.bookings[booking.id] = booking
    return event


def events_for_booking(store: Store, booking_id: str) -> List[ShipmentEvent]:
    return sorted(
        [event for event in store.shipment_events.values() if event.booking_id == booking_id],
        key=shipment_event_sort_key,
    )


def ensure_customs_profile(store: Store, booking: Booking) -> CustomsProfile:
    for profile in store.customs_profiles.values():
        if profile.booking_id == booking.id:
            return recalculate_customs_profile(store, profile)
    flags: List[str] = []
    if booking.cargo_category in {CargoCategory.furniture, CargoCategory.homewares, CargoCategory.garden}:
        flags.append("timber_packaging_ispm_15")
    if booking.cargo_category in {CargoCategory.tiles_stone, CargoCategory.bathroom_fittings}:
        flags.append("biosecurity_inspection_possible")
    profile = CustomsProfile(
        id=store.next_id("CUS"),
        booking_id=booking.id,
        goods_value_usd=10000,
        hs_code=booking.hs_code,
        biosecurity_flags=flags,
        updated_at=now_utc(),
    )
    store.customs_profiles[profile.id] = recalculate_customs_profile(store, profile)
    return store.customs_profiles[profile.id]


def recalculate_customs_profile(store: Store, profile: CustomsProfile) -> CustomsProfile:
    booking = store.bookings[profile.booking_id]
    freight = booking.total_cost_usd or 0
    duty_rate = 0.05
    if (profile.hs_code or "").startswith(("940", "830")):
        duty_rate = 0.03
    profile.duty_estimate_usd = round_money(profile.goods_value_usd * duty_rate)
    profile.brokerage_fee_usd = 175 if profile.broker_preference == CustomsBrokerPreference.ship_hoppa_broker else 0
    profile.gst_estimate_usd = round_money((profile.goods_value_usd + freight + profile.duty_estimate_usd) * 0.10)
    profile.landed_cost_estimate_usd = round_money(
        profile.goods_value_usd + freight + profile.duty_estimate_usd + profile.gst_estimate_usd + profile.brokerage_fee_usd
    )
    profile.updated_at = now_utc()
    store.customs_profiles[profile.id] = profile
    return profile


def update_customs_profile(store: Store, booking_id: str, request: CustomsProfileUpdate) -> CustomsProfile:
    profile = ensure_customs_profile(store, store.bookings[booking_id])
    data = request.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(profile, key, value)
    profile = recalculate_customs_profile(store, profile)
    update_release_holds(store, store.bookings[booking_id])
    update_booking_health(store, store.bookings[booking_id])
    return profile


def invoice_for_booking(store: Store, booking_id: str) -> Optional[Invoice]:
    for invoice in store.invoices.values():
        if invoice.booking_id == booking_id and invoice.status != PaymentStatus.void:
            return invoice
    return None


def service_fee_category(booking: Booking) -> str:
    if booking.urgency_fee_usd >= 150:
        return "Rush"
    if booking.urgency_fee_usd > 0:
        return "Priority"
    return "Standard"


def invoice_line_specs(booking: Booking) -> List[tuple[str, float, str]]:
    category = service_fee_category(booking)
    service_fee = (booking.platform_fee_usd or 0) + booking.urgency_fee_usd
    return [
        ("Pro-rata container share", booking.cbm_cost_usd or 0, "freight_share"),
        (f"Ship Hoppa service fee - {category}", service_fee, f"ship_hoppa_service_fee_{category.lower()}"),
        ("Ship Hoppa pickup", booking.pickup_fee_usd, "pickup_fee"),
        ("Customs brokerage estimate", 175, "customs_brokerage"),
        ("Destination terminal estimate", 220, "destination_charge"),
    ]


def apply_invoice_lines(store: Store, invoice: Invoice, booking: Booking) -> Invoice:
    line_items = [
        InvoiceLineItem(id=store.next_id("LINE"), invoice_id=invoice.id, label=label, amount_usd=round_money(amount), source=source)
        for label, amount, source in invoice_line_specs(booking)
        if amount
    ]
    total = round_money(sum(item.amount_usd for item in line_items))
    invoice.line_items = line_items
    invoice.subtotal_usd = total
    invoice.total_usd = total
    invoice.updated_at = now_utc()
    return invoice


def ensure_invoice(store: Store, booking: Booking) -> Invoice:
    existing = invoice_for_booking(store, booking.id)
    if existing:
        if any(item.source in {"platform_fee", "urgency_fee"} for item in existing.line_items):
            existing = apply_invoice_lines(store, existing, booking)
            store.invoices[existing.id] = existing
        return existing
    timestamp = now_utc()
    invoice_id = store.next_id("INV")
    invoice = Invoice(
        id=invoice_id,
        booking_id=booking.id,
        status=PaymentStatus.issued,
        line_items=[],
        subtotal_usd=0,
        total_usd=0,
        issued_at=timestamp,
        due_date=date.today() + timedelta(days=7),
        created_at=timestamp,
        updated_at=timestamp,
    )
    invoice = apply_invoice_lines(store, invoice, booking)
    store.invoices[invoice.id] = invoice
    booking.payment_status = invoice.status
    store.bookings[booking.id] = booking
    update_release_holds(store, booking)
    return invoice


def mark_invoice_paid(store: Store, invoice_id: str, actor_id: str) -> Invoice:
    invoice = store.invoices[invoice_id]
    timestamp = now_utc()
    invoice.status = PaymentStatus.paid
    invoice.paid_at = timestamp
    invoice.updated_at = timestamp
    store.invoices[invoice.id] = invoice
    payment = PaymentRecord(
        id=store.next_id("PAY"),
        invoice_id=invoice.id,
        amount_usd=invoice.total_usd,
        method="manual_admin",
        provider_reference=f"manual-{invoice.id}",
        paid_at=timestamp,
        created_at=timestamp,
    )
    store.payment_records[payment.id] = payment
    booking = store.bookings[invoice.booking_id]
    booking.paid = True
    booking.paid_at = timestamp
    booking.payment_status = PaymentStatus.paid
    store.bookings[booking.id] = booking
    create_audit_event(store, ActorRole.admin, actor_id, "invoice_marked_paid", "invoice", invoice.id, f"Invoice {invoice.id} marked paid.")
    update_release_holds(store, booking)
    update_booking_health(store, booking)
    return invoice


def get_or_create_hold(store: Store, booking_id: str, hold_type: ReleaseHoldType, reason: str) -> ReleaseHold:
    for hold in store.release_holds.values():
        if hold.booking_id == booking_id and hold.hold_type == hold_type and hold.status == ReleaseHoldStatus.active:
            hold.reason = reason
            return hold
    hold = ReleaseHold(
        id=store.next_id("HOLD"),
        booking_id=booking_id,
        hold_type=hold_type,
        reason=reason,
        created_at=now_utc(),
    )
    store.release_holds[hold.id] = hold
    return hold


def clear_holds(store: Store, booking_id: str, hold_type: ReleaseHoldType) -> None:
    for hold in store.release_holds.values():
        if hold.booking_id == booking_id and hold.hold_type == hold_type and hold.status == ReleaseHoldStatus.active:
            hold.status = ReleaseHoldStatus.cleared
            hold.cleared_at = now_utc()
            store.release_holds[hold.id] = hold


def update_release_holds(store: Store, booking: Booking) -> List[ReleaseHold]:
    checklist = checklist_for_booking_without_holds(store, booking)
    if checklist.checklist_status != ChecklistStatus.complete:
        get_or_create_hold(store, booking.id, ReleaseHoldType.missing_documents, "Required documents are not fully approved.")
    else:
        clear_holds(store, booking.id, ReleaseHoldType.missing_documents)

    invoice = invoice_for_booking(store, booking.id)
    if invoice and invoice.status != PaymentStatus.paid:
        get_or_create_hold(store, booking.id, ReleaseHoldType.unpaid_invoice, "Invoice must be paid before freight release.")
    elif invoice and invoice.status == PaymentStatus.paid:
        clear_holds(store, booking.id, ReleaseHoldType.unpaid_invoice)

    profile = ensure_customs_profile(store, booking)
    if profile.customs_status != CustomsStatus.cleared:
        get_or_create_hold(store, booking.id, ReleaseHoldType.customs_hold, "Customs is not cleared yet.")
    else:
        clear_holds(store, booking.id, ReleaseHoldType.customs_hold)

    if booking.admin_review_required:
        get_or_create_hold(store, booking.id, ReleaseHoldType.admin_hold, "Operations review is still required.")
    else:
        clear_holds(store, booking.id, ReleaseHoldType.admin_hold)

    active = [hold for hold in store.release_holds.values() if hold.booking_id == booking.id and hold.status == ReleaseHoldStatus.active]
    booking.release_status = ReleaseStatus.blocked if active else ReleaseStatus.ready
    store.bookings[booking.id] = booking
    return active


def checklist_for_booking_without_holds(store: Store, booking: Booking) -> BookingChecklistResponse:
    requirements = ensure_document_requirements(store, booking)
    docs = documents_for_booking(store, booking.id)
    approved_types = {doc.document_type for doc in docs if doc.status == DocumentStatus.approved}
    missing = [
        req.document_type
        for req in requirements
        if req.required and req.status not in {DocumentStatus.approved, DocumentStatus.waived} and req.document_type not in approved_types
    ]
    if not missing:
        status = ChecklistStatus.complete
    elif any(req.status == DocumentStatus.uploaded for req in requirements if req.document_type in missing):
        status = ChecklistStatus.in_review
    else:
        status = ChecklistStatus.incomplete
    return BookingChecklistResponse(
        booking_id=booking.id,
        checklist_status=status,
        requirements=requirements,
        documents=docs,
        missing_document_types=missing,
    )


FCL_CONTAINER_CBM_20FT = 33.0
FCL_CONTAINER_CBM_40FT = 67.0
FCL_PROTECTED_BUFFER_CBM = 4.0  # leave room for stuffing and last-minute volume drift
FCL_RECOVERABLE_RATE_USD_PER_CBM = 95.0  # rough internal rate for spare-space sales


def match_invoice_to_purchase_order(
    store: Store, parsed_invoice, hint_booking_id: Optional[str] = None,
) -> Optional[PurchaseOrder]:
    """
    Best-effort match of a ParsedInvoice to an existing PurchaseOrder.

    Strategy (first match wins):
      1. PO reference from the invoice text matches a PurchaseOrder.order_reference.
      2. The hint booking has exactly one PurchaseOrder.
      3. Supplier-name match against any PO and the booking range.
    """
    if parsed_invoice.purchase_order_reference:
        for po in store.purchase_orders.values():
            if po.order_reference and po.order_reference.upper() == parsed_invoice.purchase_order_reference.upper():
                return po

    if hint_booking_id:
        candidates = [po for po in store.purchase_orders.values() if po.booking_id == hint_booking_id]
        if len(candidates) == 1:
            return candidates[0]

    if parsed_invoice.beneficiary_name or parsed_invoice.supplier_name:
        target = (parsed_invoice.beneficiary_name or parsed_invoice.supplier_name or "").lower()
        for po in store.purchase_orders.values():
            if po.supplier_name and po.supplier_name.lower() in target:
                return po

    return None


def apply_parsed_invoice(
    store: Store,
    parsed_invoice,
    actor_id: str,
    hint_booking_id: Optional[str] = None,
    source_message_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Apply a ParsedInvoice to the store. If a PO match is found and the
    invoice has a total_amount and currency, create a SupplierPayRequest
    plus its approval. Returns a result dict describing what happened.
    """
    matched_po = match_invoice_to_purchase_order(store, parsed_invoice, hint_booking_id)
    result: Dict[str, Any] = {
        "matched_purchase_order_id": matched_po.id if matched_po else None,
        "supplier_pay_request_id": None,
        "approval_request_id": None,
    }

    if not matched_po or parsed_invoice.total_amount is None or not parsed_invoice.currency:
        return result

    # Avoid duplicate SupplierPayRequest for the same invoice number on the same PO
    invoice_ref = parsed_invoice.invoice_number or parsed_invoice.proforma_number
    if invoice_ref:
        existing = next(
            (
                sp for sp in store.supplier_pay_requests.values()
                if sp.purchase_order_id == matched_po.id
                and sp.supplier_invoice_reference == invoice_ref
            ),
            None,
        )
        if existing:
            result["supplier_pay_request_id"] = existing.id
            return result

    # Decide payment stage from the matched PO state
    paid_stage_count = sum(
        1 for sp in store.supplier_pay_requests.values()
        if sp.purchase_order_id == matched_po.id and sp.marked_paid_at
    )
    payment_stage = SupplierPayStage.deposit if paid_stage_count == 0 else SupplierPayStage.balance

    pay_request = create_supplier_pay_request(
        store,
        matched_po.id,
        SupplierPayRequestCreate(
            payment_stage=payment_stage,
            amount=parsed_invoice.total_amount,
            currency=parsed_invoice.currency,
            supplier_invoice_reference=invoice_ref,
            notes=f"Extracted from invoice{f' (source: {source_message_id})' if source_message_id else ''}.",
            bank_details_fingerprint=parsed_invoice.account_number_last4 or parsed_invoice.iban_last4,
            bank_details_changed=False,
        ),
        actor_id=actor_id,
    )

    result["supplier_pay_request_id"] = pay_request.id
    result["approval_request_id"] = pay_request.approval_request_id
    return result


def detect_fcl_spare_space(store: Store, booking_id: str) -> Optional[SpaceOpportunity]:
    """
    Detect whether an FCL booking has spare capacity that could be sold to
    other importers. Returns a SpaceOpportunity if recoverable_cbm > 0,
    otherwise None. Idempotent: if an opportunity already exists for the
    booking and is still active, returns it.
    """
    booking = store.bookings.get(booking_id)
    if not booking:
        return None

    project = next(
        (p for p in store.import_projects.values() if booking_id in (p.linked_shipment_ids or [])),
        None,
    )
    is_fcl = bool(project and project.workflow_type == ImportWorkflowType.fcl_spare_space)
    if not is_fcl:
        return None

    container = store.containers.get(booking.container_id) if booking.container_id else None
    container_cbm = FCL_CONTAINER_CBM_40FT if container is None else (container.current_cbm + container.remaining_cbm)
    booked_cbm = booking.cbm_actual or booking.cbm_estimate or 0.0
    recoverable = max(0.0, container_cbm - booked_cbm - FCL_PROTECTED_BUFFER_CBM)

    existing = next(
        (
            opp for opp in store.space_opportunities.values()
            if opp.booking_id == booking_id and opp.status not in (SpaceOpportunityStatus.closed, SpaceOpportunityStatus.declined)
        ),
        None,
    )

    if existing:
        existing.total_container_cbm = round_money(container_cbm)
        existing.booked_cbm = round_money(booked_cbm)
        existing.recoverable_cbm = round_money(recoverable)
        existing.estimated_recovery_usd = round_money(recoverable * FCL_RECOVERABLE_RATE_USD_PER_CBM)
        return existing

    if recoverable < 1.0:
        return None

    opportunity = SpaceOpportunity(
        id=store.next_id("SPACE"),
        booking_id=booking_id,
        container_id=booking.container_id,
        total_container_cbm=round_money(container_cbm),
        booked_cbm=round_money(booked_cbm),
        protected_buffer_cbm=FCL_PROTECTED_BUFFER_CBM,
        recoverable_cbm=round_money(recoverable),
        estimated_recovery_usd=round_money(recoverable * FCL_RECOVERABLE_RATE_USD_PER_CBM),
        owner_actor_id=booking.importer_id,
        detected_at=now_utc(),
    )
    store.space_opportunities[opportunity.id] = opportunity
    return opportunity


def list_space_opportunities_for_booking(store: Store, booking_id: str) -> List[SpaceOpportunity]:
    return [
        opp for opp in store.space_opportunities.values()
        if opp.booking_id == booking_id
    ]


def approve_space_opportunity_listing(store: Store, opportunity_id: str, actor_id: str) -> SpaceOpportunity:
    opp = store.space_opportunities.get(opportunity_id)
    if not opp:
        raise ValueError(f"SpaceOpportunity {opportunity_id} not found")
    opp.status = SpaceOpportunityStatus.listed
    opp.listed_at = now_utc()
    create_audit_event(
        store,
        ActorRole.importer,
        actor_id,
        "space_opportunity_listed",
        "space_opportunity",
        opp.id,
        f"Owner approved listing {opp.recoverable_cbm} CBM of spare FCL space.",
        {"opportunity_id": opp.id, "recoverable_cbm": opp.recoverable_cbm},
    )
    return opp


def landed_cost_summary(store: Store, booking_id: str) -> Dict[str, Any]:
    """
    Aggregate every known cost line for a booking into one landed-cost summary.
    Costs from supplier (purchase orders / supplier pay), Ship Hoppa freight
    (Invoice), customs (CustomsProfile), and delivery (DeliveryPlan).
    Returns lines + totals plus paid-vs-estimate split.
    """
    booking = store.bookings.get(booking_id)
    if not booking:
        raise KeyError(f"Booking {booking_id} not found")

    lines: List[Dict[str, Any]] = []

    # Supplier goods value (purchase orders)
    purchase_orders = [
        po for po in store.purchase_orders.values() if po.booking_id == booking_id
    ]
    goods_value = sum(po.goods_value for po in purchase_orders)
    if goods_value:
        lines.append({
            "category": "supplier_goods",
            "label": "Supplier goods value",
            "amount_usd": round_money(goods_value),
            "status": "estimate",
        })

    # Supplier pay (FX cost on top of goods value)
    sp_requests = [
        sp for sp in store.supplier_pay_requests.values() if sp.booking_id == booking_id
    ]
    fx_fees = 0.0
    for sp in sp_requests:
        if sp.selected_quote_id:
            quote = store.supplier_pay_quotes.get(sp.selected_quote_id)
            if quote:
                fx_fees += quote.provider_fee
    if fx_fees:
        lines.append({
            "category": "supplier_pay_fx",
            "label": "Supplier payment FX/fees",
            "amount_usd": round_money(fx_fees),
            "status": "estimate" if any(sp.marked_paid_at is None for sp in sp_requests) else "actual",
        })

    # Ship Hoppa freight invoice
    invoice = next(
        (inv for inv in store.invoices.values() if inv.booking_id == booking_id),
        None,
    )
    if invoice and invoice.total_usd:
        lines.append({
            "category": "freight",
            "label": "Ship Hoppa freight",
            "amount_usd": round_money(invoice.total_usd),
            "status": "actual" if invoice.status == PaymentStatus.paid else "estimate",
        })

    # Customs charges
    customs = next(
        (cp for cp in store.customs_profiles.values() if cp.booking_id == booking_id),
        None,
    )
    if customs:
        if customs.duty_estimate_usd:
            lines.append({
                "category": "duty",
                "label": "Import duty",
                "amount_usd": round_money(customs.duty_estimate_usd),
                "status": "actual" if customs.customs_status == CustomsStatus.cleared else "estimate",
            })
        if customs.gst_estimate_usd:
            lines.append({
                "category": "gst",
                "label": "GST",
                "amount_usd": round_money(customs.gst_estimate_usd),
                "status": "actual" if customs.customs_status == CustomsStatus.cleared else "estimate",
            })
        if customs.brokerage_fee_usd:
            lines.append({
                "category": "brokerage",
                "label": "Customs brokerage",
                "amount_usd": round_money(customs.brokerage_fee_usd),
                "status": "estimate",
            })

    # Final delivery
    delivery_plan = next(
        (dp for dp in store.delivery_plans.values() if dp.booking_id == booking_id),
        None,
    )
    if delivery_plan and delivery_plan.trucking_quote_usd:
        lines.append({
            "category": "destination_delivery",
            "label": "Destination delivery",
            "amount_usd": round_money(delivery_plan.trucking_quote_usd),
            "status": "actual" if delivery_plan.delivered_at else "estimate",
        })

    total_estimate = round_money(sum(line["amount_usd"] for line in lines))
    actual_total = round_money(
        sum(line["amount_usd"] for line in lines if line["status"] == "actual")
    )
    estimated_remaining = round_money(
        sum(line["amount_usd"] for line in lines if line["status"] == "estimate")
    )

    return {
        "booking_id": booking_id,
        "lines": lines,
        "total_landed_cost_usd": total_estimate,
        "paid_to_date_usd": actual_total,
        "remaining_estimate_usd": estimated_remaining,
        "currency": "USD",
    }


def release_status_for_booking(store: Store, booking_id: str) -> ReleaseStatusResponse:
    booking = store.bookings[booking_id]
    active_holds = update_release_holds(store, booking)
    booking = update_booking_health(store, booking)
    return ReleaseStatusResponse(
        booking_id=booking_id,
        release_status=booking.release_status,
        can_release=not active_holds,
        holds=sorted(
            [hold for hold in store.release_holds.values() if hold.booking_id == booking_id],
            key=lambda item: item.created_at,
        ),
    )


def delivery_plan_for_booking(store: Store, booking_id: str) -> Optional[DeliveryPlan]:
    return next((plan for plan in store.delivery_plans.values() if plan.booking_id == booking_id), None)


def delivery_status_for_release(store: Store, booking_id: str) -> DeliveryPlanStatus:
    release = release_status_for_booking(store, booking_id)
    return DeliveryPlanStatus.ready_to_book if release.can_release else DeliveryPlanStatus.blocked_by_release


def ensure_delivery_plan(store: Store, booking: Booking) -> DeliveryPlan:
    existing = delivery_plan_for_booking(store, booking.id)
    if existing:
        if existing.status not in {DeliveryPlanStatus.booked, DeliveryPlanStatus.delivered}:
            existing.status = delivery_status_for_release(store, booking.id)
            existing.updated_at = now_utc()
            store.delivery_plans[existing.id] = existing
        return existing

    timestamp = now_utc()
    address_parts = [booking.delivery_city]
    if booking.delivery_postcode:
        address_parts.append(booking.delivery_postcode)
    address_parts.append(booking.delivery_country)
    plan = DeliveryPlan(
        id=store.next_id("DEL"),
        booking_id=booking.id,
        destination_address=", ".join(address_parts),
        destination_contact_name=store.importers.get(booking.importer_id).contact_name
        if booking.importer_id in store.importers
        else "Importer warehouse",
        destination_contact_phone=store.importers.get(booking.importer_id).phone
        if booking.importer_id in store.importers
        else None,
        equipment_required=["forklift"],
        status=delivery_status_for_release(store, booking.id),
        trucking_quote_usd=320,
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.delivery_plans[plan.id] = plan
    return plan


def update_delivery_plan(store: Store, booking_id: str, payload: DeliveryPlanUpdate, actor_id: str) -> DeliveryPlan:
    if booking_id not in store.bookings:
        raise ValueError("Booking not found")
    plan = ensure_delivery_plan(store, store.bookings[booking_id])
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(plan, key, value)
    if plan.status not in {DeliveryPlanStatus.booked, DeliveryPlanStatus.delivered}:
        plan.status = delivery_status_for_release(store, booking_id)
    plan.updated_at = now_utc()
    store.delivery_plans[plan.id] = plan
    create_audit_event(
        store,
        ActorRole.importer,
        actor_id,
        "delivery_plan_updated",
        "delivery_plan",
        plan.id,
        "Destination delivery details updated.",
        metadata={"updated_fields": sorted(updates.keys())},
    )
    return plan


def book_delivery_plan(store: Store, delivery_plan_id: str, actor_id: str) -> DeliveryPlan:
    if delivery_plan_id not in store.delivery_plans:
        raise ValueError("Delivery plan not found")
    plan = store.delivery_plans[delivery_plan_id]
    release = release_status_for_booking(store, plan.booking_id)
    if not release.can_release:
        plan.status = DeliveryPlanStatus.blocked_by_release
        plan.updated_at = now_utc()
        store.delivery_plans[plan.id] = plan
        raise ValueError("Delivery cannot be booked until payment, customs, documents, and release holds are clear.")
    plan.status = DeliveryPlanStatus.booked
    plan.booked_at = now_utc()
    plan.updated_at = plan.booked_at
    store.delivery_plans[plan.id] = plan
    booking = store.bookings[plan.booking_id]
    project = import_project_for_booking(store, booking.id)
    if project:
        upsert_project_step(
            store,
            project,
            "delivery",
            ImportProjectStepStatus.in_progress,
            {"delivery_plan_id": plan.id, "destination_address": plan.destination_address},
            plan.id,
        )
        create_import_project_event(
            store,
            project.id,
            "delivery_booked",
            ProjectActorType.user,
            actor_id,
            event_reference=plan.id,
        )
    create_audit_event(store, ActorRole.importer, actor_id, "delivery_booked", "delivery_plan", plan.id, "Destination delivery booked.")
    return plan


def mark_delivery_delivered(store: Store, delivery_plan_id: str, actor_id: str) -> DeliveryPlan:
    if delivery_plan_id not in store.delivery_plans:
        raise ValueError("Delivery plan not found")
    plan = store.delivery_plans[delivery_plan_id]
    timestamp = now_utc()
    plan.status = DeliveryPlanStatus.delivered
    plan.delivered_at = timestamp
    plan.updated_at = timestamp
    store.delivery_plans[plan.id] = plan

    booking = store.bookings[plan.booking_id]
    booking.status = BookingStatus.delivered
    booking.delivered_at = timestamp
    booking.release_status = ReleaseStatus.released
    store.bookings[booking.id] = booking

    project = import_project_for_booking(store, booking.id)
    if project:
        upsert_project_step(
            store,
            project,
            "delivery",
            ImportProjectStepStatus.complete,
            {"delivery_plan_id": plan.id, "delivered_at": timestamp.isoformat()},
            plan.id,
        )
        project.current_step = "delivery"
        project.next_action = "Delivery complete. Finalise landed cost and archive the import record."
        project.updated_at = timestamp
        store.import_projects[project.id] = project
        create_import_project_event(
            store,
            project.id,
            "delivery_completed",
            ProjectActorType.user,
            actor_id,
            event_reference=plan.id,
        )
    create_audit_event(store, ActorRole.importer, actor_id, "delivery_completed", "delivery_plan", plan.id, "Destination delivery marked complete.")
    return plan


def waive_release_hold(store: Store, hold_id: str, reason: str, actor_id: str) -> ReleaseHold:
    hold = store.release_holds[hold_id]
    hold.status = ReleaseHoldStatus.waived
    hold.waived_by = actor_id
    hold.waiver_reason = reason
    hold.cleared_at = now_utc()
    store.release_holds[hold.id] = hold
    create_audit_event(store, ActorRole.admin, actor_id, "release_hold_waived", "release_hold", hold.id, reason)
    update_booking_health(store, store.bookings[hold.booking_id])
    return hold


def ensure_booking_workspace(store: Store, booking: Booking) -> None:
    ensure_document_requirements(store, booking)
    ensure_customs_profile(store, booking)
    if not events_for_booking(store, booking.id):
        create_shipment_event(
            store,
            booking.id,
            ShipmentEventCreate(
                stage=ShipmentEventStage.booking_submitted,
                label="Booking submitted",
                occurred_at=booking.created_at,
                source_type=SourceType.manual_admin,
                source_name="Ship Hoppa app",
                confidence=SourceConfidence.confirmed,
            ),
        )
    update_release_holds(store, booking)
    update_booking_health(store, booking)


def create_supplier_link(store: Store, booking_id: str) -> SupplierAccessLink:
    for link in store.supplier_links.values():
        if link.booking_id == booking_id and link.active:
            return link
    link = SupplierAccessLink(
        id=store.next_id("SUP"),
        booking_id=booking_id,
        token=secrets.token_urlsafe(24),
        expires_at=now_utc() + timedelta(days=45),
        created_at=now_utc(),
    )
    store.supplier_links[link.id] = link
    create_audit_event(store, ActorRole.admin, "ops", "supplier_link_created", "booking", booking_id, f"Supplier link created for {booking_id}.")
    return link


def supplier_instructions_for_booking(store: Store, booking: Booking) -> str:
    warehouse = store.warehouse_for_lane(booking.lane_id or "")
    if booking.delivery_mode.value == "ship_hoppa_pickup":
        return (
            f"Confirm cargo readiness by {booking.latest_supplier_ready_date}. "
            f"Keep goods packed for export and accessible at {booking.pickup_address or booking.supplier_city}. "
            f"Mark every package with booking {booking.id}."
        )
    return (
        f"Deliver cargo to {warehouse.name if warehouse else 'Ship Hoppa warehouse'} by {booking.warehouse_receipt_cutoff}. "
        f"Mark every package with booking {booking.id}."
    )


def supplier_portal(store: Store, token: str) -> SupplierPortalResponse:
    link = supplier_link_by_token(store, token)
    link.last_used_at = now_utc()
    store.supplier_links[link.id] = link
    booking = store.bookings[link.booking_id]
    ensure_booking_workspace(store, booking)
    summary = SupplierBookingSummary(
        id=booking.id,
        supplier_name=booking.supplier_name,
        supplier_city=booking.supplier_city,
        cargo_description=booking.cargo_description,
        cargo_category=booking.cargo_category,
        cbm_estimate=booking.cbm_estimate,
        weight_kg_estimate=booking.weight_kg_estimate,
        cargo_ready_date_latest=booking.cargo_ready_date_latest,
        delivery_mode=booking.delivery_mode,
        pickup_address=booking.pickup_address,
        pickup_contact_name=booking.pickup_contact_name,
        pickup_contact_phone=booking.pickup_contact_phone,
        pickup_window_start=booking.pickup_window_start,
        pickup_window_end=booking.pickup_window_end,
        warehouse_receipt_cutoff=booking.warehouse_receipt_cutoff,
        latest_supplier_ready_date=booking.latest_supplier_ready_date,
        status=booking.status,
    )
    return SupplierPortalResponse(
        booking=summary,
        supplier_instructions=supplier_instructions_for_booking(store, booking),
        checklist=checklist_for_booking(store, booking.id),
        events=events_for_booking(store, booking.id),
    )


def supplier_link_by_token(store: Store, token: str) -> SupplierAccessLink:
    for link in store.supplier_links.values():
        if link.token == token and link.active:
            if link.expires_at and link.expires_at < now_utc():
                raise ValueError("Supplier link has expired")
            return link
    raise ValueError("Supplier link not found")


def supplier_ready(store: Store, token: str, request: SupplierReadyRequest) -> SupplierPortalResponse:
    link = supplier_link_by_token(store, token)
    booking = store.bookings[link.booking_id]
    booking.cargo_ready_date_latest = request.cargo_ready_date_latest
    booking.pickup_address = request.pickup_address or booking.pickup_address
    booking.pickup_contact_name = request.pickup_contact_name or booking.pickup_contact_name
    booking.pickup_contact_phone = request.pickup_contact_phone or booking.pickup_contact_phone
    booking.pickup_window_start = request.pickup_window_start or booking.pickup_window_start
    booking.pickup_window_end = request.pickup_window_end or booking.pickup_window_end
    booking.updated_at = now_utc()
    store.bookings[booking.id] = booking
    create_shipment_event(
        store,
        booking.id,
        ShipmentEventCreate(
            stage=ShipmentEventStage.pickup_scheduled,
            label="Supplier confirmed cargo readiness",
            occurred_at=now_utc(),
            source_type=SourceType.warehouse_event,
            source_name="Supplier portal",
            confidence=SourceConfidence.verified,
            notes=f"Cargo ready by {request.cargo_ready_date_latest}.",
        ),
    )
    create_audit_event(store, ActorRole.system, "supplier-portal", "supplier_ready_confirmed", "booking", booking.id, "Supplier confirmed cargo readiness.")
    return supplier_portal(store, token)


BROKER_ALLOWED_STATUSES = {
    CustomsStatus.submitted,
    CustomsStatus.queried,
    CustomsStatus.cleared,
}


def create_broker_link(store: Store, booking_id: str) -> BrokerAccessLink:
    if booking_id not in store.bookings:
        raise ValueError("Booking not found")
    for link in store.broker_links.values():
        if link.booking_id == booking_id and link.active:
            return link
    link = BrokerAccessLink(
        id=store.next_id("BRK"),
        booking_id=booking_id,
        token=secrets.token_urlsafe(24),
        expires_at=now_utc() + timedelta(days=45),
        created_at=now_utc(),
    )
    store.broker_links[link.id] = link
    create_audit_event(store, ActorRole.admin, "ops", "broker_link_created", "booking", booking_id, f"Broker link created for {booking_id}.")
    return link


def broker_link_by_token(store: Store, token: str) -> BrokerAccessLink:
    for link in store.broker_links.values():
        if link.token == token and link.active:
            if link.expires_at and link.expires_at < now_utc():
                raise ValueError("Broker link has expired")
            return link
    raise ValueError("Broker link not found")


def _broker_portal_response(store: Store, booking: Booking) -> BrokerPortalResponse:
    profile = ensure_customs_profile(store, booking)
    importer = store.importers.get(booking.importer_id)
    company_name = importer.company_name if importer else None
    importer_abn = profile.importer_abn or (importer.abn if importer else None)
    booking_summary = BrokerBookingSummary(
        id=booking.id,
        importer_company_name=company_name,
        importer_abn=importer_abn,
        supplier_country=booking.supplier_country,
        delivery_country=booking.delivery_country,
        delivery_city=booking.delivery_city,
        cargo_description=booking.cargo_description,
        cargo_category=booking.cargo_category,
        cbm_estimate=booking.cbm_estimate,
        weight_kg_estimate=booking.weight_kg_estimate,
        cargo_ready_date_latest=booking.cargo_ready_date_latest,
        status=booking.status,
    )
    customs_summary = BrokerCustomsSummary(
        incoterm=profile.incoterm,
        goods_value_usd=profile.goods_value_usd,
        currency=profile.currency,
        hs_code=profile.hs_code,
        biosecurity_flags=list(profile.biosecurity_flags),
        customs_status=profile.customs_status,
        duty_estimate_usd=profile.duty_estimate_usd,
        gst_estimate_usd=profile.gst_estimate_usd,
        landed_cost_estimate_usd=profile.landed_cost_estimate_usd,
        customs_entry_number=profile.customs_entry_number,
        duty_paid_usd=profile.duty_paid_usd,
        gst_paid_usd=profile.gst_paid_usd,
        broker_notes=profile.broker_notes,
        updated_at=profile.updated_at,
    )
    holds = [
        hold for hold in store.release_holds.values()
        if hold.booking_id == booking.id and hold.status == ReleaseHoldStatus.active
    ]
    return BrokerPortalResponse(
        booking=booking_summary,
        customs=customs_summary,
        holds=holds,
        documents=documents_for_booking(store, booking.id),
        events=events_for_booking(store, booking.id),
    )


def broker_portal(store: Store, token: str) -> BrokerPortalResponse:
    link = broker_link_by_token(store, token)
    link.last_used_at = now_utc()
    store.broker_links[link.id] = link
    booking = store.bookings[link.booking_id]
    return _broker_portal_response(store, booking)


def broker_clearance_update(store: Store, token: str, request: BrokerClearanceUpdate) -> BrokerPortalResponse:
    if request.customs_status not in BROKER_ALLOWED_STATUSES:
        raise ValueError("Broker may only set status to submitted, queried, or cleared")
    link = broker_link_by_token(store, token)
    booking = store.bookings[link.booking_id]
    profile = ensure_customs_profile(store, booking)
    profile.customs_status = request.customs_status
    if request.customs_entry_number is not None:
        profile.customs_entry_number = request.customs_entry_number
    if request.duty_paid_usd is not None:
        profile.duty_paid_usd = request.duty_paid_usd
    if request.gst_paid_usd is not None:
        profile.gst_paid_usd = request.gst_paid_usd
    if request.broker_notes is not None:
        profile.broker_notes = request.broker_notes
    profile.updated_at = now_utc()
    store.customs_profiles[profile.id] = profile
    update_release_holds(store, booking)
    update_booking_health(store, booking)
    if request.customs_status == CustomsStatus.cleared:
        create_shipment_event(
            store,
            booking.id,
            ShipmentEventCreate(
                stage=ShipmentEventStage.customs_cleared,
                label="Customs cleared by broker",
                occurred_at=now_utc(),
                source_type=SourceType.forwarder_confirmation,
                source_name="Broker portal",
                confidence=SourceConfidence.verified,
                notes=request.customs_entry_number and f"Entry {request.customs_entry_number}." or None,
            ),
        )
    create_audit_event(
        store,
        ActorRole.system,
        "broker-portal",
        "broker_clearance_update",
        "booking",
        booking.id,
        f"Broker set customs status to {request.customs_status.value}.",
    )
    link.last_used_at = now_utc()
    store.broker_links[link.id] = link
    return _broker_portal_response(store, booking)


def create_warehouse_link(store: Store, booking_id: str) -> WarehouseAccessLink:
    if booking_id not in store.bookings:
        raise ValueError("Booking not found")
    for link in store.warehouse_links.values():
        if link.booking_id == booking_id and link.active:
            return link
    link = WarehouseAccessLink(
        id=store.next_id("WHL"),
        booking_id=booking_id,
        token=secrets.token_urlsafe(24),
        expires_at=now_utc() + timedelta(days=45),
        created_at=now_utc(),
    )
    store.warehouse_links[link.id] = link
    create_audit_event(store, ActorRole.admin, "ops", "warehouse_link_created", "booking", booking_id, f"Warehouse link created for {booking_id}.")
    return link


def warehouse_link_by_token(store: Store, token: str) -> WarehouseAccessLink:
    for link in store.warehouse_links.values():
        if link.token == token and link.active:
            if link.expires_at and link.expires_at < now_utc():
                raise ValueError("Warehouse link has expired")
            return link
    raise ValueError("Warehouse link not found")


def _warehouse_portal_response(store: Store, booking: Booking) -> WarehousePortalResponse:
    importer = store.importers.get(booking.importer_id)
    warehouse = store.warehouse_for_lane(booking.lane_id or "") if booking.lane_id else None
    summary = WarehouseBookingSummary(
        id=booking.id,
        importer_company_name=importer.company_name if importer else None,
        supplier_country=booking.supplier_country,
        supplier_city=booking.supplier_city,
        cargo_description=booking.cargo_description,
        cargo_category=booking.cargo_category,
        cbm_estimate=booking.cbm_estimate,
        weight_kg_estimate=booking.weight_kg_estimate,
        number_of_packages=booking.number_of_packages,
        cargo_ready_date_latest=booking.cargo_ready_date_latest,
        delivery_mode=booking.delivery_mode,
        warehouse_receipt_cutoff=booking.warehouse_receipt_cutoff,
        warehouse_name=warehouse.name if warehouse else None,
        cbm_actual=booking.cbm_actual,
        weight_kg_actual=booking.weight_kg_actual,
        received_at_warehouse=booking.received_at_warehouse,
        status=booking.status,
    )
    return WarehousePortalResponse(
        booking=summary,
        documents=documents_for_booking(store, booking.id),
        events=events_for_booking(store, booking.id),
    )


def warehouse_portal(store: Store, token: str) -> WarehousePortalResponse:
    link = warehouse_link_by_token(store, token)
    link.last_used_at = now_utc()
    store.warehouse_links[link.id] = link
    booking = store.bookings[link.booking_id]
    return _warehouse_portal_response(store, booking)


def warehouse_receipt_update(store: Store, token: str, request: WarehouseReceiptUpdate) -> WarehousePortalResponse:
    link = warehouse_link_by_token(store, token)
    booking = store.bookings[link.booking_id]
    if booking.delivery_mode == DeliveryMode.ship_hoppa_pickup:
        raise PermissionError("This shipment is on Ship Hoppa pickup. The warehouse portal is not used for it.")
    record_warehouse_measurement(
        store,
        booking.id,
        request.actual_cbm,
        request.actual_weight_kg,
        actor_id="warehouse-portal",
    )
    create_shipment_event(
        store,
        booking.id,
        ShipmentEventCreate(
            stage=ShipmentEventStage.warehouse_received,
            label="Cargo received at warehouse",
            occurred_at=now_utc(),
            source_type=SourceType.warehouse_event,
            source_name="Warehouse portal",
            confidence=SourceConfidence.confirmed,
            notes=request.notes,
        ),
    )
    create_audit_event(
        store,
        ActorRole.system,
        "warehouse-portal",
        "warehouse_receipt_confirmed",
        "booking",
        booking.id,
        f"Warehouse confirmed receipt: {request.actual_cbm:.2f} CBM / {request.actual_weight_kg:.0f} kg.",
    )
    link.last_used_at = now_utc()
    store.warehouse_links[link.id] = link
    booking = store.bookings[booking.id]
    return _warehouse_portal_response(store, booking)


CARRIER_ALLOWED_EVENT_STAGES = frozenset({
    ShipmentEventStage.loaded,
    ShipmentEventStage.departed,
    ShipmentEventStage.arrived,
})


def create_carrier_link(store: Store, booking_id: str) -> CarrierAccessLink:
    if booking_id not in store.bookings:
        raise ValueError("Booking not found")
    for link in store.carrier_links.values():
        if link.booking_id == booking_id and link.active:
            return link
    link = CarrierAccessLink(
        id=store.next_id("CRL"),
        booking_id=booking_id,
        token=secrets.token_urlsafe(24),
        expires_at=now_utc() + timedelta(days=45),
        created_at=now_utc(),
    )
    store.carrier_links[link.id] = link
    create_audit_event(store, ActorRole.admin, "ops", "carrier_link_created", "booking", booking_id, f"Carrier link created for {booking_id}.")
    return link


def carrier_link_by_token(store: Store, token: str) -> CarrierAccessLink:
    for link in store.carrier_links.values():
        if link.token == token and link.active:
            if link.expires_at and link.expires_at < now_utc():
                raise ValueError("Carrier link has expired")
            return link
    raise ValueError("Carrier link not found")


def _carrier_portal_response(store: Store, booking: Booking) -> CarrierPortalResponse:
    importer = store.importers.get(booking.importer_id)
    container = store.containers.get(booking.container_id) if booking.container_id else None
    summary = CarrierBookingSummary(
        id=booking.id,
        importer_company_name=importer.company_name if importer else None,
        container_id=booking.container_id,
        container_number=container.container_number if container else None,
        vessel_name=container.vessel_name if container else None,
        voyage_number=container.voyage_number if container else None,
        carrier_name=container.carrier_name if container else None,
        estimated_departure=container.estimated_departure if container else None,
        estimated_arrival=container.estimated_arrival if container else None,
        baseline_estimated_arrival=container.baseline_estimated_arrival if container else None,
        target_sailing_date=container.target_sailing_date if container else None,
        carrier_cutoff_date=container.carrier_cutoff_date if container else None,
        cargo_description=booking.cargo_description,
        cargo_category=booking.cargo_category,
        cbm_estimate=booking.cbm_estimate,
        weight_kg_estimate=booking.weight_kg_estimate,
        status=booking.status,
    )
    return CarrierPortalResponse(
        booking=summary,
        documents=documents_for_booking(store, booking.id),
        events=events_for_booking(store, booking.id),
    )


def carrier_portal(store: Store, token: str) -> CarrierPortalResponse:
    link = carrier_link_by_token(store, token)
    link.last_used_at = now_utc()
    store.carrier_links[link.id] = link
    booking = store.bookings[link.booking_id]
    return _carrier_portal_response(store, booking)


def carrier_eta_update(store: Store, token: str, request: CarrierEtaUpdate) -> CarrierPortalResponse:
    link = carrier_link_by_token(store, token)
    booking = store.bookings[link.booking_id]
    if booking.status == BookingStatus.delivered:
        raise ValueError("This booking has already been delivered. ETA updates are no longer accepted.")
    if not booking.container_id:
        raise ValueError("This booking is not yet on a container. ETA cannot be updated until a sailing is selected.")
    update_container_eta(
        store,
        booking.container_id,
        request.estimated_arrival,
        actor_id="carrier-portal",
        source="carrier_portal",
    )
    note = request.note.strip() if request.note else ""
    create_audit_event(
        store,
        ActorRole.system,
        "carrier-portal",
        "carrier_eta_update",
        "booking",
        booking.id,
        f"Carrier set ETA to {request.estimated_arrival}." + (f" Note: {note}" if note else ""),
    )
    link.last_used_at = now_utc()
    store.carrier_links[link.id] = link
    return _carrier_portal_response(store, booking)


def carrier_event_update(store: Store, token: str, request: CarrierEventUpdate) -> CarrierPortalResponse:
    if request.stage not in CARRIER_ALLOWED_EVENT_STAGES:
        raise ValueError("Carrier may only submit loaded, departed, or arrived events.")
    link = carrier_link_by_token(store, token)
    booking = store.bookings[link.booking_id]
    create_shipment_event(
        store,
        booking.id,
        ShipmentEventCreate(
            stage=request.stage,
            label=request.label or request.stage.value.replace("_", " ").title(),
            occurred_at=now_utc(),
            source_type=SourceType.forwarder_confirmation,
            source_name="Carrier portal",
            confidence=SourceConfidence.confirmed,
            notes=request.notes,
        ),
    )
    create_audit_event(
        store,
        ActorRole.system,
        "carrier-portal",
        "carrier_event_update",
        "booking",
        booking.id,
        f"Carrier reported {request.stage.value}.",
    )
    link.last_used_at = now_utc()
    store.carrier_links[link.id] = link
    return _carrier_portal_response(store, booking)


def sailing_search(store: Store) -> List[SailingSearchResult]:
    results: List[SailingSearchResult] = []
    for option in store.sailing_options.values():
        if not option.active:
            continue
        warehouse_cutoff = option.carrier_gate_in_cutoff_date - timedelta(days=2)
        if warehouse_cutoff < date.today():
            continue
        lane = store.lanes[option.lane_id]
        matching_container = next(
            (
                container
                for container in store.containers.values()
                if container.lane_id == option.lane_id
                and container.target_sailing_date == option.etd
                and container.status.value in {"open", "filling"}
            ),
            None,
        )
        available_cbm = matching_container.remaining_cbm if matching_container else lane.practical_cbm_limit
        available_weight = matching_container.remaining_weight_kg if matching_container else lane.road_weight_limit_kg
        results.append(
            SailingSearchResult(
                sailing_option_id=option.id,
                container_id=matching_container.id if matching_container else None,
                lane_id=option.lane_id,
                carrier_name=option.carrier_name,
                service_name=option.service_name,
                departure_port=option.departure_port,
                arrival_port=option.arrival_port,
                etd=option.etd,
                eta=option.eta,
                transit_days=option.transit_days,
                warehouse_receipt_cutoff_date=warehouse_cutoff,
                carrier_gate_in_cutoff_date=option.carrier_gate_in_cutoff_date,
                available_cbm=round(available_cbm, 2),
                available_weight_kg=round(available_weight, 2),
                source_confidence=option.confidence,
                source_name=option.source_name,
                total_all_in_usd=option.total_all_in_usd,
                route_waypoints=matching_container.route_waypoints if matching_container and matching_container.route_waypoints else option.route_waypoints,
                route_geometry_source_type=(
                    matching_container.route_geometry_source_type
                    if matching_container and matching_container.route_waypoints
                    else option.route_geometry_source_type
                ),
                route_geometry_source_name=(
                    matching_container.route_geometry_source_name
                    if matching_container and matching_container.route_waypoints
                    else option.route_geometry_source_name
                ),
                route_geometry_confidence=(
                    matching_container.route_geometry_confidence
                    if matching_container and matching_container.route_waypoints
                    else option.route_geometry_confidence
                ),
            )
        )
    return sorted(results, key=lambda item: item.etd)
