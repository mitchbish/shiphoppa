from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


ADMIN_HEADERS = {"Authorization": "Bearer shiphoppa-admin-dev"}


def test_post_attribution_event_creates_record() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post(
        "/growth/attribution-events",
        headers=ADMIN_HEADERS,
        json={
            "event_type": "supplier_signed_up",
            "source": "supplier_referral_link",
            "channel": "wechat",
            "template_key": "supplier_invite_v1",
            "category": "furniture",
            "region": "China",
            "value_usd": 0,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["event_type"] == "supplier_signed_up"
    assert body["source"] == "supplier_referral_link"
    assert body["id"] in store.growth_attribution_events


def test_get_attribution_events_filters_by_source() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    client.post(
        "/growth/attribution-events",
        headers=ADMIN_HEADERS,
        json={"event_type": "lead_discovered", "source": "alibaba"},
    )
    client.post(
        "/growth/attribution-events",
        headers=ADMIN_HEADERS,
        json={"event_type": "lead_discovered", "source": "made_in_china"},
    )

    response = client.get("/growth/attribution-events?source=alibaba", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert all(event["source"] == "alibaba" for event in body)
    assert len(body) >= 1


def test_get_attribution_events_filters_by_event_type() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    client.post(
        "/growth/attribution-events",
        headers=ADMIN_HEADERS,
        json={"event_type": "lead_discovered", "source": "alibaba"},
    )
    client.post(
        "/growth/attribution-events",
        headers=ADMIN_HEADERS,
        json={"event_type": "shipment_created", "source": "alibaba"},
    )

    response = client.get("/growth/attribution-events?event_type=shipment_created", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert all(event["event_type"] == "shipment_created" for event in body)


def test_attribution_summary_groups_by_source_and_sums_value() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    for value in [1000.0, 2500.0]:
        client.post(
            "/growth/attribution-events",
            headers=ADMIN_HEADERS,
            json={
                "event_type": "revenue_recognised",
                "source": "supplier_referral_link",
                "value_usd": value,
            },
        )
    client.post(
        "/growth/attribution-events",
        headers=ADMIN_HEADERS,
        json={"event_type": "revenue_recognised", "source": "seo_blog", "value_usd": 500.0},
    )

    response = client.get("/growth/attribution-summary?group_by=source", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["group_by"] == "source"
    sources = {row["group_key"]: row for row in body["rows"]}
    assert sources["supplier_referral_link"]["event_count"] == 2
    assert sources["supplier_referral_link"]["total_value_usd"] == 3500.0
    assert sources["seo_blog"]["total_value_usd"] == 500.0
    assert body["total_events"] == 3
    assert body["total_value_usd"] == 4000.0


def test_attribution_summary_invalid_group_by_returns_400() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.get("/growth/attribution-summary?group_by=foo", headers=ADMIN_HEADERS)
    assert response.status_code == 400


def test_attribution_summary_groups_by_template_key() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    client.post(
        "/growth/attribution-events",
        headers=ADMIN_HEADERS,
        json={
            "event_type": "lead_contacted",
            "source": "outbound",
            "template_key": "alibaba_intro_v2",
        },
    )

    response = client.get("/growth/attribution-summary?group_by=template_key", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    rows = {row["group_key"]: row for row in body["rows"]}
    assert "alibaba_intro_v2" in rows
    assert rows["alibaba_intro_v2"]["event_count"] == 1


def test_attribution_filter_by_date_range() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    client.post(
        "/growth/attribution-events",
        headers=ADMIN_HEADERS,
        json={"event_type": "lead_discovered", "source": "alibaba"},
    )

    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    response = client.get(
        f"/growth/attribution-events?since={yesterday}&until={today}",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1
