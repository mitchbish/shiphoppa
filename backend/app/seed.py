from datetime import date, timedelta

from .algorithms import apply_feasibility_to_booking, evaluate_container_feasibility, next_weekday, now_utc, recalculate_container
from .models import (
    Booking,
    BookingStatus,
    CargoCategory,
    CarrierService,
    ConsolidationWarehouse,
    Container,
    ContainerStatus,
    Coordinates,
    Importer,
    Lane,
    SailingOption,
    ServiceLevel,
    SourceConfidence,
    SourceType,
)
from .route_geometry import sea_route_waypoints
from .store import Store


def upcoming_weekdays(weekday: int, count: int = 5) -> list:
    today = date.today()
    days = (weekday - today.weekday()) % 7
    if days == 0:
        days = 7
    first = today + timedelta(days=days)
    return [first + timedelta(days=7 * index) for index in range(count)]


def seed_data(store: Store) -> None:
    timestamp = now_utc()
    lane = Lane(
        id="LANE-SCN-BNE",
        name="South China to Brisbane",
        origin_region="Guangdong, China",
        origin_ports=["Yantian", "Shekou", "Nansha"],
        destination_port="Brisbane",
        destination_region="Southeast Queensland",
        container_type="40HC",
        practical_cbm_limit=55,
        road_weight_limit_kg=20000,
        max_shippers_per_container=5,
        typical_transit_days_min=16,
        typical_transit_days_max=22,
        sailing_frequency="weekly",
        base_container_cost_usd=3000,
        platform_fee_per_booking_usd=150,
        max_wait_days=21,
        cbm_release_threshold=0.80,
        weight_release_threshold=0.85,
        cutoff_days_before_sailing=5,
        warehouse_receipt_cutoff_days_before_sailing=6,
        origin_max_pickup_radius_km=200,
        pickup_fee_usd=95,
        priority_handling_fee_usd=75,
        rush_handling_fee_usd=150,
        cargo_restrictions=[
            "no food",
            "no perishables",
            "no hazmat",
            "no live plants/animals",
            "ISPM 15 required for all timber packaging",
        ],
        active=True,
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.lanes[lane.id] = lane

    warehouse = ConsolidationWarehouse(
        id="WH-FOSHAN",
        lane_id=lane.id,
        name="Ship Hoppa Foshan Warehouse",
        city="Foshan",
        country="China",
        coordinates=Coordinates(lat=23.0215, lng=113.1214),
        address="Warehouse 8, Jihua Logistics Park, Foshan, Guangdong, China",
        contact_name="Li Wei",
        contact_phone="+86 20 5555 0101",
        contact_email="warehouse.foshan@shiphoppa.example",
        operating_hours="Mon-Sat 8am-6pm",
        max_containers_per_week=4,
        handling_fee_per_container_usd=250,
        active=True,
    )
    store.warehouses[warehouse.id] = warehouse

    carrier_services = [
        CarrierService(
            id="CS-COSCO-AAX3",
            lane_id=lane.id,
            carrier_name="COSCO",
            service_name="AAX3 - Asia Australia Express",
            departure_port="Yantian",
            arrival_port="Brisbane",
            departure_day_of_week="Wednesday",
            transit_days=18,
            direct_or_transhipment="direct",
            rate_40hc_usd=2800,
            thc_origin_usd=150,
            thc_destination_usd=200,
            documentation_fee_usd=75,
            fuel_surcharge_usd=100,
            peak_season_surcharge_usd=0,
            total_all_in_usd=3325,
            empty_depot_city="Shenzhen",
            empty_depot_coordinates=Coordinates(lat=22.5431, lng=114.0579),
            drayage_cost_to_warehouse_usd=230,
            drayage_cost_to_port_usd=180,
            schedule_reliability_pct=82,
            average_delay_days=1.4,
            next_available_sailings=upcoming_weekdays(2),
            booking_cutoff_days_before=5,
            rates_updated_at=timestamp,
            created_at=timestamp,
            updated_at=timestamp,
        ),
        CarrierService(
            id="CS-MSC-DRAGON",
            lane_id=lane.id,
            carrier_name="MSC",
            service_name="Dragon - Far East Australia",
            departure_port="Shekou",
            arrival_port="Brisbane",
            departure_day_of_week="Friday",
            transit_days=21,
            direct_or_transhipment="transhipment via Singapore",
            rate_40hc_usd=2500,
            thc_origin_usd=140,
            thc_destination_usd=190,
            documentation_fee_usd=80,
            fuel_surcharge_usd=120,
            peak_season_surcharge_usd=0,
            total_all_in_usd=3030,
            empty_depot_city="Shenzhen",
            empty_depot_coordinates=Coordinates(lat=22.5431, lng=114.0579),
            drayage_cost_to_warehouse_usd=220,
            drayage_cost_to_port_usd=175,
            schedule_reliability_pct=78,
            average_delay_days=2.1,
            next_available_sailings=upcoming_weekdays(4),
            booking_cutoff_days_before=5,
            rates_updated_at=timestamp,
            created_at=timestamp,
            updated_at=timestamp,
        ),
        CarrierService(
            id="CS-ONE-CA2",
            lane_id=lane.id,
            carrier_name="ONE",
            service_name="CA2 - China Australia",
            departure_port="Yantian",
            arrival_port="Brisbane",
            departure_day_of_week="Monday",
            transit_days=16,
            direct_or_transhipment="direct",
            rate_40hc_usd=3200,
            thc_origin_usd=160,
            thc_destination_usd=210,
            documentation_fee_usd=70,
            fuel_surcharge_usd=90,
            peak_season_surcharge_usd=0,
            total_all_in_usd=3730,
            empty_depot_city="Shenzhen",
            empty_depot_coordinates=Coordinates(lat=22.5431, lng=114.0579),
            drayage_cost_to_warehouse_usd=230,
            drayage_cost_to_port_usd=180,
            schedule_reliability_pct=88,
            average_delay_days=0.8,
            next_available_sailings=upcoming_weekdays(0),
            booking_cutoff_days_before=5,
            rates_updated_at=timestamp,
            created_at=timestamp,
            updated_at=timestamp,
        ),
    ]
    for service in carrier_services:
        service.route_waypoints = sea_route_waypoints(service.departure_port, service.arrival_port)
        store.carrier_services[service.id] = service
        for sailing in service.next_available_sailings:
            carrier_cutoff = sailing - timedelta(days=service.booking_cutoff_days_before)
            sailing_option = SailingOption(
                id=f"SAIL-{service.id}-{sailing.strftime('%Y%m%d')}",
                lane_id=lane.id,
                carrier_service_id=service.id,
                carrier_name=service.carrier_name,
                service_name=service.service_name,
                departure_port=service.departure_port,
                arrival_port=service.arrival_port,
                vessel_name=f"{service.carrier_name} {service.service_name}",
                voyage_number=f"{service.carrier_name[:3].upper()}-{sailing.strftime('%m%d')}",
                etd=sailing,
                eta=sailing + timedelta(days=service.transit_days),
                transit_days=service.transit_days,
                direct_or_transhipment=service.direct_or_transhipment,
                total_all_in_usd=(
                    service.total_all_in_usd
                    + service.drayage_cost_to_warehouse_usd
                    + service.drayage_cost_to_port_usd
                ),
                carrier_gate_in_cutoff_date=carrier_cutoff,
                shipping_instructions_cutoff_date=carrier_cutoff - timedelta(days=1),
                vgm_cutoff_date=carrier_cutoff,
                route_waypoints=service.route_waypoints,
                route_geometry_source_type=service.route_geometry_source_type,
                route_geometry_source_name=service.route_geometry_source_name,
                route_geometry_confidence=service.route_geometry_confidence,
                source_type=SourceType.manual_admin,
                source_name="Ship Hoppa seed schedule",
                source_reference=f"{service.id}-{sailing.isoformat()}",
                last_verified_at=timestamp,
                confidence=SourceConfidence.estimated,
                created_at=timestamp,
                updated_at=timestamp,
            )
            store.sailing_options[sailing_option.id] = sailing_option

    anchor_importer = Importer(
        id="IMP-ANCHOR",
        company_name="Hoppa Stone Imports",
        contact_name="Mitch Bishop",
        email="anchor@shiphoppa.example",
        default_lane_id=lane.id,
        default_supplier_city="Foshan",
        default_cargo_category=CargoCategory.tiles_stone,
        default_cbm=18,
        default_weight_kg=14500,
        cbm_correction_factor=1.0,
        bookings_count=1,
        total_cbm_shipped=0,
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.importers[anchor_importer.id] = anchor_importer

    target_sailing = next_weekday(date.today() + timedelta(days=lane.cutoff_days_before_sailing + 7), 2)
    carrier_cutoff = target_sailing - timedelta(days=lane.cutoff_days_before_sailing)
    container = Container(
        id="CON-FOUNDING",
        lane_id=lane.id,
        status=ContainerStatus.filling,
        target_sailing_date=target_sailing,
        carrier_cutoff_date=carrier_cutoff,
        warehouse_receipt_cutoff_date=target_sailing - timedelta(days=lane.warehouse_receipt_cutoff_days_before_sailing),
        shipping_instructions_cutoff_date=carrier_cutoff - timedelta(days=1),
        vgm_cutoff_date=carrier_cutoff,
        opened_at=timestamp,
        oldest_booking_date=date.today() - timedelta(days=3),
        sailing_source_type=SourceType.manual_admin,
        sailing_source_name="Ship Hoppa weekly schedule",
        sailing_source_reference=f"{lane.id}-founding-container",
        sailing_source_last_verified_at=timestamp,
        sailing_source_confidence=SourceConfidence.estimated,
        route_waypoints=sea_route_waypoints("Yantian", "Brisbane"),
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.containers[container.id] = container

    anchor_booking = Booking(
        id="BKG-ANCHOR",
        importer_id=anchor_importer.id,
        lane_id=lane.id,
        container_id=container.id,
        supplier_name="Foshan Stone Co.",
        supplier_city="Foshan",
        supplier_province="Guangdong",
        supplier_country="China",
        supplier_coordinates=Coordinates(lat=23.0215, lng=113.1214),
        delivery_city="Brisbane",
        delivery_postcode="4000",
        delivery_country="Australia",
        cargo_description="stone slabs and tiles",
        cargo_category=CargoCategory.tiles_stone,
        hs_code="6802",
        cbm_estimate=18,
        weight_kg_estimate=14500,
        cargo_ready_date_earliest=date.today() - timedelta(days=1),
        cargo_ready_date_latest=date.today() + timedelta(days=3),
        service_level=ServiceLevel.standard,
        status=BookingStatus.confirmed,
        match_score=100,
        match_confidence="anchor",
        matched_at=timestamp,
        confirmed_at=timestamp,
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.bookings[anchor_booking.id] = anchor_booking
    container.bookings.append(anchor_booking.id)
    apply_feasibility_to_booking(anchor_booking, evaluate_container_feasibility(store, anchor_booking, container))
    store.bookings[anchor_booking.id] = anchor_booking
    recalculate_container(store, container)
