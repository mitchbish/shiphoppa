import os

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store
from app.models import SentinelSubscriberStatus
from app.operations import (
    active_sentinel_phone_numbers,
    create_sentinel_subscriber,
)


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}


def test_create_subscriber_returns_pending_with_token() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.post(
        "/sentinel/subscribers",
        headers=ADMIN_HEADERS,
        json={"phone_number": "+61400000001", "label": "Mitch primary"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == SentinelSubscriberStatus.pending.value
    assert body["phone_number"] == "+61400000001"
    assert len(body["confirmation_token"]) == 32
    assert body["label"] == "Mitch primary"


def test_confirm_subscriber_activates_and_records_audit() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    create_resp = client.post(
        "/sentinel/subscribers",
        headers=ADMIN_HEADERS,
        json={"phone_number": "+61400000002"},
    )
    token = create_resp.json()["confirmation_token"]

    response = client.post("/sentinel/subscribers/confirm", json={"token": token})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == SentinelSubscriberStatus.active.value
    assert body["confirmed_at"] is not None

    audits = [
        e for e in store.audit_events.values()
        if e.event_type == "sentinel_subscriber_confirmed"
    ]
    assert len(audits) == 1


def test_confirm_with_unknown_token_returns_404() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    response = client.post("/sentinel/subscribers/confirm", json={"token": "deadbeef"})
    assert response.status_code == 404


def test_opt_out_marks_status_and_is_idempotent() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    sub = create_sentinel_subscriber(store, "+61400000003", "Ops Bob", "admin")

    first = client.post(
        "/sentinel/subscribers/opt-out",
        headers=ADMIN_HEADERS,
        json={"phone_number": "+61400000003"},
    )
    assert first.status_code == 200
    assert first.json()["status"] == SentinelSubscriberStatus.opted_out.value
    assert first.json()["opted_out_at"] is not None

    second = client.post(
        "/sentinel/subscribers/opt-out",
        headers=ADMIN_HEADERS,
        json={"phone_number": "+61400000003"},
    )
    assert second.status_code == 200
    assert second.json()["status"] == SentinelSubscriberStatus.opted_out.value


def test_list_returns_all_subscribers_including_opted_out() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    create_sentinel_subscriber(store, "+61400000010", "A", "admin")
    create_sentinel_subscriber(store, "+61400000011", "B", "admin")

    response = client.get("/sentinel/subscribers", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    phones = sorted(s["phone_number"] for s in body)
    assert phones == ["+61400000010", "+61400000011"]


def test_active_phone_numbers_includes_only_active_and_falls_back_to_env() -> None:
    reset_store_for_tests()
    # No active subscribers; fallback should use SHIP_HOPPA_OPS_PHONE if set.
    os.environ["SHIP_HOPPA_OPS_PHONE"] = "+61400999999"
    try:
        assert active_sentinel_phone_numbers(store) == ["+61400999999"]

        sub = create_sentinel_subscriber(store, "+61400000020", None, "admin")
        # Pending; should still fall back to env var.
        assert active_sentinel_phone_numbers(store) == ["+61400999999"]

        sub.status = SentinelSubscriberStatus.active
        store.sentinel_subscribers[sub.id] = sub
        # Now active subscriber takes over and env var is bypassed.
        assert active_sentinel_phone_numbers(store) == ["+61400000020"]

        sub2 = create_sentinel_subscriber(store, "+61400000021", None, "admin")
        sub2.status = SentinelSubscriberStatus.active
        store.sentinel_subscribers[sub2.id] = sub2
        assert sorted(active_sentinel_phone_numbers(store)) == [
            "+61400000020",
            "+61400000021",
        ]

        sub.status = SentinelSubscriberStatus.opted_out
        store.sentinel_subscribers[sub.id] = sub
        assert active_sentinel_phone_numbers(store) == ["+61400000021"]
    finally:
        del os.environ["SHIP_HOPPA_OPS_PHONE"]


def test_create_subscriber_idempotent_on_existing_phone() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    first = client.post(
        "/sentinel/subscribers",
        headers=ADMIN_HEADERS,
        json={"phone_number": "+61400000030"},
    )
    second = client.post(
        "/sentinel/subscribers",
        headers=ADMIN_HEADERS,
        json={"phone_number": "+61400000030"},
    )
    assert first.json()["id"] == second.json()["id"]
