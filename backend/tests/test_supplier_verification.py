from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store
from app.models import (
    ContactMethod,
    SupplierLead,
    SupplierLeadSource,
    SupplierOutreachStatus,
    SupplierVerificationStatus,
)


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}


def seed_supplier_lead() -> SupplierLead:
    timestamp = datetime.utcnow()
    lead = SupplierLead(
        id=store.next_id("LEAD"),
        company_name="Foshan Marble Works",
        country="China",
        city="Foshan",
        product_categories=["countertops"],
        discovery_source=SupplierLeadSource.supplier_website,
        discovery_source_url="https://example.com/factory/foshan",
        public_contact_source_url="https://example.com/factory/foshan/contact",
        public_contact_captured_at=timestamp,
        public_email="sales@example.com",
        contact_method_allowed=ContactMethod.email,
        outreach_status=SupplierOutreachStatus.discovered,
        fit_reason="Bulky goods, China-to-AU lane",
        compliance_basis="Public website with contact details",
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.supplier_leads[lead.id] = lead
    return lead


def test_verify_supplier_lead_sets_verified_status_and_records_actor() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    lead = seed_supplier_lead()

    response = client.patch(
        f"/growth/supplier-leads/{lead.id}/verification",
        headers=ADMIN_HEADERS,
        json={"verification_status": "verified", "verification_notes": "Confirmed via Alibaba badge"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verification_status"] == "verified"
    assert body["verification_notes"] == "Confirmed via Alibaba badge"
    assert body["verified_at"] is not None
    assert body["verified_by"] == "dev-admin"


def test_reject_supplier_lead_sets_do_not_contact() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    lead = seed_supplier_lead()

    response = client.patch(
        f"/growth/supplier-leads/{lead.id}/verification",
        headers=ADMIN_HEADERS,
        json={"verification_status": "rejected", "verification_notes": "Not a real factory"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verification_status"] == "rejected"
    assert body["do_not_contact"] is True


def test_restrict_status_does_not_set_do_not_contact() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    lead = seed_supplier_lead()

    response = client.patch(
        f"/growth/supplier-leads/{lead.id}/verification",
        headers=ADMIN_HEADERS,
        json={"verification_status": "restricted"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verification_status"] == "restricted"
    assert body["do_not_contact"] is False


def test_verify_writes_audit_event() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    lead = seed_supplier_lead()
    audit_before = len(store.audit_events)

    client.patch(
        f"/growth/supplier-leads/{lead.id}/verification",
        headers=ADMIN_HEADERS,
        json={"verification_status": "verified"},
    )

    new_events = [
        evt for evt in store.audit_events.values()
        if evt.event_type == "supplier_lead_verification_updated" and evt.entity_id == lead.id
    ]
    assert len(new_events) == 1
    assert new_events[0].metadata["new_status"] == "verified"
    assert new_events[0].metadata["previous_status"] == "unverified"
    assert len(store.audit_events) > audit_before


def test_unknown_lead_returns_404() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.patch(
        "/growth/supplier-leads/LEAD-9999/verification",
        headers=ADMIN_HEADERS,
        json={"verification_status": "verified"},
    )
    assert response.status_code == 404


def test_supplier_lead_default_verification_status_is_unverified() -> None:
    reset_store_for_tests()
    lead = seed_supplier_lead()
    assert lead.verification_status == SupplierVerificationStatus.unverified
