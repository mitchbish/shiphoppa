"""
Ship Hoppa Automation Engine

Implements the shipment state machine, fact extraction from source messages,
missing-data detection, and automated partner chase logic.

This is Step 5 of the build plan: "Intake and extraction, missing-data prompts,
approval cards, sentinel checks, and admin exception queues."
"""

import re
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .models import (
    ActorRole,
    AdminTaskStatus,
    ApprovalRequestType,
    AutomationDecision,
    AutomationType,
    Booking,
    BookingStatus,
    ChecklistStatus,
    CustomsStatus,
    DeliveryPlanStatus,
    DocumentStatus,
    DocumentType,
    ExtractionStatus,
    OutboundChannel,
    OutboundRecipientType,
    PaymentStatus,
    ProductionMilestoneStatus,
    PurchaseOrderStatus,
    ReleaseHoldType,
    ReleaseStatus,
    ShipmentEventStage,
    SourceConfidence,
    SourceMessage,
    SourceMessageCreate,
)
from .store import Store


class ShipmentLifecycleState(str, Enum):
    draft_order = "draft_order"
    order_confirmed = "order_confirmed"
    deposit_due = "deposit_due"
    deposit_paid = "deposit_paid"
    production_in_progress = "production_in_progress"
    qc_required = "qc_required"
    qc_passed = "qc_passed"
    packing_required = "packing_required"
    cargo_ready = "cargo_ready"
    pickup_scheduled = "pickup_scheduled"
    picked_up = "picked_up"
    warehouse_received = "warehouse_received"
    measured_and_checked = "measured_and_checked"
    shipping_plan_ready = "shipping_plan_ready"
    container_booked = "container_booked"
    export_docs_required = "export_docs_required"
    waiting_sailing = "waiting_sailing"
    departed_origin = "departed_origin"
    in_transit = "in_transit"
    arrived_port = "arrived_port"
    customs_pending = "customs_pending"
    destination_charges_due = "destination_charges_due"
    release_blocked = "release_blocked"
    released = "released"
    delivery_scheduled = "delivery_scheduled"
    delivered = "delivered"
    landed_cost_finalised = "landed_cost_finalised"
    closed = "closed"


class AutomationAction(str, Enum):
    auto_accept = "auto_accept"
    ask_customer = "ask_customer"
    admin_review = "admin_review"


class ExtractedFact(BaseModel):
    field: str
    value: str
    confidence: SourceConfidence = SourceConfidence.estimated
    source_snippet: str = ""


class MissingDataItem(BaseModel):
    field: str
    label: str
    responsible_party: OutboundRecipientType
    urgency: str = "normal"
    chase_channel: OutboundChannel = OutboundChannel.email


class AutomationResult(BaseModel):
    lifecycle_state: ShipmentLifecycleState
    next_action_label: str
    missing_data: List[MissingDataItem] = Field(default_factory=list)
    extracted_facts: List[ExtractedFact] = Field(default_factory=list)
    chase_messages_queued: int = 0
    state_advanced: bool = False
    approvals_created: int = 0
    admin_tasks_created: int = 0


# --- Shipment lifecycle state derivation ---

