from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def booking_payload(email: str = "po-clone-test@example.com") -> dict:
    return {
        "importer_company_name": "Bayside Build Co.",
        "importer_contact_name": "Alex Morgan",
        "importer_email": email,
        "supplier_name": "Dongguan Home Furnishings",
        "supplier_city": "Dongguan",
        "supplier_province": "Guangdong",
        "supplier_country": "China",
        "delivery_city": "Brisbane",
        "delivery_postcode": "4101",
        "delivery_country": "Australia",
        "cargo_description": "flat-pack furniture",
        "cargo_category": "furniture",
        "cbm_estimate": 20,
        "weight_kg_estimate": 3800,
        "cargo_ready_date_earliest": date.today().isoformat(),
        "cargo_ready_date_latest": (date.today() + timedelta(days=5)).isoformat(),
        "service_level": "standard",
    }


def create_po(client: TestClient, booking_id: str, reference: str = "PO-2026-Q3-001") -> dict:
    response = client.post(
        "/purchase-orders",
        headers=IMPORTER_HEADERS,
        json={
            "booking_id": booking_id,
            "order_reference": reference,
            "buyer_company_name": "Bayside Build Co.",
            "supplier_name": "Dongguan Home Furnishings",
            "supplier_contact_email": "sales@example.cn",
            "product_summary": "Vanity tops, mirrors, bathroom fittings",
            "incoterm": "FOB",
            "currency": "USD",
            "goods_value": 18000,
            "deposit_amount": 5400,
            "balance_amount": 12600,
            "production_due_date": (date.today() + timedelta(days=30)).isoformat(),
            "cargo_ready_target_date": (date.today() + timedelta(days=45)).isoformat(),
        },
    )
    assert response.status_code == 201
    return response.json()


def test_clone_purchase_order_copies_metadata_and_resets_dates() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload()).json()["booking"]
    source = create_po(client, booking["id"], "PO-2026-Q3-ORIGINAL")

    response = client.post(
        f"/purchase-orders/{source['id']}/clone",
        headers=IMPORTER_HEADERS,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] != source["id"]
    assert body["order_reference"] == "Copy of PO-2026-Q3-ORIGINAL"
    assert body["supplier_name"] == source["supplier_name"]
    assert body["product_summary"] == source["product_summary"]
    assert body["goods_value"] == source["goods_value"]
    # Reset fields:
    assert body["booking_id"] is None
    assert body["production_due_date"] is None
    assert body["cargo_ready_target_date"] is None
    assert body["status"] == "order_confirmed"


def test_clone_with_explicit_new_reference() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload()).json()["booking"]
    source = create_po(client, booking["id"])

    response = client.post(
        f"/purchase-orders/{source['id']}/clone?new_order_reference=PO-Q4-FRESH",
        headers=IMPORTER_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["order_reference"] == "PO-Q4-FRESH"


def test_clone_unknown_purchase_order_returns_404() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post(
        "/purchase-orders/PO-9999/clone",
        headers=IMPORTER_HEADERS,
    )
    assert response.status_code == 404


def test_clone_writes_audit_event_and_version() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload()).json()["booking"]
    source = create_po(client, booking["id"])

    audit_before = len(store.audit_events)
    versions_before = len(store.import_project_versions)
    client.post(
        f"/purchase-orders/{source['id']}/clone",
        headers=IMPORTER_HEADERS,
    )
    assert len(store.audit_events) > audit_before
    assert len(store.import_project_versions) > versions_before


def test_clone_links_to_target_project_when_specified() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload()).json()["booking"]
    source = create_po(client, booking["id"])

    target_project = client.post(
        "/import-projects",
        headers=IMPORTER_HEADERS,
        json={"title": "Q4 Reorder Plan"},
    ).json()

    response = client.post(
        f"/purchase-orders/{source['id']}/clone?target_project_id={target_project['id']}",
        headers=IMPORTER_HEADERS,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["import_project_id"] == target_project["id"]
