from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CargoCategory(str, Enum):
    tiles_stone = "tiles_stone"
    furniture = "furniture"
    homewares = "homewares"
    bathroom_fittings = "bathroom_fittings"
    lighting = "lighting"
    hardware = "hardware"
    garden = "garden"
    automotive = "automotive"
    other = "other"


class ServiceLevel(str, Enum):
    standard = "standard"
    express = "express"


class BookingStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    matched = "matched"
    confirmed = "confirmed"
    at_warehouse = "at_warehouse"
    loaded = "loaded"
    shipped = "shipped"
    arrived = "arrived"
    delivered = "delivered"


class ContainerStatus(str, Enum):
    open = "open"
    filling = "filling"
    committed = "committed"
    loading = "loading"
    shipped = "shipped"
    arrived = "arrived"
    unpacked = "unpacked"


class ActorRole(str, Enum):
    importer = "importer"
    admin = "admin"
    system = "system"


class DeliveryMode(str, Enum):
    ship_hoppa_pickup = "ship_hoppa_pickup"
    self_delivery = "self_delivery"


class DeliveryPlanMethod(str, Enum):
    ship_hoppa_trucker = "ship_hoppa_trucker"
    importer_trucker = "importer_trucker"
    warehouse_pickup = "warehouse_pickup"


class DeliveryPlanStatus(str, Enum):
    blocked_by_release = "blocked_by_release"
    ready_to_book = "ready_to_book"
    booked = "booked"
    delivered = "delivered"


class AccountIntegrationProvider(str, Enum):
    alibaba = "alibaba"
    email_inbox = "email_inbox"
    accounting = "accounting"
    supplier_pay = "supplier_pay"
    object_storage = "object_storage"


class AccountIntegrationStatus(str, Enum):
    not_connected = "not_connected"
    connected = "connected"
    needs_attention = "needs_attention"
    coming_soon = "coming_soon"


class FeasibilityStatus(str, Enum):
    feasible = "feasible"
    tight = "tight"
    misses_cutoff = "misses_cutoff"
    admin_review = "admin_review"


class SourceType(str, Enum):
    manual_admin = "manual_admin"
    forwarder_confirmation = "forwarder_confirmation"
    carrier_api = "carrier_api"
    visibility_provider = "visibility_provider"
    warehouse_event = "warehouse_event"


class SourceConfidence(str, Enum):
    estimated = "estimated"
    verified = "verified"
    confirmed = "confirmed"


class DocumentType(str, Enum):
    commercial_invoice = "commercial_invoice"
    packing_list = "packing_list"
    supplier_photos = "supplier_photos"
    product_specs = "product_specs"
    fumigation_ispm = "fumigation_ispm"
    shipping_instructions = "shipping_instructions"
    house_bill = "house_bill"
    arrival_notice = "arrival_notice"
    delivery_order = "delivery_order"


class DocumentStatus(str, Enum):
    required = "required"
    uploaded = "uploaded"
    approved = "approved"
    rejected = "rejected"
    waived = "waived"


class ChecklistStatus(str, Enum):
    incomplete = "incomplete"
    in_review = "in_review"
    complete = "complete"


class ShipmentEventStage(str, Enum):
    booking_submitted = "booking_submitted"
    booking_confirmed = "booking_confirmed"
    pickup_scheduled = "pickup_scheduled"
    picked_up = "picked_up"
    warehouse_received = "warehouse_received"
    measured = "measured"
    variance_approved = "variance_approved"
    loaded = "loaded"
    container_committed = "container_committed"
    departed = "departed"
    transshipped = "transshipped"
    arrived = "arrived"
    customs_cleared = "customs_cleared"
    freight_released = "freight_released"
    delivered = "delivered"


class PaymentStatus(str, Enum):
    not_invoiced = "not_invoiced"
    issued = "issued"
    part_paid = "part_paid"
    paid = "paid"
    overdue = "overdue"
    void = "void"


class ReleaseStatus(str, Enum):
    blocked = "blocked"
    ready = "ready"
    released = "released"


class ReleaseHoldType(str, Enum):
    unpaid_invoice = "unpaid_invoice"
    missing_documents = "missing_documents"
    customs_hold = "customs_hold"
    warehouse_variance = "warehouse_variance"
    admin_hold = "admin_hold"


class ReleaseHoldStatus(str, Enum):
    active = "active"
    cleared = "cleared"
    waived = "waived"


class CustomsBrokerPreference(str, Enum):
    ship_hoppa_broker = "ship_hoppa_broker"
    importer_broker = "importer_broker"
    undecided = "undecided"


class CustomsStatus(str, Enum):
    documents_required = "documents_required"
    submitted = "submitted"
    queried = "queried"
    cleared = "cleared"
    held = "held"


class AdminTaskStatus(str, Enum):
    open = "open"
    done = "done"
    waived = "waived"


class ImportWorkflowType(str, Enum):
    standard_import = "standard_import"
    supplier_handoff = "supplier_handoff"
    fcl_spare_space = "fcl_spare_space"
    mcl_shared_space = "mcl_shared_space"
    customs_only = "customs_only"
    delivery_only = "delivery_only"


class ImportProjectStatus(str, Enum):
    active = "active"
    archived = "archived"
    cancelled = "cancelled"
    deleted_pending_retention = "deleted_pending_retention"
    deleted = "deleted"


class ImportProjectStepStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    complete = "complete"
    blocked = "blocked"
    skipped = "skipped"


class ImportProjectSnapshotType(str, Enum):
    order_confirmed = "order_confirmed"
    production_complete = "production_complete"
    cargo_received = "cargo_received"
    sailing_booked = "sailing_booked"
    departed = "departed"
    arrived = "arrived"
    customs_cleared = "customs_cleared"
    delivered = "delivered"
    landed_cost_finalised = "landed_cost_finalised"
    manual = "manual"


class ProjectActorType(str, Enum):
    user = "user"
    partner = "partner"
    system = "system"
    admin = "admin"


class FileBackupStatus(str, Enum):
    pending = "pending"
    complete = "complete"
    failed = "failed"
    not_required = "not_required"


class SourceMessageType(str, Enum):
    forwarded_email = "forwarded_email"
    connected_inbox = "connected_inbox"
    supplier_portal = "supplier_portal"
    courier_portal = "courier_portal"
    broker_portal = "broker_portal"
    admin_upload = "admin_upload"


class ExtractionStatus(str, Enum):
    pending = "pending"
    matched = "matched"
    needs_review = "needs_review"
    failed = "failed"


class AutomationType(str, Enum):
    match_message = "match_message"
    extract_document = "extract_document"
    chase_partner = "chase_partner"
    generate_approval = "generate_approval"
    update_eta = "update_eta"
    invoice_reconcile = "invoice_reconcile"
    bank_details_check = "bank_details_check"
    supplier_pay_quote = "supplier_pay_quote"
    delivery_prepare = "delivery_prepare"
    space_detect = "space_detect"
    supplier_discovery = "supplier_discovery"