def derive_lifecycle_state(store: Store, booking: Booking) -> ShipmentLifecycleState:
    if booking.status == BookingStatus.delivered:
        delivery_plan = next(
            (dp for dp in store.delivery_plans.values() if dp.booking_id == booking.id),
            None,
        )
        if delivery_plan and delivery_plan.delivered_at:
            return ShipmentLifecycleState.landed_cost_finalised
        return ShipmentLifecycleState.delivered

    if booking.status == BookingStatus.arrived:
        customs_profile = next(
            (cp for cp in store.customs_profiles.values() if cp.booking_id == booking.id),
            None,
        )
        if customs_profile and customs_profile.customs_status == CustomsStatus.cleared:
            if booking.release_status == ReleaseStatus.released:
                delivery_plan = next(
                    (dp for dp in store.delivery_plans.values() if dp.booking_id == booking.id),
                    None,
                )
                if delivery_plan and delivery_plan.status == DeliveryPlanStatus.booked:
                    return ShipmentLifecycleState.delivery_scheduled
                return ShipmentLifecycleState.released
            return ShipmentLifecycleState.release_blocked
        if booking.payment_status in (PaymentStatus.issued, PaymentStatus.overdue):
            return ShipmentLifecycleState.destination_charges_due
        return ShipmentLifecycleState.customs_pending

    if booking.status == BookingStatus.shipped:
        events = [e for e in store.shipment_events.values() if e.booking_id == booking.id]
        if any(e.stage == ShipmentEventStage.arrived for e in events):
            return ShipmentLifecycleState.arrived_port
        if any(e.stage == ShipmentEventStage.transshipped for e in events):
            return ShipmentLifecycleState.in_transit
        return ShipmentLifecycleState.departed_origin

    if booking.status == BookingStatus.loaded:
        return ShipmentLifecycleState.waiting_sailing

    if booking.status == BookingStatus.at_warehouse:
        if booking.cbm_actual:
            return ShipmentLifecycleState.measured_and_checked
        return ShipmentLifecycleState.warehouse_received

    if booking.status == BookingStatus.confirmed:
        if booking.container_id:
            return ShipmentLifecycleState.container_booked
        return ShipmentLifecycleState.shipping_plan_ready

    if booking.status == BookingStatus.matched:
        purchase_orders = [
            po for po in store.purchase_orders.values()
            if po.booking_id == booking.id
        ]
        if purchase_orders:
            po = purchase_orders[0]
            if po.status == PurchaseOrderStatus.ready_to_ship:
                return ShipmentLifecycleState.cargo_ready
            if po.status in (PurchaseOrderStatus.ready_for_qc, PurchaseOrderStatus.qc_in_progress):
                return ShipmentLifecycleState.qc_required
            if po.status == PurchaseOrderStatus.in_production:
                return ShipmentLifecycleState.production_in_progress
            if po.status == PurchaseOrderStatus.deposit_paid:
                return ShipmentLifecycleState.deposit_paid
            if po.status == PurchaseOrderStatus.deposit_due:
                return ShipmentLifecycleState.deposit_due
            if po.status == PurchaseOrderStatus.order_confirmed:
                return ShipmentLifecycleState.order_confirmed
        if booking.pickup_address:
            return ShipmentLifecycleState.cargo_ready
        return ShipmentLifecycleState.order_confirmed

    if booking.status == BookingStatus.submitted:
        return ShipmentLifecycleState.order_confirmed

    return ShipmentLifecycleState.draft_order


# --- Next-action labels per state ---

NEXT_ACTION_LABELS: Dict[ShipmentLifecycleState, str] = {
    ShipmentLifecycleState.draft_order: "Find the best shipping option for this import.",
    ShipmentLifecycleState.order_confirmed: "Confirm deposit payment or mark order active.",
    ShipmentLifecycleState.deposit_due: "Pay supplier deposit or mark as paid outside app.",
    ShipmentLifecycleState.deposit_paid: "Wait for production to begin.",
    ShipmentLifecycleState.production_in_progress: "Monitor production milestones.",
    ShipmentLifecycleState.qc_required: "Book or complete quality inspection.",
    ShipmentLifecycleState.qc_passed: "Confirm packing details and ready date.",
    ShipmentLifecycleState.packing_required: "Upload packing list and confirm dimensions.",
    ShipmentLifecycleState.cargo_ready: "Schedule pickup or confirm self-delivery.",
    ShipmentLifecycleState.pickup_scheduled: "Goods in transit to warehouse.",
    ShipmentLifecycleState.picked_up: "Awaiting warehouse receipt confirmation.",
    ShipmentLifecycleState.warehouse_received: "Measure and check cargo at warehouse.",
    ShipmentLifecycleState.measured_and_checked: "Confirm shipping plan and container.",
    ShipmentLifecycleState.shipping_plan_ready: "Book container or shared space.",
    ShipmentLifecycleState.container_booked: "Prepare export documents.",
    ShipmentLifecycleState.export_docs_required: "Upload shipping instructions, BL, fumigation.",
    ShipmentLifecycleState.waiting_sailing: "Goods loaded, waiting for vessel departure.",
    ShipmentLifecycleState.departed_origin: "In transit to destination port.",
    ShipmentLifecycleState.in_transit: "Monitor vessel progress and ETA.",
    ShipmentLifecycleState.arrived_port: "Prepare customs entry and broker handoff.",
    ShipmentLifecycleState.customs_pending: "Waiting for customs clearance.",
    ShipmentLifecycleState.destination_charges_due: "Pay destination charges.",
    ShipmentLifecycleState.release_blocked: "Clear release holds before delivery.",
    ShipmentLifecycleState.released: "Book delivery to final destination.",
    ShipmentLifecycleState.delivery_scheduled: "Awaiting delivery completion.",
    ShipmentLifecycleState.delivered: "Confirm delivery and reconcile landed cost.",
    ShipmentLifecycleState.landed_cost_finalised: "Import complete.",
    ShipmentLifecycleState.closed: "Archived.",
}


