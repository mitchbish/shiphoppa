from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}


def test_system_health_reports_provider_readiness_and_sentinel_codes() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.get("/system/health", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "warning"
    assert {check["key"] for check in payload["checks"]} >= {
        "email_delivery",
        "sms_delivery",
        "email_ingestion",
        "supplier_pay",
        "shipping_data",
    }
    active_codes = {definition["code"] for definition in payload["active_error_codes"]}
    assert {"SH-3403", "SH-3502", "SH-4201"}.issubset(active_codes)

    registry = client.get("/sentinel/error-codes", headers=ADMIN_HEADERS)
    assert registry.status_code == 200
    assert any(definition["code"] == "SH-6101" for definition in registry.json())


def test_admin_can_queue_outbound_message_without_sending() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post(
        "/outbound-messages",
        headers=ADMIN_HEADERS,
        json={
            "recipient_type": "supplier",
            "recipient_id": "supplier-demo",
            "channel": "email",
            "template_key": "supplier_invite_v1",
            "subject": "Ship Hoppa can simplify overseas orders",
            "body_snapshot": "A safe preview of the supplier invite.",
            "compliance_basis": "Admin-approved contact using sourced business details.",
        },
    )

    assert response.status_code == 201
    message = response.json()
    assert message["status"] == "queued"
    assert message["provider"] == "resend"
    assert message["suppression_checked_at"]

    messages = client.get("/outbound-messages", headers=ADMIN_HEADERS)
    assert messages.status_code == 200
    assert messages.json()[0]["id"] == message["id"]