class AutomationDecision(str, Enum):
    auto_accepted = "auto_accepted"
    customer_approval_required = "customer_approval_required"
    admin_review_required = "admin_review_required"
    failed = "failed"


class ApprovalRequestType(str, Enum):
    approve_payment = "approve_payment"
    approve_supplier_payment = "approve_supplier_payment"
    approve_trucking = "approve_trucking"
    accept_sailing_change = "accept_sailing_change"
    approve_customs_submission = "approve_customs_submission"
    approve_spare_space_listing = "approve_spare_space_listing"
    approve_release = "approve_release"
    approve_invoice_variance = "approve_invoice_variance"


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"


class PurchaseOrderStatus(str, Enum):
    draft = "draft"
    order_confirmed = "order_confirmed"
    deposit_due = "deposit_due"
    deposit_paid = "deposit_paid"
    in_production = "in_production"
    ready_for_qc = "ready_for_qc"
    qc_in_progress = "qc_in_progress"
    ready_to_ship = "ready_to_ship"
    shipped = "shipped"
    cancelled = "cancelled"


class ProductionMilestoneType(str, Enum):
    deposit_paid = "deposit_paid"
    production_started = "production_started"
    sample_ready = "sample_ready"
    sample_approved = "sample_approved"
    production_complete = "production_complete"
    qc_booked = "qc_booked"
    qc_passed = "qc_passed"
    qc_failed = "qc_failed"
    balance_due = "balance_due"
    goods_ready = "goods_ready"


class ProductionMilestoneStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    complete = "complete"
    blocked = "blocked"
    waived = "waived"


class QualityInspectionResult(str, Enum):
    not_required = "not_required"
    pending = "pending"
    booked = "booked"
    passed = "passed"
    failed = "failed"
    rework_required = "rework_required"
    waived = "waived"


class SupplierPayStage(str, Enum):
    deposit = "deposit"
    balance = "balance"
    final = "final"
    custom = "custom"


class SupplierPayProvider(str, Enum):
    wise = "wise"
    ofx = "ofx"
    manual_bank_transfer = "manual_bank_transfer"


class SupplierPayRequestStatus(str, Enum):
    draft = "draft"
    quote_ready = "quote_ready"
    approval_required = "approval_required"
    approved = "approved"
    rejected = "rejected"
    marked_paid_outside_app = "marked_paid_outside_app"
    paid = "paid"
    cancelled = "cancelled"


class SupplierPayQuoteStatus(str, Enum):
    quoted = "quoted"
    selected = "selected"
    expired = "expired"


class OutboundRecipientType(str, Enum):
    importer = "importer"
    supplier = "supplier"
    courier = "courier"
    broker = "broker"
    warehouse = "warehouse"
    forwarder = "forwarder"
    admin = "admin"


class OutboundChannel(str, Enum):
    email = "email"
    sms = "sms"
    wechat = "wechat"
    contact_form = "contact_form"


class OutboundProvider(str, Enum):
    resend = "resend"
    twilio = "twilio"
    manual = "manual"
    other = "other"


class OutboundStatus(str, Enum):
    queued = "queued"
    sent = "sent"
    delivered = "delivered"
    opened = "opened"
    clicked = "clicked"
    replied = "replied"
    bounced = "bounced"
    complained = "complained"
    failed = "failed"
    opted_out = "opted_out"


class SentinelSeverity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class SystemHealthStatus(str, Enum):
    healthy = "healthy"
    warning = "warning"
    failing = "failing"


class SEOTargetCountry(str, Enum):
    australia = "australia"
    united_states = "united_states"
    china = "china"


class SEOAudience(str, Enum):
    supplier = "supplier"
    importer = "importer"
    fcl_owner = "fcl_owner"
    mcl_buyer = "mcl_buyer"
    partner = "partner"


class SEOOpportunitySource(str, Enum):
    seo_engine = "seo_engine"
    ai_citation = "ai_citation"
    competitor_gap = "competitor_gap"
    supplier_discovery = "supplier_discovery"
    admin_seed = "admin_seed"
    partner_signal = "partner_signal"


class SEOPageType(str, Enum):
    supplier_landing = "supplier_landing"
    lane_page = "lane_page"
    category_page = "category_page"
    city_page = "city_page"
    knowledge_article = "knowledge_article"
    comparison_page = "comparison_page"


class SEOOpportunityStatus(str, Enum):
    discovered = "discovered"
    brief_ready = "brief_ready"
    page_drafted = "page_drafted"
    published = "published"
    monitoring = "monitoring"
    paused = "paused"
    rejected = "rejected"


class SupplierDiscoverySourceSet(str, Enum):
    supplier_websites = "supplier_websites"
    directories = "directories"
    trade_show = "trade_show"
    partner_referrals = "partner_referrals"
    marketplace_api = "marketplace_api"
    admin_seed = "admin_seed"
    mixed = "mixed"


class SupplierDiscoveryRunStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    paused = "paused"
    failed = "failed"
    blocked = "blocked"


class SupplierLeadSource(str, Enum):
    alibaba = "alibaba"
    made_in_china = "made_in_china"
    global_sources = "global_sources"
    trade_show = "trade_show"
    supplier_website = "supplier_website"
    partner_referral = "partner_referral"
    importer_invite = "importer_invite"
    supplier_referral = "supplier_referral"
    seo_engine = "seo_engine"
    other = "other"


class ContactMethod(str, Enum):
    email = "email"
    sms = "sms"
    wechat = "wechat"
    contact_form = "contact_form"
    phone = "phone"
    none = "none"


class SupplierOutreachStatus(str, Enum):
    discovered = "discovered"
    enriched = "enriched"
    scored = "scored"
    needs_human_review = "needs_human_review"
    approved_for_contact = "approved_for_contact"
    contacted = "contacted"
    replied = "replied"
    onboarded = "onboarded"
    referred_importer = "referred_importer"
    do_not_contact = "do_not_contact"
    rejected = "rejected"


class GrowthAttributionEventType(str, Enum):
    lead_discovered = "lead_discovered"
    lead_enriched = "lead_enriched"
    lead_contacted = "lead_contacted"
    lead_replied = "lead_replied"
    supplier_signed_up = "supplier_signed_up"
    buyer_invited = "buyer_invited"
    importer_claimed = "importer_claimed"
    shipment_created = "shipment_created"
    invoice_issued = "invoice_issued"
    revenue_recognised = "revenue_recognised"
    opt_out = "opt_out"
    complaint = "complaint"


class Coordinates(BaseModel):
    lat: float
    lng: float