def next_action_for_state(state: ShipmentLifecycleState) -> str:
    return NEXT_ACTION_LABELS.get(state, "Review shipment status.")


# --- Fact extraction from source messages ---

BOOKING_ID_PATTERN = re.compile(r"\b(BK-\d{4})\b", re.IGNORECASE)
CONTAINER_PATTERN = re.compile(r"\b([A-Z]{4}\d{7})\b")
DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
CBM_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:cbm|m3|cubic\s*met)", re.IGNORECASE)
WEIGHT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilos)", re.IGNORECASE)
VESSEL_PATTERN = re.compile(r"(?:vessel|ship|mv|m\.v\.)\s*[:=]?\s*([A-Z][A-Za-z\s]{3,30})", re.IGNORECASE)
VOYAGE_PATTERN = re.compile(r"(?:voyage|voy)\s*[:=]?\s*([A-Z0-9\-]{3,20})", re.IGNORECASE)
ETA_PATTERN = re.compile(r"(?:eta|arrival|arrive)\s*[:=]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})", re.IGNORECASE)
ETD_PATTERN = re.compile(r"(?:etd|departure|depart|sailing)\s*[:=]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})", re.IGNORECASE)
READY_DATE_PATTERN = re.compile(r"(?:ready|cargo ready|goods ready)\s*(?:date)?\s*[:=]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})", re.IGNORECASE)
INVOICE_AMOUNT_PATTERN = re.compile(r"(?:total|amount|invoice)\s*[:=]?\s*(?:USD|US\$|\$)\s*([\d,]+\.?\d*)", re.IGNORECASE)
PO_NUMBER_PATTERN = re.compile(r"(?:po|purchase order|order)\s*(?:#|no\.?|number)?\s*[:=]?\s*([A-Z0-9\-]{3,20})", re.IGNORECASE)


