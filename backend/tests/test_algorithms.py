from datetime import date, timedelta

from app.algorithms import add_business_days, commit_container, confirm_booking, rank_carrier_options, release_reasons, submit_booking
from app.models import BookingCreate, CargoCategory, CommitContainerRequest, DeliveryMode, ServiceLevel, SourceConfidence, SourceType
from app.route_geometry import sea_route_waypoints
from app.seed import seed_data
from app.store import Store


def build_store() -> Store:
    store = Store()
    seed_data(store)
    return store


def test_light_furniture_matches_anchor_container() -> None:
    store = build_store()
    result = submit_booking(
        store,
        BookingCreate(
            importer_company_name="Bayside Cabinets",
            importer_contact_name="Ari Chan",
            importer_email="ari@example.com",
            supplier_city="Dongguan",
            supplier_province="Guangdong",
            supplier_country="China",
            delivery_city="Brisbane",
            delivery_postcode="4101",
            delivery_country="Australia",
            cargo_category=CargoCategory.furniture,
            cargo_description="flat-pack vanities",
            cbm_estimate=20,
            weight_kg_estimate=3800,
            cargo_ready_date_earliest=date.today(),
            cargo_ready_date_latest=date.today() + timedelta(days=4),
            service_level=ServiceLevel.standard,
        ),
    )

    assert result.container is not None
    assert result.container.id == "CON-FOUNDING"
    assert result.booking.match_score is not None
    assert result.booking.match_score >= 60
    assert result.booking.delivery_mode == DeliveryMode.ship_hoppa_pickup
    assert result.booking.pickup_fee_usd == 95
    assert result.booking.warehouse_receipt_cutoff == result.container.warehouse_receipt_cutoff_date
    assert result.booking.total_cost_usd is not None


def test_no_lane_returns_route_notification() -> None:
    store = build_store()
    result = submit_booking(
        store,
        BookingCreate(
            importer_company_name="WA Imports",
            importer_contact_name="Jo Taylor",
            importer_email="jo@example.com",
            supplier_city="Istanbul",
            supplier_country="Turkey",
            delivery_city="Perth",
            delivery_postcode="6000",
            delivery_country="Australia",
            cargo_category=CargoCategory.homewares,
            cbm_estimate=8,
            weight_kg_estimate=1400,
            cargo_ready_date_earliest=date.today(),
            cargo_ready_date_latest=date.today() + timedelta(days=7),
            service_level=ServiceLevel.standard,
        ),
    )

    assert result.container is None
    assert result.booking.lane_id is None
    assert result.notification.trigger == "no_match_found"


def test_carrier_ranking_returns_top_three() -> None:
    store = build_store()
    options = rank_carrier_options(store, "CON-FOUNDING")

    assert len(options) >= 3
    assert options[0].score >= options[-1].score
    assert options[0].total_all_in_usd > 0
    assert len(options[0].route_waypoints) >= 2


def test_release_reason_when_weight_threshold_reached() -> None:
    store = build_store()
    submit_booking(
        store,
        BookingCreate(
            importer_company_name="Tile Barn",
            importer_contact_name="Sam Singh",
            importer_email="sam@example.com",
            supplier_city="Foshan",
            supplier_province="Guangdong",
            supplier_country="China",
            delivery_city="Brisbane",
            delivery_postcode="4006",
            delivery_country="Australia",
            cargo_category=CargoCategory.hardware,
            cargo_description="compact metal fittings",
            cbm_estimate=4,
            weight_kg_estimate=2600,
            cargo_ready_date_earliest=date.today(),
            cargo_ready_date_latest=date.today() + timedelta(days=3),
            service_level=ServiceLevel.standard,
        ),
    )

    reasons = release_reasons(store, store.containers["CON-FOUNDING"])
    assert any("Weight fill" in reason for reason in reasons)


def test_commit_updates_sailing_and_future_cutoff() -> None:
    store = build_store()
    result = commit_container(store, "CON-FOUNDING")

    container = store.containers["CON-FOUNDING"]
    assert result.released is True
    assert result.selected_carrier is not None
    assert container.target_sailing_date == result.selected_carrier.sailing_date
    assert container.carrier_cutoff_date >= date.today()
    assert container.warehouse_receipt_cutoff_date == add_business_days(container.carrier_cutoff_date, -2)
    assert container.sailing_source_type == SourceType.forwarder_confirmation
    assert container.sailing_source_confidence == SourceConfidence.confirmed
    assert container.container_cost_usd == result.selected_carrier.total_all_in_usd
    assert container.route_waypoints == result.selected_carrier.route_waypoints


