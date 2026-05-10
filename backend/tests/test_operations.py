from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def booking_payload(email: str = "ops@example.com") -> dict:
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
        "cargo_description": "flat-pack vanities and bathroom cabinets",
        "cargo_category": "furniture",
        "cbm_estimate": 20,
        "weight_kg_estimate": 3800,
        "cargo_ready_date_earliest": date.today().isoformat(),
        "cargo_ready_date_latest": (date.today() + timedelta(days=5)).isoformat(),
        "service_level": "standard",
    }


def create_booking(client: TestClient, email: str = "ops@example.com") -> dict:
    response = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload(email))
    assert response.status_code == 201
    return response.json()["booking"]


def test_document_checklist_upload_and_approval() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client)

    checklist = client.get(f"/bookings/{booking['id']}/checklist", headers=IMPORTER_HEADERS).json()
    assert checklist["checklist_status"] == "incomplete"
    assert "commercial_invoice" in checklist["missing_document_types"]

    upload = client.post(
        f"/bookings/{booking['id']}/documents",
        headers=IMPORTER_HEADERS,
        json={
            "document_type": "commercial_invoice",
            "file_name": "invoice.pdf",
            "mime_type": "application/pdf",
        },
    )
    assert upload.status_code == 201
    assert upload.json()["status"] == "uploaded"

    approve = client.post(f"/documents/{upload.json()['id']}/approve", headers=ADMIN_HEADERS, json={"reason": "Looks good"})
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"


def test_tracking_events_auto_and_manual() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "events@example.com")

    initial_events = client.get(f"/bookings/{booking['id']}/events", headers=IMPORTER_HEADERS).json()
    assert any(event["stage"] == "booking_submitted" for event in initial_events)

    add_event = client.post(
        f"/bookings/{booking['id']}/events",
        headers=ADMIN_HEADERS,
        json={
            "stage": "warehouse_received",
            "label": "Warehouse received cargo",
            "occurred_at": date.today().isoformat() + "T09:00:00",
            "source_type": "warehouse_event",
            "source_name": "Foshan warehouse",
            "confidence": "confirmed",
        },
    )
    assert add_event.status_code == 201
    events = client.get(f"/bookings/{booking['id']}/events", headers=IMPORTER_HEADERS).json()
    assert any(event["stage"] == "warehouse_received" for event in events)


def test_sailing_schedule_and_preferred_sailing_booking() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    sailings = client.get("/sailings", headers=IMPORTER_HEADERS)
    assert sailings.status_code == 200
    selected = sailings.json()[0]
    assert selected["available_cbm"] > 0
    assert len(selected["route_waypoints"]) >= 2
    assert selected["route_geometry_source_name"] == "Ship Hoppa route library"

    payload = {
        **booking_payload("sailing-choice@example.com"),
        "preferred_sailing_option_id": selected["sailing_option_id"],
        "preferred_container_id": selected["container_id"],
    }
    response = client.post("/bookings", headers=IMPORTER_HEADERS, json=payload)
    assert response.status_code == 201
    assert response.json()["container"]["target_sailing_date"] == selected["etd"]


def test_supplier_portal_hides_pricing_and_accepts_updates() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "supplier@example.com")

    link_response = client.post("/supplier-links", headers=ADMIN_HEADERS, json={"booking_id": booking["id"]})
    assert link_response.status_code == 201
    token = link_response.json()["token"]

    portal = client.get(f"/supplier/{token}")
    assert portal.status_code == 200
    assert "total_cost_usd" not in portal.json()["booking"]

    ready = client.post(
        f"/supplier/{token}/ready",
        json={"cargo_ready_date_latest": (date.today() + timedelta(days=4)).isoformat()},
    )
    assert ready.status_code == 200
    assert ready.json()["booking"]["cargo_ready_date_latest"] == (date.today() + timedelta(days=4)).isoformat()

    upload = client.post(
        f"/supplier/{token}/documents",
        json={"document_type": "packing_list", "file_name": "supplier-pack-list.pdf"},
    )
    assert upload.status_code == 201
    assert upload.json()["uploaded_by_id"] == "supplier-portal"


def test_invoice_payment_customs_and_release_holds() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = create_booking(client, "release@example.com")
    booking_id = booking["id"]

    invoice = client.get(f"/bookings/{booking_id}/invoice", headers=IMPORTER_HEADERS).json()
    assert invoice["status"] == "issued"
    assert invoice["total_usd"] > booking["total_cost_usd"]
    invoice_sources = {line["source"] for line in invoice["line_items"]}
    assert "platform_fee" not in invoice_sources
    assert "urgency_fee" not in invoice_sources
    service_line = next(line for line in invoice["line_items"] if line["source"].startswith("ship_hoppa_service_fee_"))
    assert service_line["amount_usd"] == booking["platform_fee_usd"] + booking["urgency_fee_usd"]

    for document_type in client.get(f"/bookings/{booking_id}/checklist", headers=IMPORTER_HEADERS).json()["missing_document_types"]:
        doc = client.post(
            f"/bookings/{booking_id}/documents",
            headers=IMPORTER_HEADERS,
            json={"document_type": document_type, "file_name": f"{document_type}.pdf"},
        ).json()
        client.post(f"/documents/{doc['id']}/approve", headers=ADMIN_HEADERS, json={"reason": "Approved"})

    paid = client.post(f"/invoices/{invoice['id']}/mark-paid", headers=ADMIN_HEADERS)
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"

    customs = client.put(
        f"/bookings/{booking_id}/customs-profile",
        headers=ADMIN_HEADERS,
        json={"customs_status": "cleared", "goods_value_usd": 12000},
    )
    assert customs.status_code == 200
    assert customs.json()["landed_cost_estimate_usd"] > 12000

    release = client.get(f"/bookings/{booking_id}/release-status", headers=IMPORTER_HEADERS)
    assert release.status_code == 200
    assert release.json()["can_release"] is True
