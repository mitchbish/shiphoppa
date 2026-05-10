from datetime import timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store
from app.models import (
    ContactMethod,
    GrowthAttributionEventType,
    SupplierLead,
    SupplierLeadSource,
    SupplierOutreachStatus,
    SupplierProfileClaimStatus,
    SupplierVerificationStatus,
)
from app.operations import now_utc


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}


def _seed_lead(verification: SupplierVerificationStatus = SupplierVerificationStatus.verified) -> SupplierLead:
    timestamp = now_utc()
    lead = SupplierLead(
        id=store.next_id("LEAD"),
        company_name="Foshan Test Co.",
        country="China",
        city="Foshan",
        product_categories=["lighting"],
        discovery_source=SupplierLeadSource.seo_engine,
        discovery_source_url="https://example.com",
        company_website="https://example.com",
        public_contact_source_url="https://example.com/contact",
        public_contact_captured_at=timestamp,
        preferred_language="en",
        exports_to_regions=["Australia"],
        overseas_buyer_signals=["test"],
        bulky_goods_fit=True,
        lead_score=80,
        fit_reason="testing",
        compliance_basis="testing",
        contact_method_allowed=ContactMethod.email,
        outreach_status=SupplierOutreachStatus.contacted,
        verification_status=verification,
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.supplier_leads[lead.id] = lead
    return lead


def test_create_claim_link_requires_verified_lead() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    lead = _seed_lead(SupplierVerificationStatus.unverified)

    response = client.post(
        f"/growth/supplier-leads/{lead.id}/claim-link",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 400
    assert "not verified" in response.json()["detail"].lower()


def test_create_claim_link_returns_pending_for_verified_lead() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    lead = _seed_lead()

    response = client.post(
        f"/growth/supplier-leads/{lead.id}/claim-link",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["lead_id"] == lead.id
    assert body["status"] == SupplierProfileClaimStatus.pending.value
    assert len(body["token"]) == 32


def test_create_claim_link_idempotent_returns_same_pending() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    lead = _seed_lead()

    first = client.post(
        f"/growth/supplier-leads/{lead.id}/claim-link",
        headers=ADMIN_HEADERS,
    ).json()
    second = client.post(
        f"/growth/supplier-leads/{lead.id}/claim-link",
        headers=ADMIN_HEADERS,
    ).json()
    assert first["id"] == second["id"]
    assert first["token"] == second["token"]


def test_get_supplier_claim_returns_claim_and_lead() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    lead = _seed_lead()
    claim_resp = client.post(
        f"/growth/supplier-leads/{lead.id}/claim-link",
        headers=ADMIN_HEADERS,
    ).json()

    response = client.get(f"/api/supplier-claim/{claim_resp['token']}")
    assert response.status_code == 200
    body = response.json()
    assert body["claim"]["id"] == claim_resp["id"]
    assert body["lead"]["id"] == lead.id


def test_get_supplier_claim_404_for_unknown_token() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.get("/api/supplier-claim/notarealtoken")
    assert response.status_code == 404


def test_accept_supplier_claim_marks_lead_onboarded_and_records_growth() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    lead = _seed_lead()
    claim_resp = client.post(
        f"/growth/supplier-leads/{lead.id}/claim-link",
        headers=ADMIN_HEADERS,
    ).json()

    response = client.post(
        f"/api/supplier-claim/{claim_resp['token']}/accept",
        json={"contact_email": "owner@example.com", "contact_name": "Wei Lin"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["claim"]["status"] == SupplierProfileClaimStatus.claimed.value
    assert body["claim"]["claimed_by_email"] == "owner@example.com"
    assert body["claim"]["claimed_contact_name"] == "Wei Lin"

    refreshed = store.supplier_leads[lead.id]
    assert refreshed.outreach_status == SupplierOutreachStatus.onboarded
    assert refreshed.public_email == "owner@example.com"

    growth_events = [
        e for e in store.growth_attribution_events.values()
        if e.event_type == GrowthAttributionEventType.supplier_signed_up
        and e.supplier_lead_id == lead.id
    ]
    assert len(growth_events) == 1


def test_accept_supplier_claim_idempotent_does_not_re_emit_growth_event() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    lead = _seed_lead()
    token = client.post(
        f"/growth/supplier-leads/{lead.id}/claim-link",
        headers=ADMIN_HEADERS,
    ).json()["token"]

    first = client.post(
        f"/api/supplier-claim/{token}/accept",
        json={"contact_email": "first@example.com", "contact_name": "First"},
    )
    second = client.post(
        f"/api/supplier-claim/{token}/accept",
        json={"contact_email": "second@example.com", "contact_name": "Second"},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    growth_events = [
        e for e in store.growth_attribution_events.values()
        if e.event_type == GrowthAttributionEventType.supplier_signed_up
        and e.supplier_lead_id == lead.id
    ]
    assert len(growth_events) == 1


def test_accept_returns_410_for_expired_claim() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    lead = _seed_lead()
    claim_resp = client.post(
        f"/growth/supplier-leads/{lead.id}/claim-link",
        headers=ADMIN_HEADERS,
    ).json()
    claim_id = claim_resp["id"]
    claim_obj = store.supplier_profile_claims[claim_id]
    claim_obj.expires_at = now_utc() - timedelta(days=1)
    store.supplier_profile_claims[claim_id] = claim_obj

    response = client.post(
        f"/api/supplier-claim/{claim_resp['token']}/accept",
        json={"contact_email": "late@example.com", "contact_name": "Late"},
    )
    assert response.status_code == 410
