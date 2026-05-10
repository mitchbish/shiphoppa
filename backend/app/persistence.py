import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

from .models import (
    AccountIntegration,
    AccountProfile,
    AdminTask,
    ApprovalRequest,
    AuditEvent,
    AutomationRun,
    Booking,
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
    SupplierAccessLink,
    SupplierDiscoveryRun,
    SupplierLead,
    SupplierPayQuote,
    SupplierPayRequest,
)
from .store import Store


SNAPSHOT_VERSION = "ship-hoppa-store-snapshot-v1"
DEFAULT_SNAPSHOT_PATH = Path(__file__).resolve().parents[1] / "storage" / "store_snapshot.json"
SNAPSHOT_WRITE_LOCK = Lock()

STORE_COLLECTION_MODELS: Dict[str, Type[BaseModel]] = {
    "lanes": Lane,
    "importers": Importer,
    "account_profiles": AccountProfile,
    "account_integrations": AccountIntegration,
    "bookings": Booking,
    "containers": Container,
    "carrier_services": CarrierService,
    "sailing_options": SailingOption,
    "warehouses": ConsolidationWarehouse,
    "document_requirements": DocumentRequirement,
    "shipment_documents": ShipmentDocument,
    "shipment_events": ShipmentEvent,
    "supplier_links": SupplierAccessLink,
    "invoices": Invoice,
    "payment_records": PaymentRecord,
    "release_holds": ReleaseHold,
    "customs_profiles": CustomsProfile,
    "delivery_plans": DeliveryPlan,
    "admin_tasks": AdminTask,
    "purchase_orders": PurchaseOrder,
    "production_milestones": ProductionMilestone,
    "quality_inspections": QualityInspection,
    "supplier_pay_requests": SupplierPayRequest,
    "supplier_pay_quotes": SupplierPayQuote,
    "import_projects": ImportProject,
    "import_project_steps": ImportProjectStepData,
    "import_project_versions": ImportProjectVersion,
    "import_project_snapshots": ImportProjectSnapshot,
    "import_project_events": ImportProjectEvent,
    "import_project_files": ImportProjectFile,
    "source_messages": SourceMessage,
    "automation_runs": AutomationRun,
    "approval_requests": ApprovalRequest,
    "outbound_messages": OutboundMessage,
    "seo_opportunities": SEOOpportunity,
    "supplier_discovery_runs": SupplierDiscoveryRun,
    "supplier_leads": SupplierLead,
    "growth_attribution_events": GrowthAttributionEvent,
    "notifications": Notification,
    "audit_events": AuditEvent,
}


def configured_snapshot_path() -> Path:
    configured = os.getenv("SHIP_HOPPA_STORE_SNAPSHOT_PATH")
    return Path(configured).expanduser() if configured else DEFAULT_SNAPSHOT_PATH


def snapshot_enabled() -> bool:
    return os.getenv("SHIP_HOPPA_STORE_SNAPSHOT_ENABLED", "1").strip().lower() not in {"0", "false", "no"}


def store_to_snapshot(store: Store) -> Dict[str, Any]:
    collections: Dict[str, list[dict[str, Any]]] = {}
    for attr in STORE_COLLECTION_MODELS:
        collection = getattr(store, attr)
        collections[attr] = [item.model_dump(mode="json") for item in collection.values()]
    return {
        "version": SNAPSHOT_VERSION,
        "saved_at": datetime.utcnow().replace(microsecond=0).isoformat(),
        "counters": dict(store._counters),
        "collections": collections,
    }


def load_snapshot_into_store(store: Store, snapshot: Dict[str, Any], clear: bool = True) -> Store:
    if snapshot.get("version") != SNAPSHOT_VERSION:
        raise ValueError("Unsupported Ship Hoppa store snapshot version")
    if clear:
        for attr in STORE_COLLECTION_MODELS:
            getattr(store, attr).clear()
        store.idempotency_records.clear()

    collections = snapshot.get("collections", {})
    for attr, model in STORE_COLLECTION_MODELS.items():
        target = getattr(store, attr)
        target.clear()
        for raw_item in collections.get(attr, []):
            item = model(**raw_item)
            target[item.id] = item

    store._counters = defaultdict(int, {key: int(value) for key, value in snapshot.get("counters", {}).items()})
    return store


def save_store_snapshot(store: Store, path: Optional[Path] = None) -> Path:
    target = path or configured_snapshot_path()
    with SNAPSHOT_WRITE_LOCK:
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = store_to_snapshot(store)
        temporary = target.with_name(f"{target.name}.{os.getpid()}.tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(target)
    return target


def load_store_snapshot(store: Store, path: Optional[Path] = None) -> bool:
    target = path or configured_snapshot_path()
    if not target.exists():
        return False
    snapshot = json.loads(target.read_text(encoding="utf-8"))
    load_snapshot_into_store(store, snapshot)
    return True