def test_seeded_route_library_covers_global_corridors() -> None:
    route_pairs = [
        ("Yantian", "Brisbane"),
        ("Shanghai", "Los Angeles"),
        ("Ningbo", "New York"),
        ("Yantian", "Rotterdam"),
        ("Rotterdam", "Brisbane"),
        ("Jebel Ali", "Rotterdam"),
        ("Los Angeles", "Sydney"),
    ]

    for origin, destination in route_pairs:
        route = sea_route_waypoints(origin, destination)
        assert len(route) >= 3
        assert route[0].lat != route[-1].lat


def test_late_booking_skips_founding_container_for_next_feasible_sailing() -> None:
    store = build_store()
    founding = store.containers["CON-FOUNDING"]
    late_ready = add_business_days(founding.warehouse_receipt_cutoff_date, -3) + timedelta(days=2)

    result = submit_booking(
        store,
        BookingCreate(
            importer_company_name="Late Cabinets",
            importer_contact_name="Mel Tan",
            importer_email="late@example.com",
            supplier_city="Dongguan",
            supplier_province="Guangdong",
            supplier_country="China",
            delivery_city="Brisbane",
            delivery_postcode="4101",
            delivery_country="Australia",
            cargo_category=CargoCategory.furniture,
            cbm_estimate=12,
            weight_kg_estimate=2500,
            cargo_ready_date_earliest=late_ready - timedelta(days=1),
            cargo_ready_date_latest=late_ready,
            service_level=ServiceLevel.standard,
        ),
    )

    assert result.container is not None
    assert result.container.id != "CON-FOUNDING"
    assert result.booking.feasibility_status != "misses_cutoff"
    assert result.booking.latest_supplier_ready_date >= result.booking.cargo_ready_date_latest


def test_unknown_supplier_city_requires_admin_review_and_blocks_confirmation() -> None:
    store = build_store()
    result = submit_booking(
        store,
        BookingCreate(
            importer_company_name="Review Imports",
            importer_contact_name="Nina Park",
            importer_email="review@example.com",
            supplier_city="Huizhou",
            supplier_province="Guangdong",
            supplier_country="China",
            delivery_city="Brisbane",
            delivery_postcode="4101",
            delivery_country="Australia",
            cargo_category=CargoCategory.homewares,
            cbm_estimate=8,
            weight_kg_estimate=1400,
            cargo_ready_date_earliest=date.today(),
            cargo_ready_date_latest=date.today() + timedelta(days=5),
            service_level=ServiceLevel.standard,
        ),
    )

    assert result.booking.admin_review_required is True
    assert result.booking.feasibility_status == "admin_review"
    try:
        confirm_booking(store, result.booking.id)
    except ValueError as exc:
        assert "operations review" in str(exc)
    else:
        raise AssertionError("admin review booking should not confirm")


def test_confirmed_cutoff_override_becomes_container_source_of_truth() -> None:
    store = build_store()
    options = rank_carrier_options(store, "CON-FOUNDING")
    override_gate_in = options[0].carrier_gate_in_cutoff_date + timedelta(days=1)
    result = commit_container(
        store,
        "CON-FOUNDING",
        CommitContainerRequest(
            sailing_option_id=options[0].sailing_option_id,
            confirmed_carrier_cutoff_date=override_gate_in,
            confirmed_shipping_instructions_cutoff_date=override_gate_in - timedelta(days=1),
            confirmed_vgm_cutoff_date=override_gate_in,
            source_reference="FWD-CONF-123",
        ),
    )

    container = store.containers["CON-FOUNDING"]
    assert result.released is True
    assert container.carrier_cutoff_date == override_gate_in
    assert container.warehouse_receipt_cutoff_date == add_business_days(override_gate_in, -2)
    assert container.sailing_source_reference == "FWD-CONF-123"
    assert container.sailing_source_confidence == SourceConfidence.confirmed
