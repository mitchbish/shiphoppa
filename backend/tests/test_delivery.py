from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}
IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def test_delivery_plan_defaults_and_update() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.get("/bookings/BKG-ANCHOR/delivery-plan", headers=IMPORTER_HEADERS)
    assert response.status_code == 200
    plan = response.json()
    assert plan["booking_id"] == "BKG-ANCHOR"
    assert plan["status"] == "blocked_by_release"
    assert "Brisbane" in plan["destination_address"]

    update_response = client.put(
        "/bookings/BKG-ANCHOR/delivery-plan",
        headers=IMPORTER_HEADERS,
        json={
            "destination_address": "12 Warehouse Road, Brisbane QLD 4101",
            "destination_contact_name": "Warehouse dock",
            "equipment_required": ["forklift", "tail_lift"],
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["destination_address"] == "12 Warehouse Road, Brisbane QLD 4101"
    assert updated["equipment_required"] == ["forklift", "tail_lift"]


def test_delivery_booking_is_blocked_until_release_clear() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    plan = client.get("/bookings/BKG-ANCHOR/delivery-plan", headers=IMPORTER_HEADERS).json()
    response = client.post(f"/delivery-plans/{plan['id']}/book", headers=IMPORTER_HEADERS)
    assert response.status_code == 409
    assert "cannot be booked" in response.json()["detail"]

    release_response = client.get("/bookings/BKG-ANCHOR/release-status", headers=IMPORTER_HEADERS)
    assert release_response.status_code == 200
    assert release_response.json()["can_release"] is False


def test_delivery_can_be_marked_delivered_by_importer() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    plan = client.get("/bookings/BKG-ANCHOR/delivery-plan", headers=IMPORTER_HEADERS).json()
    delivered_response = client.post(f"/delivery-plans/{plan['id']}/mark-delivered", headers=IMPORTER_HEADERS)
    assert delivered_response.status_code == 200
    delivered = delivered_response.json()
    assert delivered["status"] == "delivered"
    assert delivered["delivered_at"] is not None

    bookings = client.get("/bookings", headers=ADMIN_HEADERS).json()
    anchor = next(booking for booking in bookings if booking["id"] == "BKG-ANCHOR")
    assert anchor["status"] == "delivered"