def extract_facts_from_text(text: str) -> List[ExtractedFact]:
    facts: List[ExtractedFact] = []
    if not text:
        return facts

    for match in BOOKING_ID_PATTERN.finditer(text):
        facts.append(ExtractedFact(
            field="booking_id",
            value=match.group(1).upper(),
            confidence=SourceConfidence.verified,
            source_snippet=text[max(0, match.start() - 20):match.end() + 20],
        ))

    for match in CONTAINER_PATTERN.finditer(text):
        facts.append(ExtractedFact(
            field="container_number",
            value=match.group(1),
            confidence=SourceConfidence.verified,
            source_snippet=text[max(0, match.start() - 20):match.end() + 20],
        ))

    for match in CBM_PATTERN.finditer(text):
        facts.append(ExtractedFact(
            field="cbm",
            value=match.group(1),
            confidence=SourceConfidence.estimated,
            source_snippet=text[max(0, match.start() - 20):match.end() + 20],
        ))

    for match in WEIGHT_PATTERN.finditer(text):
        facts.append(ExtractedFact(
            field="weight_kg",
            value=match.group(1),
            confidence=SourceConfidence.estimated,
            source_snippet=text[max(0, match.start() - 20):match.end() + 20],
        ))

    for match in VESSEL_PATTERN.finditer(text):
        facts.append(ExtractedFact(
            field="vessel_name",
            value=match.group(1).strip(),
            confidence=SourceConfidence.estimated,
            source_snippet=text[max(0, match.start() - 20):match.end() + 20],
        ))

    for match in VOYAGE_PATTERN.finditer(text):
        facts.append(ExtractedFact(
            field="voyage_number",
            value=match.group(1).strip(),
            confidence=SourceConfidence.estimated,
            source_snippet=text[max(0, match.start() - 20):match.end() + 20],
        ))

    for match in ETA_PATTERN.finditer(text):
        facts.append(ExtractedFact(
            field="eta",
            value=match.group(1),
            confidence=SourceConfidence.estimated,
            source_snippet=text[max(0, match.start() - 20):match.end() + 20],
        ))

    for match in ETD_PATTERN.finditer(text):
        facts.append(ExtractedFact(
            field="etd",
            value=match.group(1),
            confidence=SourceConfidence.estimated,
            source_snippet=text[max(0, match.start() - 20):match.end() + 20],
        ))

    for match in READY_DATE_PATTERN.finditer(text):
        facts.append(ExtractedFact(
            field="cargo_ready_date",
            value=match.group(1),
            confidence=SourceConfidence.estimated,
            source_snippet=text[max(0, match.start() - 20):match.end() + 20],
        ))

    for match in INVOICE_AMOUNT_PATTERN.finditer(text):
        facts.append(ExtractedFact(
            field="invoice_amount_usd",
            value=match.group(1).replace(",", ""),
            confidence=SourceConfidence.estimated,
            source_snippet=text[max(0, match.start() - 20):match.end() + 20],
        ))

    for match in PO_NUMBER_PATTERN.finditer(text):
        facts.append(ExtractedFact(
            field="po_number",
            value=match.group(1),
            confidence=SourceConfidence.estimated,
            source_snippet=text[max(0, match.start() - 20):match.end() + 20],
        ))

    return facts


# --- Missing data detection ---

def detect_missing_data(store: Store, booking: Booking) -> List[MissingDataItem]:
    missing: List[MissingDataItem] = []
    state = derive_lifecycle_state(store, booking)

    if not booking.supplier_name:
        missing.append(MissingDataItem(
            field="supplier_name",
            label="Supplier name",
            responsible_party=OutboundRecipientType.importer,
        ))

    if not booking.pickup_address and state.value >= ShipmentLifecycleState.cargo_ready.value:
        missing.append(MissingDataItem(
            field="pickup_address",
            label="Pickup address for factory collection",
            responsible_party=OutboundRecipientType.supplier,
            urgency="high" if state == ShipmentLifecycleState.cargo_ready else "normal",
        ))

    if not booking.pickup_contact_phone and booking.pickup_address:
        missing.append(MissingDataItem(
            field="pickup_contact_phone",
            label="Pickup contact phone number",
            responsible_party=OutboundRecipientType.supplier,
        ))

    documents = [d for d in store.shipment_documents.values() if d.booking_id == booking.id]
    doc_types_uploaded = {d.document_type for d in documents}

    if state.value >= ShipmentLifecycleState.cargo_ready.value:
        if DocumentType.packing_list not in doc_types_uploaded:
            missing.append(MissingDataItem(
                field="packing_list",
                label="Packing list",
                responsible_party=OutboundRecipientType.supplier,
                urgency="high",
            ))
        if DocumentType.commercial_invoice not in doc_types_uploaded:
            missing.append(MissingDataItem(
                field="commercial_invoice",
                label="Commercial invoice",
                responsible_party=OutboundRecipientType.supplier,
                urgency="high",
            ))

    if state.value >= ShipmentLifecycleState.container_booked.value:
        if DocumentType.shipping_instructions not in doc_types_uploaded:
            missing.append(MissingDataItem(
                field="shipping_instructions",
                label="Shipping instructions",
                responsible_party=OutboundRecipientType.forwarder,
            ))
        if DocumentType.fumigation_ispm not in doc_types_uploaded:
            missing.append(MissingDataItem(
                field="fumigation_certificate",
                label="ISPM-15 fumigation certificate",
                responsible_party=OutboundRecipientType.warehouse,
            ))

    if state.value >= ShipmentLifecycleState.departed_origin.value:
        if DocumentType.house_bill not in doc_types_uploaded:
            missing.append(MissingDataItem(
                field="house_bill",
                label="House bill of lading",
                responsible_party=OutboundRecipientType.forwarder,
            ))

    if state.value >= ShipmentLifecycleState.arrived_port.value:
        if DocumentType.arrival_notice not in doc_types_uploaded:
            missing.append(MissingDataItem(
                field="arrival_notice",
                label="Arrival notice",
                responsible_party=OutboundRecipientType.forwarder,
            ))
        if DocumentType.delivery_order not in doc_types_uploaded:
            missing.append(MissingDataItem(
                field="delivery_order",
                label="Delivery order",
                responsible_party=OutboundRecipientType.forwarder,
            ))

    customs_profile = next(
        (cp for cp in store.customs_profiles.values() if cp.booking_id == booking.id),
        None,
    )
    if state.value >= ShipmentLifecycleState.customs_pending.value and customs_profile:
        if not customs_profile.hs_code:
            missing.append(MissingDataItem(
                field="hs_code",
                label="HS code for customs classification",
                responsible_party=OutboundRecipientType.broker,
            ))

    delivery_plan = next(
        (dp for dp in store.delivery_plans.values() if dp.booking_id == booking.id),
        None,
    )
    if state == ShipmentLifecycleState.released and delivery_plan:
        if not delivery_plan.delivery_window_start:
            missing.append(MissingDataItem(
                field="delivery_window",
                label="Delivery window dates",
                responsible_party=OutboundRecipientType.importer,
            ))

    return missing


