from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def booking_payload(email: str = "project@example.com") -> dict:
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


def test_booking_creates_saved_import_project_workspace() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    booking_response = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload())
    assert booking_response.status_code == 201
    booking = booking_response.json()["booking"]

    project_response = client.get(f"/bookings/{booking['id']}/import-project", headers=IMPORTER_HEADERS)
    assert project_response.status_code == 200
    workspace = project_response.json()
    assert workspace["project"]["workflow_type"] == "mcl_shared_space"
    assert workspace["project"]["linked_shipment_ids"] == [booking["id"]]
    assert workspace["project"]["next_action"]
    assert {step["step_key"] for step in workspace["steps"]} >= {"intake", "shipping", "documents", "money"}
    assert workspace["versions"][0]["action"] == "project_created_from_booking"
    assert workspace["events"][0]["event_type"] == "project_created"


def test_source_message_ingestion_matches_existing_project() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload("inbox@example.com")).json()["booking"]

    message_response = client.post(
        "/source-messages",
        headers=IMPORTER_HEADERS,
        json={
            "source_type": "forwarded_email",
            "from_address": "sales@dongguan-home.example",
            "to_addresses": ["imports@shiphoppa.com"],
            "subject": f"Packing list for {booking['id']}",
            "body": "Attached is the packing list for the order.",
            "attachment_names": ["packing-list.xlsx"],
        },
    )
    assert message_response.status_code == 201
    message = message_response.json()
    assert message["matched_shipment_id"] == booking["id"]
    assert message["extraction_status"] == "matched"

    workspace = client.get(f"/bookings/{booking['id']}/import-project", headers=IMPORTER_HEADERS).json()
    assert any(item["id"] == message["id"] for item in workspace["source_messages"])
    assert any(run["automation_type"] == "match_message" for run in workspace["automation_runs"])
    assert any(event["event_type"] == "source_message_ingested" for event in workspace["events"])


def test_document_upload_adds_project_file_record() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    booking = client.post("/bookings", headers=IMPORTER_HEADERS, json=booking_payload("files@example.com")).json()["booking"]

    upload = client.post(
        f"/bookings/{booking['id']}/documents",
        headers=IMPORTER_HEADERS,
        json={"document_type": "commercial_invoice", "file_name": "invoice.pdf", "mime_type": "application/pdf"},
    )
    assert upload.status_code == 201

    workspace = client.get(f"/bookings/{booking['id']}/import-project", headers=IMPORTER_HEADERS).json()
    assert len(workspace["files"]) == 1
    project_file = workspace["files"][0]
    assert project_file["folder"] == "documents"
    assert project_file["filename"] == "invoice.pdf"
    assert project_file["storage_provider"] == "railway_postgres"
    assert project_file["backup_provider"] == "cloudflare_r2"
    assert project_file["backup_status"] == "pending"


def test_seo_opportunity_creates_guarded_supplier_discovery_loop() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post(
        "/growth/seo-opportunities",
        headers=ADMIN_HEADERS,
        json={
            "target_country": "china",
            "audience": "supplier",
            "category": "furniture",
            "city": "Foshan",
            "lane": "China to Australia",
            "keyword_cluster": ["Foshan furniture exporters", "Australia buyers"],
            "search_intent": "supplier_acquisition",
            "opportunity_score": 88,
            "page_type": "supplier_landing",
        },
    )
    assert response.status_code == 201
    opportunity = response.json()
    assert opportunity["status"] == "brief_ready"
    assert opportunity["related_supplier_discovery_run_id"]

    runs = client.get("/growth/supplier-discovery-runs", headers=ADMIN_HEADERS).json()
    assert runs[0]["run_status"] == "completed"
    assert runs[0]["compliance_review_required"] is True

    leads = client.get("/growth/supplier-leads", headers=ADMIN_HEADERS).json()
    assert len(leads) == 1
    assert leads[0]["outreach_status"] == "needs_human_review"
    assert leads[0]["contact_method_allowed"] == "none"
    assert "requires review" in leads[0]["compliance_basis"]

    summary = client.get("/summary", headers=ADMIN_HEADERS).json()
    assert summary["supplier_leads"] == 1
