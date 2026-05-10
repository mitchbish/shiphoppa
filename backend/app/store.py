from collections import defaultdict
from typing import Any, Dict, Optional

from .models import (
    AccountIntegration,
    AccountProfile,
    Booking,
    BrokerAccessLink,
    AuditEvent,
    AdminTask,
    ApprovalRequest,
    AutomationRun,
    CarrierService,
    ConsolidationWarehouse,
    Container,
    CustomsProfile,
    DeliveryPlan,
    DocumentRequirement,
    GrowthAttributionEvent,
    ImportProject,
    ImportProjectEvent,
    ImportProjectFile,
    ImportProjectSnapshot,
    ImportProjectStepData,
    ImportProjectVersion,
    Importer,
    Invoice,
    Lane,
    Notification,
    OutboundMessage,
    PaymentRecord,
    ProductionMilestone,
    PurchaseOrder,
    QualityInspection,
    ReleaseHold,
    SailingOption,
    SEOOpportunity,
    ShipmentDocument,
    ShipmentEvent,
    SourceMessage,
    SpaceOpportunity,
    SupplierDiscoveryRun,
    SupplierAccessLink,
    SupplierLead,
    SupplierPayQuote,
    SupplierPayRequest,
)


class Store:
    """In-memory store for the MVP. The model boundaries mirror future tables."""

    def __init__(self) -> None:
        self.lanes: Dict[str, Lane] = {}
        self.importers: Dict[str, Importer] = {}
        self.account_profiles: Dict[str, AccountProfile] = {}
        self.account_integrations: Dict[str, AccountIntegration] = {}
        self.bookings: Dict[str, Booking] = {}
        self.containers: Dict[str, Container] = {}
        self.carrier_services: Dict[str, CarrierService] = {}
        self.sailing_options: Dict[str, SailingOption] = {}
        self.warehouses: Dict[str, ConsolidationWarehouse] = {}
        self.document_requirements: Dict[str, DocumentRequirement] = {}
        self.shipment_documents: Dict[str, ShipmentDocument] = {}
        self.shipment_events: Dict[str, ShipmentEvent] = {}
        self.supplier_links: Dict[str, SupplierAccessLink] = {}
        self.broker_links: Dict[str, BrokerAccessLink] = {}
        self.invoices: Dict[str, Invoice] = {}
        self.payment_records: Dict[str, PaymentRecord] = {}
        self.release_holds: Dict[str, ReleaseHold] = {}
        self.customs_profiles: Dict[str, CustomsProfile] = {}
        self.delivery_plans: Dict[str, DeliveryPlan] = {}
        self.admin_tasks: Dict[str, AdminTask] = {}
        self.purchase_orders: Dict[str, PurchaseOrder] = {}
        self.production_milestones: Dict[str, ProductionMilestone] = {}
        self.quality_inspections: Dict[str, QualityInspection] = {}
        self.supplier_pay_requests: Dict[str, SupplierPayRequest] = {}
        self.supplier_pay_quotes: Dict[str, SupplierPayQuote] = {}
        self.import_projects: Dict[str, ImportProject] = {}
        self.import_project_steps: Dict[str, ImportProjectStepData] = {}
        self.import_project_versions: Dict[str, ImportProjectVersion] = {}
        self.import_project_snapshots: Dict[str, ImportProjectSnapshot] = {}
        self.import_project_events: Dict[str, ImportProjectEvent] = {}
        self.import_project_files: Dict[str, ImportProjectFile] = {}
        self.source_messages: Dict[str, SourceMessage] = {}
        self.automation_runs: Dict[str, AutomationRun] = {}
        self.approval_requests: Dict[str, ApprovalRequest] = {}
        self.outbound_messages: Dict[str, OutboundMessage] = {}
        self.seo_opportunities: Dict[str, SEOOpportunity] = {}
        self.supplier_discovery_runs: Dict[str, SupplierDiscoveryRun] = {}
        self.supplier_leads: Dict[str, SupplierLead] = {}
        self.growth_attribution_events: Dict[str, GrowthAttributionEvent] = {}
        self.notifications: Dict[str, Notification] = {}
        self.audit_events: Dict[str, AuditEvent] = {}
        self.space_opportunities: Dict[str, SpaceOpportunity] = {}
        self.idempotency_records: Dict[str, Any] = {}
        self._counters = defaultdict(int)

    def next_id(self, prefix: str) -> str:
        self._counters[prefix] += 1
        return f"{prefix}-{self._counters[prefix]:04d}"

    def importer_by_email(self, email: str) -> Optional[Importer]:
        normalized = email.strip().lower()
        for importer in self.importers.values():
            if importer.email.lower() == normalized:
                return importer
        return None

    def warehouse_for_lane(self, lane_id: str) -> Optional[ConsolidationWarehouse]:
        for warehouse in self.warehouses.values():
            if warehouse.lane_id == lane_id and warehouse.active:
                return warehouse
        return None