# --- Chase message generation ---

CHASE_TEMPLATES: Dict[str, Dict[str, str]] = {
    "pickup_address": {
        "subject": "Pickup address needed for shipment {booking_id}",
        "body": "We need the factory pickup address and contact details to arrange collection for shipment {booking_id}. Please provide the full address, contact name, and phone number.",
    },
    "pickup_contact_phone": {
        "subject": "Pickup contact phone needed for {booking_id}",
        "body": "We have the pickup address for {booking_id} but need a contact phone number for the driver on collection day.",
    },
    "packing_list": {
        "subject": "Packing list required for shipment {booking_id}",
        "body": "Please upload or send the packing list for shipment {booking_id}. We need carton count, dimensions, and weights to confirm the shipping plan.",
    },
    "commercial_invoice": {
        "subject": "Commercial invoice required for shipment {booking_id}",
        "body": "Please provide the commercial invoice for shipment {booking_id}. This is needed for customs clearance at the destination.",
    },
    "shipping_instructions": {
        "subject": "Shipping instructions needed for {booking_id}",
        "body": "Please provide shipping instructions for shipment {booking_id} before the carrier cutoff date.",
    },
    "fumigation_certificate": {
        "subject": "ISPM-15 fumigation certificate needed for {booking_id}",
        "body": "Shipment {booking_id} requires a fumigation certificate (ISPM-15 compliant) before loading. Please arrange treatment and provide the certificate.",
    },
    "house_bill": {
        "subject": "House BL needed for {booking_id}",
        "body": "Please provide the house bill of lading for shipment {booking_id}.",
    },
    "arrival_notice": {
        "subject": "Arrival notice needed for {booking_id}",
        "body": "Shipment {booking_id} has arrived. Please provide the arrival notice so we can proceed with customs and delivery.",
    },
    "delivery_order": {
        "subject": "Delivery order needed for {booking_id}",
        "body": "Please provide the delivery order for shipment {booking_id} so we can arrange final delivery.",
    },
    "hs_code": {
        "subject": "HS classification needed for {booking_id}",
        "body": "Please provide the HS code classification for shipment {booking_id}. Goods description: {cargo_description}.",
    },
    "delivery_window": {
        "subject": "Delivery window needed for {booking_id}",
        "body": "Shipment {booking_id} is released and ready for delivery. Please confirm your preferred delivery dates and any equipment requirements.",
    },
}