class RouteWaypoint(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class Lane(BaseModel):
    id: str
    name: str
    origin_region: str
    origin_ports: List[str]
    destination_port: str
    destination_region: str
    container_type: str
    practical_cbm_limit: float
    road_weight_limit_kg: float
    max_shippers_per_container: int
    typical_transit_days_min: int
    typical_transit_days_max: int
    sailing_frequency: str
    base_container_cost_usd: float
    platform_fee_per_booking_usd: float
    max_wait_days: int
    cbm_release_threshold: float
    weight_release_threshold: float
    cutoff_days_before_sailing: int
    warehouse_receipt_cutoff_days_before_sailing: int = 6
    origin_max_pickup_radius_km: float
    pickup_fee_usd: float = 95
    priority_handling_fee_usd: float = 75
    rush_handling_fee_usd: float = 150
    cargo_restrictions: List[str]
    active: bool = True
    created_at: datetime
    updated_at: datetime


class CarrierService(BaseModel):
    id: str
    lane_id: str
    carrier_name: str
    service_name: str
    departure_port: str
    arrival_port: str
    departure_day_of_week: str
    transit_days: int
    direct_or_transhipment: str
    rate_20gp_usd: Optional[float] = None
    rate_40hc_usd: float
    thc_origin_usd: float
    thc_destination_usd: float
    documentation_fee_usd: float
    fuel_surcharge_usd: float
    peak_season_surcharge_usd: float
    total_all_in_usd: float
    empty_depot_city: str
    empty_depot_coordinates: Coordinates
    drayage_cost_to_warehouse_usd: float = 0
    drayage_cost_to_port_usd: float = 0
    schedule_reliability_pct: float
    average_delay_days: float = 0
    next_available_sailings: List[date]
    route_waypoints: List[RouteWaypoint] = Field(default_factory=list)
    route_geometry_source_type: SourceType = SourceType.manual_admin
    route_geometry_source_name: str = "Ship Hoppa route library"
    route_geometry_confidence: SourceConfidence = SourceConfidence.estimated
    booking_cutoff_days_before: int = 5
    active: bool = True
    rates_updated_at: datetime
    created_at: datetime
    updated_at: datetime


class SailingOption(BaseModel):
    id: str
    lane_id: str
    carrier_service_id: str
    carrier_name: str
    service_name: str
    departure_port: str
    arrival_port: str
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None
    etd: date
    eta: date
    transit_days: int
    direct_or_transhipment: str
    total_all_in_usd: float
    carrier_gate_in_cutoff_date: date
    shipping_instructions_cutoff_date: date
    vgm_cutoff_date: date
    route_waypoints: List[RouteWaypoint] = Field(default_factory=list)
    route_geometry_source_type: SourceType = SourceType.manual_admin
    route_geometry_source_name: str = "Ship Hoppa route library"
    route_geometry_confidence: SourceConfidence = SourceConfidence.estimated
    source_type: SourceType = SourceType.manual_admin
    source_name: str
    source_reference: Optional[str] = None
    last_verified_at: datetime
    confidence: SourceConfidence = SourceConfidence.estimated
    active: bool = True
    created_at: datetime
    updated_at: datetime


class ConsolidationWarehouse(BaseModel):
    id: str
    lane_id: str
    name: str
    city: str
    country: str
    coordinates: Coordinates
    address: str
    contact_name: str
    contact_phone: str
    contact_email: str
    operating_hours: str
    max_containers_per_week: int
    handling_fee_per_container_usd: float
    active: bool = True


class Importer(BaseModel):
    id: str
    company_name: str
    contact_name: str
    email: str
    phone: Optional[str] = None
    business_address: Optional[str] = None
    abn: Optional[str] = None
    default_lane_id: Optional[str] = None
    default_supplier_city: Optional[str] = None
    default_cargo_category: Optional[CargoCategory] = None
    default_cbm: Optional[float] = None
    default_weight_kg: Optional[float] = None
    cbm_correction_factor: float = 1.0
    bookings_count: int = 0
    total_cbm_shipped: float = 0
    created_at: datetime
    updated_at: datetime


class AccountProfile(BaseModel):
    id: str
    owner_actor_id: str
    importer_company_name: str
    importer_contact_name: str
    importer_email: str
    importer_phone: Optional[str] = None
    delivery_city: str
    delivery_postcode: Optional[str] = None
    delivery_country: str
    default_supplier_city: Optional[str] = None
    default_supplier_province: Optional[str] = None
    default_supplier_country: Optional[str] = None
    default_delivery_mode: DeliveryMode = DeliveryMode.ship_hoppa_pickup
    importer_abn: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AccountProfileUpdate(BaseModel):
    importer_company_name: Optional[str] = None
    importer_contact_name: Optional[str] = None
    importer_email: Optional[str] = None
    importer_phone: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_postcode: Optional[str] = None
    delivery_country: Optional[str] = None
    default_supplier_city: Optional[str] = None
    default_supplier_province: Optional[str] = None
    default_supplier_country: Optional[str] = None
    default_delivery_mode: Optional[DeliveryMode] = None
    importer_abn: Optional[str] = None


class AccountIntegration(BaseModel):
    id: str
    owner_actor_id: str
    provider: AccountIntegrationProvider
    display_name: str
    category: str
    status: AccountIntegrationStatus = AccountIntegrationStatus.not_connected
    connection_mode: str = "manual_prompt"
    prompt_when: List[str] = Field(default_factory=list)
    last_verified_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AccountIntegrationUpdate(BaseModel):
    status: Optional[AccountIntegrationStatus] = None
    notes: Optional[str] = None
    last_verified_at: Optional[datetime] = None


class DeliveryPlan(BaseModel):
    id: str
    booking_id: str
    delivery_method: DeliveryPlanMethod = DeliveryPlanMethod.ship_hoppa_trucker
    destination_address: str
    destination_contact_name: str
    destination_contact_phone: Optional[str] = None
    delivery_window_start: Optional[date] = None
    delivery_window_end: Optional[date] = None
    equipment_required: List[str] = Field(default_factory=list)
    status: DeliveryPlanStatus = DeliveryPlanStatus.blocked_by_release
    trucking_quote_usd: float = 0
    courier_invoice_storage_key: Optional[str] = None
    proof_of_delivery_storage_key: Optional[str] = None
    notes: Optional[str] = None
    booked_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DeliveryPlanUpdate(BaseModel):
    delivery_method: Optional[DeliveryPlanMethod] = None
    destination_address: Optional[str] = None
    destination_contact_name: Optional[str] = None
    destination_contact_phone: Optional[str] = None
    delivery_window_start: Optional[date] = None
    delivery_window_end: Optional[date] = None
    equipment_required: Optional[List[str]] = None
    trucking_quote_usd: Optional[float] = Field(default=None, ge=0)
    courier_invoice_storage_key: Optional[str] = None
    proof_of_delivery_storage_key: Optional[str] = None
    notes: Optional[str] = None


class Booking(BaseModel):
    id: str
    importer_id: str
    lane_id: Optional[str] = None
    container_id: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_city: str
    supplier_province: Optional[str] = None
    supplier_country: str
    supplier_coordinates: Coordinates
    delivery_city: str
    delivery_postcode: Optional[str] = None
    delivery_country: str
    cargo_description: Optional[str] = None
    cargo_category: CargoCategory
    hs_code: Optional[str] = None
    cbm_estimate: float
    cbm_actual: Optional[float] = None
    weight_kg_estimate: float
    weight_kg_actual: Optional[float] = None
    number_of_packages: Optional[int] = None
    package_type: Optional[str] = None
    package_length_cm: Optional[float] = None
    package_width_cm: Optional[float] = None
    package_height_cm: Optional[float] = None
    cargo_ready_date_earliest: date
    cargo_ready_date_latest: date
    service_level: ServiceLevel
    delivery_mode: DeliveryMode = DeliveryMode.ship_hoppa_pickup
    pickup_address: Optional[str] = None
    pickup_contact_name: Optional[str] = None
    pickup_contact_phone: Optional[str] = None
    pickup_window_start: Optional[date] = None
    pickup_window_end: Optional[date] = None
    warehouse_receipt_cutoff: Optional[date] = None
    latest_supplier_ready_date: Optional[date] = None
    feasibility_status: Optional[FeasibilityStatus] = None
    feasibility_reason: Optional[str] = None
    preferred_sailing_option_id: Optional[str] = None
    preferred_container_id: Optional[str] = None
    checklist_status: ChecklistStatus = ChecklistStatus.incomplete
    tracking_status: ShipmentEventStage = ShipmentEventStage.booking_submitted
    payment_status: PaymentStatus = PaymentStatus.not_invoiced
    release_status: ReleaseStatus = ReleaseStatus.blocked
    exception_count: int = 0
    status: BookingStatus = BookingStatus.submitted
    match_score: Optional[float] = None
    match_confidence: Optional[str] = None
    admin_review_required: bool = False
    matched_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    received_at_warehouse: Optional[datetime] = None
    loaded_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    arrived_at_port: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    quoted_cost_usd: Optional[float] = None
    cbm_cost_usd: Optional[float] = None
    platform_fee_usd: Optional[float] = None
    urgency_fee_usd: float = 0
    pickup_fee_usd: float = 0
    total_cost_usd: Optional[float] = None
    paid: bool = False
    paid_at: Optional[datetime] = None
    warehouse_receipt_photos: List[str] = Field(default_factory=list)
    loading_photos: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class Container(BaseModel):
    id: str
    lane_id: str
    status: ContainerStatus
    bookings: List[str] = Field(default_factory=list)
    current_cbm: float = 0
    current_weight_kg: float = 0
    remaining_cbm: float = 0
    remaining_weight_kg: float = 0
    fill_percentage_cbm: float = 0
    fill_percentage_weight: float = 0
    shipper_count: int = 0
    target_sailing_date: date
    carrier_cutoff_date: date
    warehouse_receipt_cutoff_date: Optional[date] = None
    shipping_instructions_cutoff_date: Optional[date] = None
    vgm_cutoff_date: Optional[date] = None
    container_close_date: Optional[date] = None
    opened_at: datetime
    oldest_booking_date: date
    carrier_name: Optional[str] = None
    carrier_service_id: Optional[str] = None
    sailing_option_id: Optional[str] = None
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None
    container_number: Optional[str] = None
    bill_of_lading_number: Optional[str] = None
    container_cost_usd: Optional[float] = None
    total_platform_fees_usd: float = 0
    cost_per_cbm_usd: Optional[float] = None
    estimated_departure: Optional[date] = None
    actual_departure: Optional[date] = None
    estimated_arrival: Optional[date] = None
    actual_arrival: Optional[date] = None
    baseline_estimated_arrival: Optional[date] = None
    eta_last_changed_at: Optional[datetime] = None
    route_waypoints: List[RouteWaypoint] = Field(default_factory=list)
    route_geometry_source_type: SourceType = SourceType.manual_admin
    route_geometry_source_name: str = "Ship Hoppa route library"
    route_geometry_confidence: SourceConfidence = SourceConfidence.estimated
    sailing_source_type: SourceType = SourceType.manual_admin
    sailing_source_name: str = "Ship Hoppa planning"
    sailing_source_reference: Optional[str] = None
    sailing_source_last_verified_at: Optional[datetime] = None
    sailing_source_confidence: SourceConfidence = SourceConfidence.estimated
    created_at: datetime
    updated_at: datetime


class Notification(BaseModel):
    id: str
    recipient_type: str
    recipient_id: str
    trigger: str
    channel: str = "in_app"
    message: str
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    read: bool = False


class AuditEvent(BaseModel):
    id: str
    actor_role: ActorRole
    actor_id: str
    event_type: str
    entity_type: str
    entity_id: str
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class DocumentRequirement(BaseModel):
    id: str
    booking_id: str
    document_type: DocumentType
    label: str
    required: bool = True
    reason: str
    status: DocumentStatus = DocumentStatus.required
    created_at: datetime
    updated_at: datetime


class ShipmentDocument(BaseModel):
    id: str
    booking_id: str
    document_type: DocumentType
    file_name: str
    storage_key: str
    mime_type: str = "application/octet-stream"
    size_bytes: int = 0
    status: DocumentStatus = DocumentStatus.uploaded
    uploaded_by_role: ActorRole = ActorRole.importer
    uploaded_by_id: str
    notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ShipmentEvent(BaseModel):
    id: str
    booking_id: str
    container_id: Optional[str] = None
    stage: ShipmentEventStage
    label: str
    source_type: SourceType
    source_name: str
    confidence: SourceConfidence
    occurred_at: Optional[datetime] = None
    estimated_at: Optional[datetime] = None
    notes: Optional[str] = None
    photos: List[str] = Field(default_factory=list)
    created_at: datetime


class SupplierAccessLink(BaseModel):
    id: str
    booking_id: str
    token: str
    active: bool = True
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime


class InvoiceLineItem(BaseModel):
    id: str
    invoice_id: str
    label: str
    amount_usd: float
    source: str


class Invoice(BaseModel):
    id: str
    booking_id: str
    status: PaymentStatus = PaymentStatus.issued
    line_items: List[InvoiceLineItem] = Field(default_factory=list)
    subtotal_usd: float = 0
    total_usd: float = 0
    issued_at: datetime
    due_date: date
    paid_at: Optional[datetime] = None
    provider_reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PaymentRecord(BaseModel):
    id: str
    invoice_id: str
    amount_usd: float
    method: str = "manual"
    provider_reference: Optional[str] = None
    paid_at: datetime
    created_at: datetime


class ReleaseHold(BaseModel):
    id: str
    booking_id: str
    hold_type: ReleaseHoldType
    status: ReleaseHoldStatus = ReleaseHoldStatus.active
    reason: str
    created_at: datetime
    cleared_at: Optional[datetime] = None
    waived_by: Optional[str] = None
    waiver_reason: Optional[str] = None


class CustomsProfile(BaseModel):
    id: str
    booking_id: str
    incoterm: str = "FOB"
    goods_value_usd: float = 10000
    currency: str = "USD"
    hs_code: Optional[str] = None
    importer_abn: Optional[str] = None
    broker_preference: CustomsBrokerPreference = CustomsBrokerPreference.ship_hoppa_broker
    biosecurity_flags: List[str] = Field(default_factory=list)
    customs_status: CustomsStatus = CustomsStatus.documents_required
    duty_estimate_usd: float = 0
    gst_estimate_usd: float = 0
    brokerage_fee_usd: float = 175
    landed_cost_estimate_usd: float = 0
    customs_entry_number: Optional[str] = None
    duty_paid_usd: Optional[float] = None
    gst_paid_usd: Optional[float] = None
    broker_notes: Optional[str] = None
    updated_at: datetime


class AdminTask(BaseModel):
    id: str
    booking_id: str
    task_type: str
    title: str
    status: AdminTaskStatus = AdminTaskStatus.open
    due_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SpaceOpportunityStatus(str, Enum):
    detected = "detected"
    awaiting_owner_approval = "awaiting_owner_approval"
    listed = "listed"
    matched = "matched"
    closed = "closed"
    declined = "declined"


class SpaceOpportunity(BaseModel):
    id: str
    booking_id: str
    container_id: Optional[str] = None
    opportunity_type: str = "sell_spare_fcl_space"
    total_container_cbm: float
    booked_cbm: float
    protected_buffer_cbm: float = 0
    recoverable_cbm: float
    estimated_recovery_usd: float = 0
    status: SpaceOpportunityStatus = SpaceOpportunityStatus.detected
    owner_actor_id: str
    detected_at: datetime
    listed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None


class PurchaseOrder(BaseModel):
    id: str
    import_project_id: str
    booking_id: Optional[str] = None
    order_reference: str
    buyer_company_name: str
    supplier_name: str
    supplier_contact_email: Optional[str] = None
    supplier_contact_phone: Optional[str] = None
    product_summary: str
    incoterm: str = "FOB"
    currency: str = "USD"
    goods_value: float = 0
    deposit_amount: float = 0
    balance_amount: float = 0
    production_due_date: Optional[date] = None
    cargo_ready_target_date: Optional[date] = None
    status: PurchaseOrderStatus = PurchaseOrderStatus.order_confirmed
    source_message_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProductionMilestone(BaseModel):
    id: str
    purchase_order_id: str
    milestone_type: ProductionMilestoneType
    label: str
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    owner: str = "supplier"
    status: ProductionMilestoneStatus = ProductionMilestoneStatus.pending
    evidence_document_id: Optional[str] = None
    notes: Optional[str] = None
    buyer_approval_required: bool = False
    created_at: datetime
    updated_at: datetime


class QualityInspection(BaseModel):
    id: str
    purchase_order_id: str
    inspection_required: bool = False
    inspection_provider: Optional[str] = None
    inspection_date: Optional[date] = None
    inspection_location: Optional[str] = None
    report_document_id: Optional[str] = None
    result: QualityInspectionResult = QualityInspectionResult.not_required
    defects_summary: Optional[str] = None
    buyer_approval_required: bool = False
    created_at: datetime
    updated_at: datetime


class SupplierPayRequest(BaseModel):
    id: str
    purchase_order_id: str
    import_project_id: str
    booking_id: Optional[str] = None
    payment_stage: SupplierPayStage
    supplier_name: str
    supplier_invoice_reference: Optional[str] = None
    amount: float
    currency: str = "USD"
    status: SupplierPayRequestStatus = SupplierPayRequestStatus.approval_required
    requested_by: str
    approval_request_id: Optional[str] = None
    selected_quote_id: Optional[str] = None
    marked_paid_at: Optional[datetime] = None
    paid_outside_app_by: Optional[str] = None
    proof_storage_key: Optional[str] = None
    notes: Optional[str] = None
    bank_details_fingerprint: Optional[str] = None
    bank_details_changed: bool = False
    created_at: datetime
    updated_at: datetime


class SupplierPayQuote(BaseModel):
    id: str
    supplier_pay_request_id: str
    provider: SupplierPayProvider
    provider_reference: Optional[str] = None
    source_type: SourceType = SourceType.manual_admin
    source_name: str = "Ship Hoppa quote estimate"
    amount: float
    source_currency: str = "USD"
    target_currency: str = "USD"
    fx_rate: float = 1
    provider_fee: float = 0
    estimated_total: float = 0
    expires_at: Optional[datetime] = None
    status: SupplierPayQuoteStatus = SupplierPayQuoteStatus.quoted
    selected: bool = False
    created_at: datetime


class ImportProject(BaseModel):
    id: str
    organization_id: str
    owner_user_id: str
    workflow_type: ImportWorkflowType = ImportWorkflowType.standard_import
    workflow_version: str = "2026.05"
    title: str
    description: Optional[str] = None
    status: ImportProjectStatus = ImportProjectStatus.active
    current_step: str = "intake"
    next_action: Optional[str] = None
    blocked_reason: Optional[str] = None
    summary: str = ""
    linked_purchase_order_ids: List[str] = Field(default_factory=list)
    linked_shipment_ids: List[str] = Field(default_factory=list)
    linked_supplier_workspace_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class ImportProjectStepData(BaseModel):
    id: str
    import_project_id: str
    step_key: str
    step_number: int
    data: Dict[str, Any] = Field(default_factory=dict)
    status: ImportProjectStepStatus = ImportProjectStepStatus.not_started
    source_references: List[str] = Field(default_factory=list)
    updated_at: datetime


class ImportProjectVersion(BaseModel):
    id: str
    import_project_id: str
    version_number: int
    changed_by: str
    action: str
    step_key: Optional[str] = None
    source_reference: Optional[str] = None
    before_summary: Optional[str] = None
    after_summary: Optional[str] = None
    created_at: datetime


class ImportProjectSnapshot(BaseModel):
    id: str
    import_project_id: str
    snapshot_type: ImportProjectSnapshotType
    snapshot_data: Dict[str, Any] = Field(default_factory=dict)
    file_manifest: List[str] = Field(default_factory=list)
    created_by: str
    created_at: datetime
    storage_key: str


class ImportProjectEvent(BaseModel):
    id: str
    import_project_id: str
    event_type: str
    event_reference: Optional[str] = None
    actor_type: ProjectActorType
    actor_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime


class ImportProjectFile(BaseModel):
    id: str
    import_project_id: str
    shipment_id: Optional[str] = None
    folder: str
    filename: str
    content_type: str = "application/octet-stream"
    size_bytes: int = 0
    storage_provider: str = "railway_postgres"
    storage_key: str
    backup_provider: str = "cloudflare_r2"
    backup_storage_key: Optional[str] = None
    archive_storage_key: Optional[str] = None
    archive_created_at: Optional[datetime] = None
    backup_status: FileBackupStatus = FileBackupStatus.pending
    checksum: Optional[str] = None
    uploaded_by: str
    source_message_id: Optional[str] = None
    document_id: Optional[str] = None
    created_at: datetime


class SourceMessage(BaseModel):
    id: str
    source_type: SourceMessageType
    from_address: str
    to_addresses: List[str] = Field(default_factory=list)
    subject: str
    body: str = ""
    received_at: datetime
    attachments: List[str] = Field(default_factory=list)
    matched_import_project_id: Optional[str] = None
    matched_shipment_id: Optional[str] = None
    extraction_status: ExtractionStatus = ExtractionStatus.pending
    confidence: SourceConfidence = SourceConfidence.estimated
    created_at: datetime


class SourceMessageCreate(BaseModel):
    source_type: SourceMessageType = SourceMessageType.forwarded_email
    from_address: str
    to_addresses: List[str] = Field(default_factory=list)
    subject: str
    body: str = ""
    received_at: Optional[datetime] = None
    attachment_names: List[str] = Field(default_factory=list)


class OutboundMessageCreate(BaseModel):
    recipient_type: OutboundRecipientType
    recipient_id: str
    channel: OutboundChannel
    template_key: str
    body_snapshot: str
    subject: Optional[str] = None
    template_version: str = "v1"
    campaign_id: Optional[str] = None
    compliance_basis: str
    provider: Optional[OutboundProvider] = None
    related_supplier_lead_id: Optional[str] = None
    related_shipment_id: Optional[str] = None


class AutomationRun(BaseModel):
    id: str
    automation_type: AutomationType
    input_reference: str
    output_reference: Optional[str] = None
    confidence: SourceConfidence = SourceConfidence.estimated
    decision: AutomationDecision
    reason: str
    created_tasks: List[str] = Field(default_factory=list)
    created_approvals: List[str] = Field(default_factory=list)
    audit_event_id: Optional[str] = None
    created_at: datetime


class ApprovalRequest(BaseModel):
    id: str
    request_type: ApprovalRequestType
    status: ApprovalStatus = ApprovalStatus.pending
    title: str
    plain_language_summary: str
    amount_usd: Optional[float] = None
    due_at: Optional[datetime] = None
    related_import_project_id: Optional[str] = None
    related_booking_id: Optional[str] = None
    source_reference: Optional[str] = None
    created_at: datetime
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None


class OutboundMessage(BaseModel):
    id: str
    recipient_type: OutboundRecipientType
    recipient_id: str
    channel: OutboundChannel
    provider: OutboundProvider = OutboundProvider.manual
    provider_message_id: Optional[str] = None
    template_key: str
    template_version: str = "v1"
    campaign_id: Optional[str] = None
    subject: Optional[str] = None
    body_snapshot: str
    status: OutboundStatus = OutboundStatus.queued
    failure_code: Optional[str] = None
    sentinel_error_code: Optional[str] = None
    compliance_basis: str
    suppression_checked_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    opt_out_at: Optional[datetime] = None
    related_supplier_lead_id: Optional[str] = None
    related_shipment_id: Optional[str] = None
    created_at: datetime


class SentinelErrorDefinition(BaseModel):
    code: str
    category: str
    severity: SentinelSeverity
    user_safe_message: str
    internal_message: str
    retryable: bool
    creates_admin_task: bool
    sends_sms_alert: bool
    runbook_url: Optional[str] = None


class SystemHealthCheck(BaseModel):
    key: str
    label: str
    provider: Optional[str] = None
    status: SystemHealthStatus
    configured: bool
    message: str
    sentinel_error_code: Optional[str] = None
    last_checked_at: datetime


class SystemHealthResponse(BaseModel):
    overall_status: SystemHealthStatus
    checked_at: datetime
    environment: str
    checks: List[SystemHealthCheck]
    active_error_codes: List[SentinelErrorDefinition]
    queued_outbound_messages: int = 0
    failed_outbound_messages: int = 0
    open_admin_tasks: int = 0
    open_approvals: int = 0


class SEOOpportunity(BaseModel):
    id: str
    target_country: SEOTargetCountry
    audience: SEOAudience
    category: str
    city: Optional[str] = None
    lane: Optional[str] = None
    keyword_cluster: List[str] = Field(default_factory=list)
    search_intent: str
    source: SEOOpportunitySource = SEOOpportunitySource.seo_engine
    opportunity_score: float = Field(..., ge=0, le=100)
    page_type: SEOPageType
    cms_page_id: Optional[str] = None
    status: SEOOpportunityStatus = SEOOpportunityStatus.discovered
    related_supplier_discovery_run_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SEOOpportunityCreate(BaseModel):
    target_country: SEOTargetCountry
    audience: SEOAudience = SEOAudience.supplier
    category: str
    city: Optional[str] = None
    lane: Optional[str] = None
    keyword_cluster: List[str] = Field(default_factory=list)
    search_intent: str = "supplier_acquisition"
    source: SEOOpportunitySource = SEOOpportunitySource.seo_engine
    opportunity_score: float = Field(75, ge=0, le=100)
    page_type: SEOPageType = SEOPageType.supplier_landing
    create_discovery_run: bool = True


class SupplierDiscoveryRun(BaseModel):
    id: str
    seo_opportunity_id: Optional[str] = None
    target_country: SEOTargetCountry
    target_city: Optional[str] = None
    product_category: str
    lane: Optional[str] = None
    source_set: SupplierDiscoverySourceSet = SupplierDiscoverySourceSet.mixed
    query_terms: List[str] = Field(default_factory=list)
    source_rules: List[str] = Field(default_factory=list)
    run_status: SupplierDiscoveryRunStatus = SupplierDiscoveryRunStatus.queued
    leads_found: int = 0
    leads_enriched: int = 0
    leads_rejected: int = 0
    leads_approved_for_contact: int = 0
    compliance_review_required: bool = True
    sentinel_error_code: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class SupplierLead(BaseModel):
    id: str
    company_name: str
    country: str
    city: Optional[str] = None
    product_categories: List[str] = Field(default_factory=list)
    discovery_source: SupplierLeadSource
    discovery_source_url: str
    platform_profile_url: Optional[str] = None
    company_website: Optional[str] = None
    public_contact_source_url: str
    public_contact_captured_at: datetime
    public_email: Optional[str] = None
    public_phone: Optional[str] = None
    public_wechat: Optional[str] = None
    preferred_language: str = "zh-CN"
    exports_to_regions: List[str] = Field(default_factory=list)
    overseas_buyer_signals: List[str] = Field(default_factory=list)
    bulky_goods_fit: bool = False
    lead_score: float = Field(0, ge=0, le=100)
    fit_reason: str
    compliance_basis: str
    contact_method_allowed: ContactMethod = ContactMethod.none
    outreach_status: SupplierOutreachStatus = SupplierOutreachStatus.discovered
    supplier_discovery_run_id: Optional[str] = None
    last_contacted_at: Optional[datetime] = None
    next_follow_up_at: Optional[datetime] = None
    opt_out_at: Optional[datetime] = None
    do_not_contact: bool = False
    assigned_owner: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class GrowthAttributionEvent(BaseModel):
    id: str
    event_type: GrowthAttributionEventType
    supplier_lead_id: Optional[str] = None
    supplier_workspace_id: Optional[str] = None
    importer_organization_id: Optional[str] = None
    shipment_id: Optional[str] = None
    campaign_id: Optional[str] = None
    source: str
    channel: Optional[str] = None
    template_key: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    value_usd: Optional[float] = None
    occurred_at: datetime


class ImportProjectWorkspaceResponse(BaseModel):
    project: ImportProject
    steps: List[ImportProjectStepData]
    versions: List[ImportProjectVersion]
    events: List[ImportProjectEvent]
    files: List[ImportProjectFile]
    bookings: List[Booking]
    purchase_orders: List[PurchaseOrder]
    production_milestones: List[ProductionMilestone]
    quality_inspections: List[QualityInspection]
    supplier_pay_requests: List[SupplierPayRequest]
    supplier_pay_quotes: List[SupplierPayQuote]
    source_messages: List[SourceMessage]
    automation_runs: List[AutomationRun]
    approvals: List[ApprovalRequest]


class DocumentUploadRequest(BaseModel):
    document_type: DocumentType
    file_name: str
    mime_type: str = "application/octet-stream"
    content_base64: Optional[str] = None
    notes: Optional[str] = None


class DocumentDecisionRequest(BaseModel):
    reason: Optional[str] = None


class PurchaseOrderCreate(BaseModel):
    booking_id: Optional[str] = None
    import_project_id: Optional[str] = None
    order_reference: str
    buyer_company_name: str
    supplier_name: str
    supplier_contact_email: Optional[str] = None
    supplier_contact_phone: Optional[str] = None
    product_summary: str
    incoterm: str = "FOB"
    currency: str = "USD"
    goods_value: float = Field(..., ge=0)
    deposit_amount: float = Field(0, ge=0)
    balance_amount: float = Field(0, ge=0)
    production_due_date: Optional[date] = None
    cargo_ready_target_date: Optional[date] = None
    inspection_required: bool = False
    source_message_id: Optional[str] = None


class ProductionMilestoneCompleteRequest(BaseModel):
    evidence_document_id: Optional[str] = None
    notes: Optional[str] = None


class SupplierPayRequestCreate(BaseModel):
    payment_stage: SupplierPayStage
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    supplier_invoice_reference: Optional[str] = None
    bank_details_fingerprint: Optional[str] = None
    bank_details_changed: bool = False
    notes: Optional[str] = None


class SupplierPayMarkPaidRequest(BaseModel):
    paid_by: str = "importer"
    proof_storage_key: Optional[str] = None
    notes: Optional[str] = None


class ApprovalDecisionRequest(BaseModel):
    reason: Optional[str] = None
    decided_by: str = "importer"


class BookingChecklistResponse(BaseModel):
    booking_id: str
    checklist_status: ChecklistStatus
    requirements: List[DocumentRequirement]
    documents: List[ShipmentDocument]
    missing_document_types: List[DocumentType]


class ShipmentEventCreate(BaseModel):
    stage: ShipmentEventStage
    label: Optional[str] = None
    occurred_at: Optional[datetime] = None
    estimated_at: Optional[datetime] = None
    source_type: SourceType = SourceType.manual_admin
    source_name: str = "Ship Hoppa ops"
    confidence: SourceConfidence = SourceConfidence.verified
    notes: Optional[str] = None


class SailingSearchResult(BaseModel):
    sailing_option_id: str
    container_id: Optional[str] = None
    lane_id: str
    carrier_name: str
    service_name: str
    departure_port: str
    arrival_port: str
    etd: date
    eta: date
    transit_days: int
    warehouse_receipt_cutoff_date: date
    carrier_gate_in_cutoff_date: date
    available_cbm: float
    available_weight_kg: float
    source_confidence: SourceConfidence
    source_name: str
    total_all_in_usd: float
    route_waypoints: List[RouteWaypoint] = Field(default_factory=list)
    route_geometry_source_type: SourceType = SourceType.manual_admin
    route_geometry_source_name: str = "Ship Hoppa route library"
    route_geometry_confidence: SourceConfidence = SourceConfidence.estimated


class SupplierLinkCreate(BaseModel):
    booking_id: str


class SupplierReadyRequest(BaseModel):
    cargo_ready_date_latest: date
    pickup_address: Optional[str] = None
    pickup_contact_name: Optional[str] = None
    pickup_contact_phone: Optional[str] = None
    pickup_window_start: Optional[date] = None
    pickup_window_end: Optional[date] = None


class SupplierBookingSummary(BaseModel):
    id: str
    supplier_name: Optional[str] = None
    supplier_city: str
    cargo_description: Optional[str] = None
    cargo_category: CargoCategory
    cbm_estimate: float
    weight_kg_estimate: float
    cargo_ready_date_latest: date
    delivery_mode: DeliveryMode
    pickup_address: Optional[str] = None
    pickup_contact_name: Optional[str] = None
    pickup_contact_phone: Optional[str] = None
    pickup_window_start: Optional[date] = None
    pickup_window_end: Optional[date] = None
    warehouse_receipt_cutoff: Optional[date] = None
    latest_supplier_ready_date: Optional[date] = None
    status: BookingStatus


class SupplierPortalResponse(BaseModel):
    booking: SupplierBookingSummary
    supplier_instructions: str
    checklist: BookingChecklistResponse
    events: List[ShipmentEvent]


class BrokerLinkCreate(BaseModel):
    booking_id: str


class BrokerClearanceUpdate(BaseModel):
    customs_status: CustomsStatus
    customs_entry_number: Optional[str] = None
    duty_paid_usd: Optional[float] = Field(None, ge=0)
    gst_paid_usd: Optional[float] = Field(None, ge=0)
    broker_notes: Optional[str] = None


class BrokerBookingSummary(BaseModel):
    id: str
    importer_company_name: Optional[str] = None
    importer_abn: Optional[str] = None
    supplier_country: str
    delivery_country: str
    delivery_city: str
    cargo_description: Optional[str] = None
    cargo_category: CargoCategory
    cbm_estimate: float
    weight_kg_estimate: float
    cargo_ready_date_latest: date
    status: BookingStatus


class BrokerCustomsSummary(BaseModel):
    incoterm: str
    goods_value_usd: float
    currency: str
    hs_code: Optional[str] = None
    biosecurity_flags: List[str]
    customs_status: CustomsStatus
    duty_estimate_usd: float
    gst_estimate_usd: float
    landed_cost_estimate_usd: float
    customs_entry_number: Optional[str] = None
    duty_paid_usd: Optional[float] = None
    gst_paid_usd: Optional[float] = None
    broker_notes: Optional[str] = None
    updated_at: datetime


class BrokerPortalResponse(BaseModel):
    booking: BrokerBookingSummary
    customs: BrokerCustomsSummary
    holds: List[ReleaseHold]
    documents: List[ShipmentDocument]
    events: List[ShipmentEvent]


class BrokerAccessLink(BaseModel):
    id: str
    booking_id: str
    token: str
    active: bool = True
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime


class WarehouseLinkCreate(BaseModel):
    booking_id: str


class WarehouseReceiptUpdate(BaseModel):
    actual_cbm: float = Field(..., gt=0)
    actual_weight_kg: float = Field(..., gt=0)
    notes: Optional[str] = None


class WarehouseBookingSummary(BaseModel):
    id: str
    importer_company_name: Optional[str] = None
    supplier_country: str
    supplier_city: str
    cargo_description: Optional[str] = None
    cargo_category: CargoCategory
    cbm_estimate: float
    weight_kg_estimate: float
    number_of_packages: Optional[int] = None
    cargo_ready_date_latest: date
    delivery_mode: DeliveryMode
    warehouse_receipt_cutoff: Optional[date] = None
    warehouse_name: Optional[str] = None
    cbm_actual: Optional[float] = None
    weight_kg_actual: Optional[float] = None
    received_at_warehouse: Optional[datetime] = None
    status: BookingStatus


class WarehousePortalResponse(BaseModel):
    booking: WarehouseBookingSummary
    documents: List[ShipmentDocument]
    events: List[ShipmentEvent]


class WarehouseAccessLink(BaseModel):
    id: str
    booking_id: str
    token: str
    active: bool = True
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime


class CarrierLinkCreate(BaseModel):
    booking_id: str


class CarrierEtaUpdate(BaseModel):
    estimated_arrival: date
    note: Optional[str] = None


class CarrierEventUpdate(BaseModel):
    stage: ShipmentEventStage
    label: Optional[str] = None
    notes: Optional[str] = None


class CarrierBookingSummary(BaseModel):
    id: str
    importer_company_name: Optional[str] = None
    container_id: Optional[str] = None
    container_number: Optional[str] = None
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None
    carrier_name: Optional[str] = None
    estimated_departure: Optional[date] = None
    estimated_arrival: Optional[date] = None
    baseline_estimated_arrival: Optional[date] = None
    target_sailing_date: Optional[date] = None
    carrier_cutoff_date: Optional[date] = None
    cargo_description: Optional[str] = None
    cargo_category: CargoCategory
    cbm_estimate: float
    weight_kg_estimate: float
    status: BookingStatus


class CarrierPortalResponse(BaseModel):
    booking: CarrierBookingSummary
    documents: List[ShipmentDocument]
    events: List[ShipmentEvent]


class CarrierAccessLink(BaseModel):
    id: str
    booking_id: str
    token: str
    active: bool = True
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime


class ReleaseStatusResponse(BaseModel):
    booking_id: str
    release_status: ReleaseStatus
    can_release: bool
    holds: List[ReleaseHold]


class CustomsProfileUpdate(BaseModel):
    incoterm: Optional[str] = None
    goods_value_usd: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = None
    hs_code: Optional[str] = None
    importer_abn: Optional[str] = None
    broker_preference: Optional[CustomsBrokerPreference] = None
    biosecurity_flags: Optional[List[str]] = None
    customs_status: Optional[CustomsStatus] = None


class BookingCreate(BaseModel):
    importer_company_name: str = Field(..., min_length=2)
    importer_contact_name: str = Field(..., min_length=2)
    importer_email: str = Field(..., min_length=5)
    importer_phone: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_city: str
    supplier_province: Optional[str] = None
    supplier_country: str = "China"
    delivery_city: str
    delivery_postcode: Optional[str] = None
    delivery_country: str = "Australia"
    cargo_description: Optional[str] = None
    cargo_category: CargoCategory
    cbm_estimate: float = Field(..., gt=0)
    weight_kg_estimate: float = Field(..., gt=0)
    number_of_packages: Optional[int] = Field(None, ge=1)
    package_type: Optional[str] = None
    package_length_cm: Optional[float] = Field(None, gt=0)
    package_width_cm: Optional[float] = Field(None, gt=0)
    package_height_cm: Optional[float] = Field(None, gt=0)
    cargo_ready_date_earliest: date
    cargo_ready_date_latest: date
    service_level: ServiceLevel = ServiceLevel.standard
    delivery_mode: DeliveryMode = DeliveryMode.ship_hoppa_pickup
    pickup_address: Optional[str] = None
    pickup_contact_name: Optional[str] = None
    pickup_contact_phone: Optional[str] = None
    pickup_window_start: Optional[date] = None
    pickup_window_end: Optional[date] = None
    preferred_sailing_option_id: Optional[str] = None
    preferred_container_id: Optional[str] = None


class ConfirmBookingResponse(BaseModel):
    booking: Booking
    warehouse: ConsolidationWarehouse
    supplier_instructions: str


class MatchResult(BaseModel):
    booking: Booking
    container: Optional[Container] = None
    lane: Optional[Lane] = None
    warehouse: Optional[ConsolidationWarehouse] = None
    notification: Notification
    lcl_estimate_usd: Optional[float] = None
    saving_usd: Optional[float] = None
    saving_percent: Optional[float] = None


class CarrierScoreComponents(BaseModel):
    cost: float
    schedule: float
    transit: float
    depot_proximity: float
    reliability: float


class CarrierOption(BaseModel):
    sailing_option_id: str
    service_id: str
    carrier_name: str
    service_name: str
    departure_port: str
    arrival_port: str
    sailing_date: date
    eta: date
    transit_days: int
    direct_or_transhipment: str
    total_all_in_usd: float
    carrier_gate_in_cutoff_date: date
    shipping_instructions_cutoff_date: date
    vgm_cutoff_date: date
    source_type: SourceType
    source_name: str
    source_reference: Optional[str] = None
    last_verified_at: datetime
    confidence: SourceConfidence
    route_waypoints: List[RouteWaypoint] = Field(default_factory=list)
    route_geometry_source_type: SourceType = SourceType.manual_admin
    route_geometry_source_name: str = "Ship Hoppa route library"
    route_geometry_confidence: SourceConfidence = SourceConfidence.estimated
    score: float
    components: CarrierScoreComponents


class CommitContainerRequest(BaseModel):
    sailing_option_id: Optional[str] = None
    carrier_service_id: Optional[str] = None
    sailing_date: Optional[date] = None
    confirmed_carrier_cutoff_date: Optional[date] = None
    confirmed_shipping_instructions_cutoff_date: Optional[date] = None
    confirmed_vgm_cutoff_date: Optional[date] = None
    source_reference: Optional[str] = None


class ReleaseCheckResult(BaseModel):
    container_id: str
    released: bool
    reasons: List[str]
    selected_carrier: Optional[CarrierOption] = None


class CapacitySnapshot(BaseModel):
    cbm: float
    weight_kg: float
    cbm_pct: float
    weight_pct: float
    shippers: int


class DashboardSummary(BaseModel):
    lanes: int
    bookings: int
    containers: int
    committed_containers: int
    import_projects: int = 0
    source_messages: int = 0
    supplier_leads: int = 0
    open_approvals: int = 0
    open_revenue_usd: float
    outstanding_payments_usd: float
    notifications: List[Notification]
    audit_events: List[AuditEvent]
    category_density_defaults: Dict[str, float]