def generate_chase_subject_body(
    field: str, booking: Booking
) -> Tuple[str, str]:
    template = CHASE_TEMPLATES.get(field)
    if not template:
        return (
            f"Information needed for shipment {booking.id}",
            f"We need additional information for shipment {booking.id}. Please respond with the required details.",
        )
    context = {
        "booking_id": booking.id,
        "cargo_description": booking.cargo_description or booking.cargo_category.value,
    }
    return (
        template["subject"].format(**context),
        template["body"].format(**context),
    )


# --- Automation decision ladder ---

def automation_decision_for_fact(fact: ExtractedFact) -> AutomationAction:
    high_confidence_auto_accept = {"booking_id", "container_number"}
    if fact.field in high_confidence_auto_accept and fact.confidence == SourceConfidence.verified:
        return AutomationAction.auto_accept

    low_risk_fields = {"vessel_name", "voyage_number", "eta", "etd", "cbm", "weight_kg", "cargo_ready_date"}
    if fact.field in low_risk_fields and fact.confidence in (SourceConfidence.verified, SourceConfidence.estimated):
        return AutomationAction.auto_accept

    money_fields = {"invoice_amount_usd"}
    if fact.field in money_fields:
        return AutomationAction.ask_customer

    return AutomationAction.admin_review


# --- Main automation cycle ---

def run_automation_for_booking(store: Store, booking: Booking) -> AutomationResult:
    from .operations import (
        create_audit_event,
        create_automation_run,
        queue_outbound_message,
        OutboundMessageCreate,
    )

    state = derive_lifecycle_state(store, booking)
    next_action = next_action_for_state(state)
    missing = detect_missing_data(store, booking)

    chase_count = 0
    for item in missing:
        if item.urgency == "high":
            existing_chases = [
                msg for msg in store.outbound_messages.values()
                if msg.recipient_type == item.responsible_party
                and booking.id in (msg.subject or "")
                and item.field in (msg.body_snapshot or "")
            ]
            if not existing_chases:
                subject, body = generate_chase_subject_body(item.field, booking)
                chase_request = OutboundMessageCreate(
                    recipient_type=item.responsible_party,
                    recipient_id=booking.supplier_name or "unknown",
                    channel=item.chase_channel,
                    template_key=f"chase_{item.field}",
                    body_snapshot=body,
                    subject=subject,
                    compliance_basis="automated_shipment_chase",
                    related_shipment_id=booking.id,
                )
                queue_outbound_message(
                    store,
                    chase_request,
                    ActorRole.system,
                    "automation_engine",
                )
                chase_count += 1

    create_automation_run(
        store,
        AutomationType.chase_partner,
        booking.id,
        AutomationDecision.auto_accepted if chase_count else AutomationDecision.admin_review_required,
        f"State: {state.value}. Missing items: {len(missing)}. Chase messages queued: {chase_count}.",
        confidence=SourceConfidence.estimated,
    )

    return AutomationResult(
        lifecycle_state=state,
        next_action_label=next_action,
        missing_data=missing,
        chase_messages_queued=chase_count,
    )


def run_extraction_for_message(store: Store, message: SourceMessage) -> List[ExtractedFact]:
    from .operations import create_automation_run

    text = f"{message.subject or ''}\n{message.body or ''}"
    facts = extract_facts_from_text(text)

    if facts:
        message.extraction_status = ExtractionStatus.matched
    else:
        message.extraction_status = ExtractionStatus.needs_review

    create_automation_run(
        store,
        AutomationType.extract_document,
        message.id,
        AutomationDecision.auto_accepted if facts else AutomationDecision.admin_review_required,
        f"Extracted {len(facts)} facts from source message." if facts else "No structured facts could be extracted.",
        confidence=SourceConfidence.estimated if facts else SourceConfidence.estimated,
    )

    return facts


def apply_extracted_facts(
    store: Store, booking: Booking, facts: List[ExtractedFact]
) -> Tuple[List[ExtractedFact], List[ExtractedFact]]:
    from .operations import create_approval_request, create_audit_event

    applied: List[ExtractedFact] = []
    needs_review: List[ExtractedFact] = []

    for fact in facts:
        action = automation_decision_for_fact(fact)

        if action == AutomationAction.auto_accept:
            if fact.field == "cbm" and not booking.cbm_actual:
                booking.cbm_actual = float(fact.value)
                applied.append(fact)
            elif fact.field == "weight_kg" and not booking.weight_kg_actual:
                booking.weight_kg_actual = float(fact.value)
                applied.append(fact)
            elif fact.field == "vessel_name" and booking.container_id:
                container = store.containers.get(booking.container_id)
                if container and not container.vessel_name:
                    container.vessel_name = fact.value
                    applied.append(fact)
            elif fact.field == "voyage_number" and booking.container_id:
                container = store.containers.get(booking.container_id)
                if container and not container.voyage_number:
                    container.voyage_number = fact.value
                    applied.append(fact)
            elif fact.field == "container_number" and booking.container_id:
                container = store.containers.get(booking.container_id)
                if container and not container.container_number:
                    container.container_number = fact.value
                    applied.append(fact)
            else:
                needs_review.append(fact)
        elif action == AutomationAction.ask_customer:
            approval = create_approval_request(
                store,
                request_type=ApprovalRequestType.approve_invoice_variance,
                title=f"Confirm {fact.field.replace('_', ' ')} for {booking.id}",
                summary=f"The system extracted '{fact.value}' from a source message. Please confirm this is correct.",
                amount_usd=float(fact.value) if fact.field == "invoice_amount_usd" else None,
                related_booking_id=booking.id,
                source_reference=fact.source_snippet,
            )
            needs_review.append(fact)
        else:
            needs_review.append(fact)

    if applied:
        create_audit_event(
            store,
            ActorRole.system,
            "automation_engine",
            "facts_auto_applied",
            "booking",
            booking.id,
            f"Auto-applied {len(applied)} extracted facts to shipment.",
            {"fields": [f.field for f in applied]},
        )

    return applied, needs_review


def try_advance_booking_status(store: Store, booking: Booking) -> bool:
    """
    Attempt to automatically advance a booking's status based on current data.
    Returns True if the status was advanced.
    """
    from .operations import create_audit_event, create_shipment_event, ShipmentEventCreate

    advanced = False
    state = derive_lifecycle_state(store, booking)

    if booking.status == BookingStatus.confirmed and state == ShipmentLifecycleState.container_booked:
        events = [e for e in store.shipment_events.values() if e.booking_id == booking.id]
        has_warehouse_event = any(e.stage == ShipmentEventStage.warehouse_received for e in events)
        if has_warehouse_event and not booking.received_at_warehouse:
            booking.status = BookingStatus.at_warehouse
            booking.received_at_warehouse = datetime.utcnow()
            advanced = True

    if booking.status == BookingStatus.at_warehouse:
        if booking.cbm_actual and booking.weight_kg_actual:
            events = [e for e in store.shipment_events.values() if e.booking_id == booking.id]
            has_loaded = any(e.stage == ShipmentEventStage.loaded for e in events)
            if has_loaded and not booking.loaded_at:
                booking.status = BookingStatus.loaded
                booking.loaded_at = datetime.utcnow()
                advanced = True

    if booking.status == BookingStatus.loaded:
        events = [e for e in store.shipment_events.values() if e.booking_id == booking.id]
        has_departed = any(e.stage == ShipmentEventStage.departed for e in events)
        if has_departed and not booking.shipped_at:
            booking.status = BookingStatus.shipped
            booking.shipped_at = datetime.utcnow()
            advanced = True

    if booking.status == BookingStatus.shipped:
        events = [e for e in store.shipment_events.values() if e.booking_id == booking.id]
        has_arrived = any(e.stage == ShipmentEventStage.arrived for e in events)
        if has_arrived and not booking.arrived_at_port:
            booking.status = BookingStatus.arrived
            booking.arrived_at_port = datetime.utcnow()
            advanced = True

    if booking.status == BookingStatus.arrived:
        customs_profile = next(
            (cp for cp in store.customs_profiles.values() if cp.booking_id == booking.id),
            None,
        )
        delivery_plan = next(
            (dp for dp in store.delivery_plans.values() if dp.booking_id == booking.id),
            None,
        )
        if (
            customs_profile
            and customs_profile.customs_status == CustomsStatus.cleared
            and booking.release_status == ReleaseStatus.released
            and delivery_plan
            and delivery_plan.delivered_at
        ):
            booking.status = BookingStatus.delivered
            booking.delivered_at = delivery_plan.delivered_at
            advanced = True

    if advanced:
        create_audit_event(
            store,
            ActorRole.system,
            "automation_engine",
            "booking_status_advanced",
            "booking",
            booking.id,
            f"Shipment status automatically advanced to {booking.status.value}.",
            {"new_status": booking.status.value},
        )

    return advanced


def run_full_automation_cycle(store: Store) -> Dict[str, AutomationResult]:
    from .operations import create_admin_task

    results: Dict[str, AutomationResult] = {}
    active_bookings = [
        b for b in store.bookings.values()
        if b.status not in (BookingStatus.delivered,)
    ]
    for booking in active_bookings:
        try_advance_booking_status(store, booking)
        results[booking.id] = run_automation_for_booking(store, booking)

    alerts = check_stale_shipments(store)
    for alert in alerts:
        booking = store.bookings.get(alert["booking_id"])
        if booking:
            existing_tasks = [
                t for t in store.admin_tasks.values()
                if t.booking_id == booking.id
                and t.task_type == alert["alert"]
                and t.status.value == "open"
            ]
            if not existing_tasks:
                create_admin_task(
                    store,
                    booking,
                    alert["alert"],
                    alert["message"],
                )

    return results


# --- Stale-data sentinel checks ---

def check_stale_shipments(store: Store, today: Optional[date] = None) -> List[Dict[str, Any]]:
    today = today or date.today()
    alerts: List[Dict[str, Any]] = []

    for booking in store.bookings.values():
        if booking.status == BookingStatus.delivered:
            continue

        state = derive_lifecycle_state(store, booking)

        if state in (
            ShipmentLifecycleState.production_in_progress,
            ShipmentLifecycleState.order_confirmed,
            ShipmentLifecycleState.deposit_due,
            ShipmentLifecycleState.deposit_paid,
            ShipmentLifecycleState.qc_required,
        ):
            if booking.cargo_ready_date_latest < today:
                alerts.append({
                    "booking_id": booking.id,
                    "alert": "overdue_cargo_ready",
                    "message": f"Cargo ready date ({booking.cargo_ready_date_latest}) has passed without supplier confirmation.",
                    "severity": "P2",
                })

        if state == ShipmentLifecycleState.cargo_ready:
            container = store.containers.get(booking.container_id) if booking.container_id else None
            if container and container.carrier_cutoff_date:
                days_to_cutoff = (container.carrier_cutoff_date - today).days
                if days_to_cutoff <= 3 and not booking.pickup_address:
                    alerts.append({
                        "booking_id": booking.id,
                        "alert": "cutoff_risk_no_pickup",
                        "message": f"Carrier cutoff in {days_to_cutoff} days but no pickup address set.",
                        "severity": "P1",
                    })

        if state in (ShipmentLifecycleState.departed_origin, ShipmentLifecycleState.in_transit):
            container = store.containers.get(booking.container_id) if booking.container_id else None
            if container and container.estimated_arrival:
                days_to_arrival = (container.estimated_arrival - today).days
                if days_to_arrival <= 5:
                    customs_profile = next(
                        (cp for cp in store.customs_profiles.values() if cp.booking_id == booking.id),
                        None,
                    )
                    if customs_profile and not customs_profile.hs_code:
                        alerts.append({
                            "booking_id": booking.id,
                            "alert": "arrival_imminent_no_customs",
                            "message": f"Arriving in {days_to_arrival} days but customs classification is incomplete.",
                            "severity": "P1",
                        })

        if state == ShipmentLifecycleState.release_blocked:
            holds = [
                h for h in store.release_holds.values()
                if h.booking_id == booking.id and h.status.value == "active"
            ]
            if holds:
                oldest_hold_age = (today - holds[0].created_at.date()).days if holds else 0
                if oldest_hold_age > 7:
                    alerts.append({
                        "booking_id": booking.id,
                        "alert": "stale_release_hold",
                        "message": f"Release hold active for {oldest_hold_age} days without resolution.",
                        "severity": "P2",
                    })

    return alerts
