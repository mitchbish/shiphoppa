from datetime import date, datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from typing import Dict, List, NamedTuple, Optional, Tuple

from .models import (
    ActorRole,
    AuditEvent,
    Booking,
    BookingCreate,
    BookingStatus,
    CargoCategory,
    CarrierService,
    CarrierOption,
    CarrierScoreComponents,
    CommitContainerRequest,
    ConfirmBookingResponse,
    ConsolidationWarehouse,
    Container,
    ContainerStatus,
    Coordinates,
    DeliveryMode,
    FeasibilityStatus,
    Importer,
    Lane,
    MatchResult,
    Notification,
    ReleaseCheckResult,
    SailingOption,
    ShipmentEventCreate,
    ShipmentEventStage,
    SourceConfidence,
    SourceType,
)
from .operations import create_shipment_event, ensure_booking_workspace, ensure_import_project_for_booking, ensure_invoice
from .route_geometry import sea_route_waypoints
from .store import Store


CATEGORY_DENSITY_DEFAULTS: Dict[CargoCategory, float] = {
    CargoCategory.tiles_stone: 2400,
    CargoCategory.bathroom_fittings: 800,
    CargoCategory.furniture: 200,
    CargoCategory.homewares: 350,
    CargoCategory.lighting: 150,
    CargoCategory.hardware: 1200,
    CargoCategory.garden: 400,
    CargoCategory.automotive: 600,
    CargoCategory.other: 500,
}

HS_CODE_DEFAULTS: Dict[CargoCategory, str] = {
    CargoCategory.tiles_stone: "6802",
    CargoCategory.bathroom_fittings: "3922",
    CargoCategory.furniture: "9403",
    CargoCategory.homewares: "6912",
    CargoCategory.lighting: "9405",
    CargoCategory.hardware: "8302",
    CargoCategory.garden: "3926",
    CargoCategory.automotive: "8708",
    CargoCategory.other: "9999",
}

CITY_COORDINATES: Dict[str, Coordinates] = {
    "foshan": Coordinates(lat=23.0215, lng=113.1214),
    "guangzhou": Coordinates(lat=23.1291, lng=113.2644),
    "shenzhen": Coordinates(lat=22.5431, lng=114.0579),
    "dongguan": Coordinates(lat=23.0207, lng=113.7518),
    "zhongshan": Coordinates(lat=22.5176, lng=113.3926),
    "yantian": Coordinates(lat=22.5570, lng=114.2385),
    "shekou": Coordinates(lat=22.4947, lng=113.9194),
    "nansha": Coordinates(lat=22.8016, lng=113.5252),
    "brisbane": Coordinates(lat=-27.4698, lng=153.0251),
    "gold coast": Coordinates(lat=-28.0167, lng=153.4000),
    "sunshine coast": Coordinates(lat=-26.6500, lng=153.0667),
    "logan": Coordinates(lat=-27.6392, lng=153.1094),
    "ipswich": Coordinates(lat=-27.6167, lng=152.7667),
}

SOUTH_EAST_QUEENSLAND_CITIES = {
    "brisbane",
    "gold coast",
    "sunshine coast",
    "logan",
    "ipswich",
    "toowoomba",
    "redcliffe",
    "caboolture",
}

PICKUP_SERVICEABLE_CITIES = {"foshan", "guangzhou", "dongguan", "shenzhen", "zhongshan"}
SELF_DELIVERY_FAST_CITIES = {"foshan", "guangzhou"}


class FeasibilityDecision(NamedTuple):
    status: FeasibilityStatus
    warehouse_receipt_cutoff: date
    latest_supplier_ready_date: date
    reason: str
    urgency_fee_usd: float
    pickup_fee_usd: float
    admin_review_required: bool


def now_utc() -> datetime:
    return datetime.utcnow().replace(microsecond=0)


def clamp(value: float, minimum: float = 0, maximum: float = 1) -> float:
    return max(minimum, min(maximum, value))


def round_money(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(value + 0.0000001, 2)


def add_business_days(value: date, days: int) -> date:
    if days == 0:
        return value
    step = 1 if days > 0 else -1
    remaining = abs(days)
    current = value
    while remaining:
        current += timedelta(days=step)
        if current.weekday() < 5:
            remaining -= 1
    return current


def business_days_between(start: date, end: date) -> int:
    if start == end:
        return 0
    step = 1 if end > start else -1
    current = start
    days = 0
    while current != end:
        current += timedelta(days=step)
        if current.weekday() < 5:
            days += step
    return days


def fallback_warehouse_cutoff(target_sailing_date: date, lane: Lane) -> date:
    return target_sailing_date - timedelta(days=lane.warehouse_receipt_cutoff_days_before_sailing)


def confirmed_warehouse_cutoff(carrier_gate_in_cutoff: date) -> date:
    return add_business_days(carrier_gate_in_cutoff, -2)


def geocode_city(city: str, country: str) -> Coordinates:
    key = city.strip().lower()
    if key in CITY_COORDINATES:
        return CITY_COORDINATES[key]
    if country.lower() == "china":
        return CITY_COORDINATES["guangzhou"]
    if country.lower() == "australia":
        return CITY_COORDINATES["brisbane"]
    return Coordinates(lat=0, lng=0)


def haversine_km(a: Coordinates, b: Coordinates) -> float:
    radius_km = 6371.0
    d_lat = radians(b.lat - a.lat)
    d_lng = radians(b.lng - a.lng)
    lat_1 = radians(a.lat)
    lat_2 = radians(b.lat)
    h = sin(d_lat / 2) ** 2 + cos(lat_1) * cos(lat_2) * sin(d_lng / 2) ** 2
    return 2 * radius_km * asin(sqrt(h))


def origin_lead_business_days(
    booking: Booking,
    lane: Lane,
    warehouse: Optional[ConsolidationWarehouse],
) -> Tuple[Optional[int], Optional[str]]:
    city = booking.supplier_city.strip().lower()
    if not warehouse:
        return None, "No active origin warehouse is configured for this lane."
    if city not in CITY_COORDINATES:
        return None, "Supplier city is not mapped yet, so operations must verify pickup timing."

    distance_km = haversine_km(booking.supplier_coordinates, warehouse.coordinates)
    if distance_km > lane.origin_max_pickup_radius_km:
        return None, f"Supplier is {distance_km:.0f} km from the warehouse, outside the current pickup radius."

    if booking.delivery_mode == DeliveryMode.self_delivery:
        if city in SELF_DELIVERY_FAST_CITIES:
            return 1, "Self-delivery can meet the warehouse receiving buffer."
        return 2, "Self-delivery from this city needs a two business day receiving buffer."

    if city in SELF_DELIVERY_FAST_CITIES:
        return 2, "Ship Hoppa pickup needs one transit day plus one handling day."
    if city in PICKUP_SERVICEABLE_CITIES:
        return 3, "Ship Hoppa pickup needs two transit days plus one handling day."
    return None, "Pickup from this city needs an operations review before confirmation."


def container_warehouse_cutoff(container: Container, lane: Lane) -> date:
    if container.warehouse_receipt_cutoff_date:
        return container.warehouse_receipt_cutoff_date
    if container.sailing_source_confidence == SourceConfidence.confirmed:
        return confirmed_warehouse_cutoff(container.carrier_cutoff_date)
    return fallback_warehouse_cutoff(container.target_sailing_date, lane)


def urgency_fee_for_slack(lane: Lane, slack_business_days: int) -> float:
    if slack_business_days >= 7:
        return 0
    if slack_business_days >= 3:
        return lane.priority_handling_fee_usd
    return lane.rush_handling_fee_usd


def pickup_fee_for_booking(booking: Booking, lane: Lane) -> float:
    return lane.pickup_fee_usd if booking.delivery_mode == DeliveryMode.ship_hoppa_pickup else 0


def evaluate_container_feasibility(store: Store, booking: Booking, container: Container) -> FeasibilityDecision:
    lane = store.lanes[container.lane_id]
    warehouse = store.warehouse_for_lane(container.lane_id)
    warehouse_cutoff = container_warehouse_cutoff(container, lane)
    lead_days, lead_reason = origin_lead_business_days(booking, lane, warehouse)
    pickup_fee = pickup_fee_for_booking(booking, lane)

    if lead_days is None:
        return FeasibilityDecision(
            status=FeasibilityStatus.admin_review,
            warehouse_receipt_cutoff=warehouse_cutoff,
            latest_supplier_ready_date=warehouse_cutoff,
            reason=lead_reason or "Operations must verify the delivery path.",
            urgency_fee_usd=0,
            pickup_fee_usd=pickup_fee,
            admin_review_required=True,
        )

    latest_supplier_ready = add_business_days(warehouse_cutoff, -lead_days)
    slack_days = business_days_between(booking.cargo_ready_date_latest, latest_supplier_ready)
    if slack_days < 0:
        return FeasibilityDecision(
            status=FeasibilityStatus.misses_cutoff,
            warehouse_receipt_cutoff=warehouse_cutoff,
            latest_supplier_ready_date=latest_supplier_ready,
            reason=(
                f"Cargo ready by {booking.cargo_ready_date_latest} misses the latest supplier-ready "
                f"date of {latest_supplier_ready} for this sailing."
            ),
            urgency_fee_usd=0,
            pickup_fee_usd=pickup_fee,
            admin_review_required=False,
        )

    urgency_fee = urgency_fee_for_slack(lane, slack_days)
    if urgency_fee:
        status = FeasibilityStatus.tight
        reason = f"This sailing works, but only has {slack_days} business day{'s' if slack_days != 1 else ''} of slack."
    else:
        status = FeasibilityStatus.feasible
        reason = f"This sailing works with {slack_days} business days of cutoff slack."

    return FeasibilityDecision(
        status=status,
        warehouse_receipt_cutoff=warehouse_cutoff,
        latest_supplier_ready_date=latest_supplier_ready,
        reason=reason,
        urgency_fee_usd=urgency_fee,
        pickup_fee_usd=pickup_fee,
        admin_review_required=False,
    )


def apply_feasibility_to_booking(booking: Booking, decision: FeasibilityDecision) -> None:
    booking.warehouse_receipt_cutoff = decision.warehouse_receipt_cutoff
    booking.latest_supplier_ready_date = decision.latest_supplier_ready_date
    booking.feasibility_status = decision.status
    booking.feasibility_reason = decision.reason
    booking.urgency_fee_usd = round_money(decision.urgency_fee_usd) or 0
    booking.pickup_fee_usd = round_money(decision.pickup_fee_usd) or 0
    booking.admin_review_required = booking.admin_review_required or decision.admin_review_required


def midpoint_date(start: date, end: date) -> date:
    return start + (end - start) / 2


def next_weekday(after: date, weekday: int) -> date:
    days_ahead = (weekday - after.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return after + timedelta(days=days_ahead)


def target_sailing_for_booking(booking: Booking, lane: Lane) -> date:
    buffer_days = 3 if booking.service_level.value == "express" else 7
    ready_anchor = booking.cargo_ready_date_latest + timedelta(days=buffer_days)
    return next_weekday(ready_anchor, 2)


def next_feasible_sailing_for_booking(store: Store, booking: Booking, lane: Lane) -> date:
    warehouse = store.warehouse_for_lane(lane.id)
    lead_days, _ = origin_lead_business_days(booking, lane, warehouse)
    if lead_days is None:
        return target_sailing_for_booking(booking, lane)

    candidate = next_weekday(booking.cargo_ready_date_latest, 2)
    for _ in range(12):
        warehouse_cutoff = fallback_warehouse_cutoff(candidate, lane)
        latest_supplier_ready = add_business_days(warehouse_cutoff, -lead_days)
        if booking.cargo_ready_date_latest <= latest_supplier_ready:
            return candidate
        candidate += timedelta(days=7)
    return target_sailing_for_booking(booking, lane)


def detect_lane(store: Store, payload: BookingCreate) -> Optional[Lane]:
    supplier_text = " ".join(
        [
            payload.supplier_city or "",
            payload.supplier_province or "",
            payload.supplier_country or "",
        ]
    ).lower()
    destination_text = " ".join(
        [
            payload.delivery_city or "",
            payload.delivery_postcode or "",
            payload.delivery_country or "",
        ]
    ).lower()

    matches: List[Lane] = []
    for lane in store.lanes.values():
        if not lane.active:
            continue
        origin_match = (
            "china" in supplier_text
            and (
                "guangdong" in supplier_text
                or payload.supplier_city.strip().lower() in CITY_COORDINATES
            )
        )
        destination_match = (
            "australia" in destination_text
            and (
                "queensland" in destination_text
                or payload.delivery_city.strip().lower() in SOUTH_EAST_QUEENSLAND_CITIES
                or (payload.delivery_postcode or "").startswith("4")
            )
        )
        if origin_match and destination_match:
            matches.append(lane)

    return matches[0] if len(matches) == 1 else None


def density_for_booking(booking: Booking) -> float:
    cbm = booking.cbm_actual or booking.cbm_estimate
    weight = booking.weight_kg_actual or booking.weight_kg_estimate
    return weight / cbm if cbm else 0


def container_pickup_centroid(store: Store, container: Container) -> Optional[Coordinates]:
    points = [
        store.bookings[booking_id].supplier_coordinates
        for booking_id in container.bookings
        if booking_id in store.bookings
    ]
    if not points:
        return None
    return Coordinates(
        lat=sum(point.lat for point in points) / len(points),
        lng=sum(point.lng for point in points) / len(points),
    )


def destination_proximity(booking: Booking, container_bookings: List[Booking]) -> float:
    if not container_bookings:
        return 1.0
    booking_postcode = (booking.delivery_postcode or "").strip()
    booking_city = booking.delivery_city.strip().lower()
    for existing in container_bookings:
        existing_postcode = (existing.delivery_postcode or "").strip()
        if booking_postcode and existing_postcode and booking_postcode[:2] == existing_postcode[:2]:
            return 1.0
        if booking_city == existing.delivery_city.strip().lower():
            return 0.5
    return 0.2


def has_cargo_conflict(new_booking: Booking, existing_bookings: List[Booking]) -> bool:
    description = (new_booking.cargo_description or "").lower()
    is_hazmat = any(word in description for word in ["hazmat", "hazardous", "dangerous goods", "dg"])
    is_odour = any(word in description for word in ["paint", "solvent", "chemical", "strong odour"])
    is_temperature_controlled = any(word in description for word in ["frozen", "chilled", "temperature"])
    if not (is_hazmat or is_odour or is_temperature_controlled):
        return False

    for existing in existing_bookings:
        existing_description = (existing.cargo_description or "").lower()
        existing_special = any(
            word in existing_description
            for word in ["hazmat", "hazardous", "dangerous goods", "dg", "paint", "solvent", "chemical", "frozen", "chilled"]
        )
        if is_hazmat and not existing_special:
            return True
        if is_odour and existing.cargo_category in {
            CargoCategory.furniture,
            CargoCategory.homewares,
            CargoCategory.lighting,
        }:
            return True
        if is_temperature_controlled and "temperature" not in existing_description:
            return True
    return False


def recalculate_container(store: Store, container: Container) -> Container:
    lane = store.lanes[container.lane_id]
    bookings = [store.bookings[booking_id] for booking_id in container.bookings if booking_id in store.bookings]
    current_cbm = sum(booking.cbm_actual or booking.cbm_estimate for booking in bookings)
    current_weight = sum(booking.weight_kg_actual or booking.weight_kg_estimate for booking in bookings)
    unique_importers = {booking.importer_id for booking in bookings}

    container.current_cbm = round(current_cbm, 2)
    container.current_weight_kg = round(current_weight, 2)
    container.remaining_cbm = round(lane.practical_cbm_limit - current_cbm, 2)
    container.remaining_weight_kg = round(lane.road_weight_limit_kg - current_weight, 2)
    container.fill_percentage_cbm = round(current_cbm / lane.practical_cbm_limit, 4)
    container.fill_percentage_weight = round(current_weight / lane.road_weight_limit_kg, 4)
    container.shipper_count = len(unique_importers)
    if bookings:
        container.oldest_booking_date = min(booking.cargo_ready_date_earliest for booking in bookings)
    container.total_platform_fees_usd = len(bookings) * lane.platform_fee_per_booking_usd
    cost_basis = container.container_cost_usd or lane.base_container_cost_usd
    container.cost_per_cbm_usd = round_money(cost_basis / current_cbm) if current_cbm else None
    container.updated_at = now_utc()
    store.containers[container.id] = container

    for booking in bookings:
        cbm = booking.cbm_actual or booking.cbm_estimate
        booking.cbm_cost_usd = round_money((container.cost_per_cbm_usd or 0) * cbm)
        booking.platform_fee_usd = round_money(lane.platform_fee_per_booking_usd)
        booking.total_cost_usd = round_money(
            (booking.cbm_cost_usd or 0)
            + lane.platform_fee_per_booking_usd
            + booking.urgency_fee_usd
            + booking.pickup_fee_usd
        )
        booking.quoted_cost_usd = booking.total_cost_usd
        booking.updated_at = now_utc()
        store.bookings[booking.id] = booking

    return container


def score_candidate(store: Store, booking: Booking, container: Container) -> float:
    lane = store.lanes[container.lane_id]
    existing = [store.bookings[booking_id] for booking_id in container.bookings if booking_id in store.bookings]
    booking_cbm = booking.cbm_actual or booking.cbm_estimate
    booking_weight = booking.weight_kg_actual or booking.weight_kg_estimate

    volume_fit = 1 - max(0, (container.current_cbm + booking_cbm) - lane.practical_cbm_limit) / booking_cbm
    weight_fit = 1 - max(0, (container.current_weight_kg + booking_weight) - lane.road_weight_limit_kg) / booking_weight

    ready_midpoint = midpoint_date(booking.cargo_ready_date_earliest, booking.cargo_ready_date_latest)
    date_delta = abs((container.target_sailing_date - ready_midpoint).days)
    date_alignment = 1 - date_delta / lane.max_wait_days

    centroid = container_pickup_centroid(store, container)
    if centroid:
        origin_distance = haversine_km(booking.supplier_coordinates, centroid)
        origin_proximity = 1 - origin_distance / lane.origin_max_pickup_radius_km
    else:
        origin_proximity = 1.0

    destination_score = destination_proximity(booking, existing)
    ideal_density = lane.road_weight_limit_kg / lane.practical_cbm_limit
    booking_density = density_for_booking(booking)
    if abs(container.fill_percentage_weight - container.fill_percentage_cbm) < 0.08:
        density_complement = 0.5
    elif container.fill_percentage_weight > container.fill_percentage_cbm:
        density_complement = 1.0 if booking_density < ideal_density else 0.25
    else:
        density_complement = 1.0 if booking_density > ideal_density else 0.25

    score = (
        25 * clamp(volume_fit)
        + 25 * clamp(weight_fit)
        + 20 * clamp(date_alignment)
        + 15 * clamp(origin_proximity)
        + 10 * destination_score
        + 5 * density_complement
    )
    return round(score, 1)


def candidate_containers(store: Store, booking: Booking) -> List[Tuple[Container, float]]:
    if not booking.lane_id:
        return []
    lane = store.lanes[booking.lane_id]
    booking_cbm = booking.cbm_actual or booking.cbm_estimate
    booking_weight = booking.weight_kg_actual or booking.weight_kg_estimate
    candidates: List[Tuple[Container, float]] = []

    for container in store.containers.values():
        if container.lane_id != booking.lane_id:
            continue
        if booking.preferred_container_id and container.id != booking.preferred_container_id:
            continue
        if booking.preferred_sailing_option_id:
            preferred = store.sailing_options.get(booking.preferred_sailing_option_id)
            if preferred and container.target_sailing_date != preferred.etd:
                continue
        if container.status not in {ContainerStatus.open, ContainerStatus.filling}:
            continue
        if container.remaining_cbm < booking_cbm or container.remaining_weight_kg < booking_weight:
            continue
        existing = [store.bookings[booking_id] for booking_id in container.bookings if booking_id in store.bookings]
        unique_importers = {item.importer_id for item in existing}
        if booking.importer_id not in unique_importers and len(unique_importers) >= lane.max_shippers_per_container:
            continue
        target_latest = booking.cargo_ready_date_latest + timedelta(days=lane.max_wait_days)
        if not (booking.cargo_ready_date_earliest <= container.target_sailing_date <= target_latest):
            continue
        if has_cargo_conflict(booking, existing):
            continue
        feasibility = evaluate_container_feasibility(store, booking, container)
        if feasibility.status == FeasibilityStatus.misses_cutoff:
            continue
        candidates.append((container, score_candidate(store, booking, container)))

    return sorted(candidates, key=lambda item: item[1], reverse=True)


def create_container_for_booking(store: Store, booking: Booking) -> Container:
    lane = store.lanes[booking.lane_id or ""]
    preferred_option = store.sailing_options.get(booking.preferred_sailing_option_id or "")
    target_sailing = preferred_option.etd if preferred_option else next_feasible_sailing_for_booking(store, booking, lane)
    timestamp = now_utc()
    carrier_cutoff = (
        preferred_option.carrier_gate_in_cutoff_date
        if preferred_option
        else target_sailing - timedelta(days=lane.cutoff_days_before_sailing)
    )
    container = Container(
        id=store.next_id("CON"),
        lane_id=lane.id,
        status=ContainerStatus.filling,
        bookings=[],
        target_sailing_date=target_sailing,
        carrier_cutoff_date=carrier_cutoff,
        warehouse_receipt_cutoff_date=fallback_warehouse_cutoff(target_sailing, lane),
        shipping_instructions_cutoff_date=carrier_cutoff - timedelta(days=1),
        vgm_cutoff_date=carrier_cutoff,
        opened_at=timestamp,
        oldest_booking_date=booking.cargo_ready_date_earliest,
        carrier_name=preferred_option.carrier_name if preferred_option else None,
        carrier_service_id=preferred_option.carrier_service_id if preferred_option else None,
        sailing_option_id=preferred_option.id if preferred_option else None,
        vessel_name=preferred_option.vessel_name if preferred_option else None,
        voyage_number=preferred_option.voyage_number if preferred_option else None,
        estimated_departure=preferred_option.etd if preferred_option else None,
        estimated_arrival=preferred_option.eta if preferred_option else None,
        container_cost_usd=preferred_option.total_all_in_usd if preferred_option else None,
        route_waypoints=(
            preferred_option.route_waypoints
            if preferred_option and preferred_option.route_waypoints
            else sea_route_waypoints(lane.origin_ports[0], lane.destination_port)
        ),
        route_geometry_source_type=preferred_option.route_geometry_source_type if preferred_option else SourceType.manual_admin,
        route_geometry_source_name=preferred_option.route_geometry_source_name if preferred_option else "Ship Hoppa route library",
        route_geometry_confidence=preferred_option.route_geometry_confidence if preferred_option else SourceConfidence.estimated,
        sailing_source_type=preferred_option.source_type if preferred_option else SourceType.manual_admin,
        sailing_source_name=preferred_option.source_name if preferred_option else "Ship Hoppa weekly schedule",
        sailing_source_reference=preferred_option.source_reference if preferred_option else f"{lane.id}-weekly-wednesday",
        sailing_source_last_verified_at=timestamp,
        sailing_source_confidence=preferred_option.confidence if preferred_option else SourceConfidence.estimated,
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.containers[container.id] = container
    return container


def assign_booking_to_container(store: Store, booking: Booking) -> Container:
    scored_candidates = candidate_containers(store, booking)
    best_container: Optional[Container] = None
    best_score = 0.0
    if scored_candidates:
        best_container, best_score = scored_candidates[0]

    if best_container is None or best_score < 40:
        best_container = create_container_for_booking(store, booking)
        best_score = 100.0
        booking.match_confidence = "new_container"
    elif best_score < 60:
        booking.admin_review_required = True
        booking.match_confidence = "admin_review"
    else:
        booking.match_confidence = "high"

    feasibility = evaluate_container_feasibility(store, booking, best_container)
    apply_feasibility_to_booking(booking, feasibility)
    if feasibility.status == FeasibilityStatus.admin_review:
        booking.match_confidence = "admin_review"
    elif feasibility.status == FeasibilityStatus.tight and booking.match_confidence == "high":
        booking.match_confidence = "tight_cutoff"

    booking.container_id = best_container.id
    booking.status = BookingStatus.matched
    booking.match_score = best_score
    booking.matched_at = now_utc()
    booking.updated_at = now_utc()
    if booking.id not in best_container.bookings:
        best_container.bookings.append(booking.id)
    if best_container.status == ContainerStatus.open:
        best_container.status = ContainerStatus.filling
    store.bookings[booking.id] = booking
    return recalculate_container(store, best_container)


def create_notification(
    store: Store,
    recipient_type: str,
    recipient_id: str,
    trigger: str,
    message: str,
    scheduled_for: Optional[datetime] = None,
) -> Notification:
    notification = Notification(
        id=store.next_id("NOT"),
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        trigger=trigger,
        message=message,
        created_at=now_utc(),
        scheduled_for=scheduled_for,
    )
    store.notifications[notification.id] = notification
    return notification


def create_audit_event(
    store: Store,
    actor_role: ActorRole,
    actor_id: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    message: str,
    metadata: Optional[Dict[str, object]] = None,
) -> AuditEvent:
    event = AuditEvent(
        id=store.next_id("AUD"),
        actor_role=actor_role,
        actor_id=actor_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        message=message,
        metadata=metadata or {},
        created_at=now_utc(),
    )
    store.audit_events[event.id] = event
    return event


def schedule_cutoff_reminders(store: Store, booking: Booking) -> None:
    if not booking.latest_supplier_ready_date:
        return
    deadline = datetime.combine(booking.latest_supplier_ready_date, datetime.min.time()).replace(hour=17)
    create_notification(
        store,
        "importer",
        booking.importer_id,
        "supplier_ready_72h_reminder",
        f"Booking {booking.id} must be ready by {booking.latest_supplier_ready_date} to protect this sailing.",
        scheduled_for=deadline - timedelta(hours=72),
    )
    create_notification(
        store,
        "importer",
        booking.importer_id,
        "supplier_ready_24h_reminder",
        f"Final reminder: booking {booking.id} must be ready by {booking.latest_supplier_ready_date}.",
        scheduled_for=deadline - timedelta(hours=24),
    )


def submit_booking(
    store: Store,
    payload: BookingCreate,
    actor_role: ActorRole = ActorRole.importer,
    actor_id: str = "anonymous-importer",
) -> MatchResult:
    timestamp = now_utc()
    importer = store.importer_by_email(payload.importer_email)
    if not importer:
        importer = Importer(
            id=store.next_id("IMP"),
            company_name=payload.importer_company_name,
            contact_name=payload.importer_contact_name,
            email=payload.importer_email.strip().lower(),
            phone=payload.importer_phone,
            created_at=timestamp,
            updated_at=timestamp,
        )
        store.importers[importer.id] = importer
    else:
        importer.company_name = payload.importer_company_name
        importer.contact_name = payload.importer_contact_name
        importer.phone = payload.importer_phone or importer.phone
        importer.updated_at = timestamp
        store.importers[importer.id] = importer

    lane = detect_lane(store, payload)
    supplier_coordinates = geocode_city(payload.supplier_city, payload.supplier_country)
    corrected_cbm = payload.cbm_estimate * importer.cbm_correction_factor
    booking = Booking(
        id=store.next_id("BKG"),
        importer_id=importer.id,
        lane_id=lane.id if lane else None,
        supplier_name=payload.supplier_name,
        supplier_city=payload.supplier_city,
        supplier_province=payload.supplier_province,
        supplier_country=payload.supplier_country,
        supplier_coordinates=supplier_coordinates,
        delivery_city=payload.delivery_city,
        delivery_postcode=payload.delivery_postcode,
        delivery_country=payload.delivery_country,
        cargo_description=payload.cargo_description,
        cargo_category=payload.cargo_category,
        hs_code=HS_CODE_DEFAULTS[payload.cargo_category],
        cbm_estimate=round(corrected_cbm, 2),
        weight_kg_estimate=payload.weight_kg_estimate,
        number_of_packages=payload.number_of_packages,
        package_type=payload.package_type,
        package_length_cm=payload.package_length_cm,
        package_width_cm=payload.package_width_cm,
        package_height_cm=payload.package_height_cm,
        cargo_ready_date_earliest=payload.cargo_ready_date_earliest,
        cargo_ready_date_latest=payload.cargo_ready_date_latest,
        service_level=payload.service_level,
        delivery_mode=payload.delivery_mode,
        pickup_address=payload.pickup_address,
        pickup_contact_name=payload.pickup_contact_name,
        pickup_contact_phone=payload.pickup_contact_phone,
        pickup_window_start=payload.pickup_window_start,
        pickup_window_end=payload.pickup_window_end,
        preferred_sailing_option_id=payload.preferred_sailing_option_id,
        preferred_container_id=payload.preferred_container_id,
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.bookings[booking.id] = booking
    ensure_booking_workspace(store, booking)
    importer.bookings_count += 1
    importer.default_lane_id = lane.id if lane else importer.default_lane_id
    importer.default_supplier_city = booking.supplier_city
    importer.default_cargo_category = booking.cargo_category
    importer.default_cbm = booking.cbm_estimate
    importer.default_weight_kg = booking.weight_kg_estimate
    importer.updated_at = timestamp
    store.importers[importer.id] = importer
    create_audit_event(
        store,
        actor_role,
        actor_id,
        "booking_submitted",
        "booking",
        booking.id,
        f"Booking {booking.id} submitted from {booking.supplier_city} to {booking.delivery_city}.",
        {"importer_id": importer.id, "lane_id": booking.lane_id},
    )
    ensure_import_project_for_booking(store, booking, actor_id)

    if not lane:
        notification = create_notification(
            store,
            "importer",
            importer.id,
            "no_match_found",
            "We do not serve this route yet. We will notify you when Ship Hoppa opens the lane.",
        )
        create_notification(
            store,
            "admin",
            "ops",
            "new_lane_request",
            f"New lane request from {booking.supplier_city} to {booking.delivery_city}.",
        )
        create_audit_event(
            store,
            ActorRole.system,
            "matching-engine",
            "lane_not_found",
            "booking",
            booking.id,
            f"No active lane matched booking {booking.id}.",
            {"supplier_city": booking.supplier_city, "delivery_city": booking.delivery_city},
        )
        return MatchResult(booking=booking, notification=notification)

    container = assign_booking_to_container(store, booking)
    warehouse = store.warehouse_for_lane(lane.id)
    refreshed_booking = store.bookings[booking.id]
    ensure_invoice(store, refreshed_booking)
    ensure_booking_workspace(store, refreshed_booking)
    refreshed_booking = store.bookings[booking.id]
    ensure_import_project_for_booking(store, refreshed_booking, actor_id)
    create_audit_event(
        store,
        ActorRole.system,
        "matching-engine",
        "booking_matched",
        "booking",
        refreshed_booking.id,
        f"Booking {refreshed_booking.id} matched to container {container.id}.",
        {
            "container_id": container.id,
            "match_score": refreshed_booking.match_score,
            "match_confidence": refreshed_booking.match_confidence,
            "feasibility_status": refreshed_booking.feasibility_status.value if refreshed_booking.feasibility_status else None,
            "warehouse_receipt_cutoff": refreshed_booking.warehouse_receipt_cutoff.isoformat()
            if refreshed_booking.warehouse_receipt_cutoff
            else None,
            "latest_supplier_ready_date": refreshed_booking.latest_supplier_ready_date.isoformat()
            if refreshed_booking.latest_supplier_ready_date
            else None,
        },
    )
    schedule_cutoff_reminders(store, refreshed_booking)
    notification = create_notification(
        store,
        "importer",
        importer.id,
        "booking_matched",
        (
            f"Your shipment matched to Container {container.id}, sailing {container.target_sailing_date}. "
            f"Warehouse cutoff is {refreshed_booking.warehouse_receipt_cutoff}. "
            f"Cost: ${refreshed_booking.total_cost_usd:.2f}. Confirm within 48h."
        ),
    )
    lcl_estimate = round_money((refreshed_booking.total_cost_usd or 0) * 2.4)
    saving = round_money((lcl_estimate or 0) - (refreshed_booking.total_cost_usd or 0))
    saving_percent = round((saving or 0) / (lcl_estimate or 1) * 100, 1)
    return MatchResult(
        booking=refreshed_booking,
        container=container,
        lane=lane,
        warehouse=warehouse,
        notification=notification,
        lcl_estimate_usd=lcl_estimate,
        saving_usd=saving,
        saving_percent=saving_percent,
    )


def supplier_instructions(booking: Booking, warehouse: ConsolidationWarehouse) -> str:
    if booking.delivery_mode == DeliveryMode.ship_hoppa_pickup:
        pickup_address = booking.pickup_address or f"{booking.supplier_name or booking.supplier_city}, {booking.supplier_city}"
        return (
            f"Ship Hoppa will coordinate pickup for booking {booking.id} from {pickup_address}. "
            f"Cargo must be ready by {booking.latest_supplier_ready_date}. "
            f"Pickup contact: {booking.pickup_contact_name or 'supplier contact'} "
            f"{booking.pickup_contact_phone or ''}. Mark every package with {booking.id}. "
            f"Ship Hoppa owns the process after pickup scan; supplier must keep cargo accessible and packed for export."
        )
    return (
        f"Please deliver cargo for Ship Hoppa booking {booking.id} to {warehouse.name}, "
        f"{warehouse.address} by {booking.warehouse_receipt_cutoff}. Mark every package with {booking.id}. "
        f"Warehouse hours: {warehouse.operating_hours}. Contact {warehouse.contact_name} "
        f"on {warehouse.contact_phone} before delivery. The importer or supplier is responsible until warehouse receipt scan."
    )


def confirm_booking(store: Store, booking_id: str) -> ConfirmBookingResponse:
    booking = store.bookings[booking_id]
    if not booking.lane_id:
        raise ValueError("Booking has no active lane yet.")
    warehouse = store.warehouse_for_lane(booking.lane_id)
    if not warehouse:
        raise ValueError("No active warehouse for lane.")
    if booking.status == BookingStatus.confirmed:
        return ConfirmBookingResponse(
            booking=booking,
            warehouse=warehouse,
            supplier_instructions=supplier_instructions(booking, warehouse),
        )
    if booking.status != BookingStatus.matched:
        raise ValueError(f"Only matched bookings can be confirmed. Current status is {booking.status.value}.")
    if booking.feasibility_status == FeasibilityStatus.admin_review or booking.admin_review_required:
        raise ValueError("Booking needs operations review before importer confirmation.")
    booking.status = BookingStatus.confirmed
    booking.confirmed_at = now_utc()
    booking.updated_at = now_utc()
    store.bookings[booking.id] = booking
    create_notification(
        store,
        "importer",
        booking.importer_id,
        "booking_confirmed",
        f"Booking {booking.id} is confirmed. Send your supplier the warehouse delivery instructions.",
    )
    create_audit_event(
        store,
        ActorRole.importer,
        booking.importer_id,
        "booking_confirmed",
        "booking",
        booking.id,
        f"Booking {booking.id} confirmed by importer.",
        {"container_id": booking.container_id},
    )
    create_shipment_event(
        store,
        booking.id,
        ShipmentEventCreate(
            stage=ShipmentEventStage.booking_confirmed,
            label="Booking confirmed",
            occurred_at=booking.confirmed_at,
            source_type=SourceType.manual_admin,
            source_name="Ship Hoppa app",
            confidence=SourceConfidence.confirmed,
        ),
    )
    if booking.delivery_mode == DeliveryMode.ship_hoppa_pickup:
        create_shipment_event(
            store,
            booking.id,
            ShipmentEventCreate(
                stage=ShipmentEventStage.pickup_scheduled,
                label="Pickup instructions issued",
                estimated_at=now_utc(),
                source_type=SourceType.warehouse_event,
                source_name="Ship Hoppa ops",
                confidence=SourceConfidence.verified,
            ),
        )
    ensure_invoice(store, booking)
    ensure_booking_workspace(store, booking)
    return ConfirmBookingResponse(
        booking=store.bookings[booking.id],
        warehouse=warehouse,
        supplier_instructions=supplier_instructions(store.bookings[booking.id], warehouse),
    )


def option_score(value: float, minimum: float, maximum: float, inverse: bool = False) -> float:
    if maximum == minimum:
        return 1.0
    if inverse:
        return clamp(1 - (value - minimum) / (maximum - minimum))
    return clamp((value - minimum) / (maximum - minimum))


def rank_carrier_options(store: Store, container_id: str) -> List[CarrierOption]:
    container = store.containers[container_id]
    warehouse = store.warehouse_for_lane(container.lane_id)
    if not warehouse:
        return []
    today = date.today()
    raw_options: List[Tuple[SailingOption, CarrierService]] = []
    for option in store.sailing_options.values():
        if option.lane_id != container.lane_id or not option.active:
            continue
        if option.carrier_gate_in_cutoff_date < today:
            continue
        if abs((option.etd - container.target_sailing_date).days) > 14:
            continue
        service = store.carrier_services.get(option.carrier_service_id)
        if not service or not service.active:
            continue
        raw_options.append((option, service))

    if not raw_options:
        return []

    costs = [option.total_all_in_usd for option, _ in raw_options]
    transit_days = [option.transit_days for option, _ in raw_options]
    min_cost, max_cost = min(costs), max(costs)
    min_transit, max_transit = min(transit_days), max(transit_days)

    options: List[CarrierOption] = []
    for option, service in raw_options:
        all_in_cost = option.total_all_in_usd
        cost_score = option_score(all_in_cost, min_cost, max_cost, inverse=True)
        schedule_score = clamp(1 - abs((option.etd - container.target_sailing_date).days) / 14)
        transit_score = option_score(option.transit_days, min_transit, max_transit, inverse=True)
        depot_distance = haversine_km(service.empty_depot_coordinates, warehouse.coordinates)
        depot_score = clamp(1 - depot_distance / 100)
        reliability_score = clamp(service.schedule_reliability_pct / 100)
        total_score = (
            35 * cost_score
            + 25 * schedule_score
            + 20 * transit_score
            + 10 * depot_score
            + 10 * reliability_score
        )
        options.append(
            CarrierOption(
                sailing_option_id=option.id,
                service_id=option.carrier_service_id,
                carrier_name=option.carrier_name,
                service_name=option.service_name,
                departure_port=option.departure_port,
                arrival_port=option.arrival_port,
                sailing_date=option.etd,
                eta=option.eta,
                transit_days=option.transit_days,
                direct_or_transhipment=option.direct_or_transhipment,
                total_all_in_usd=round_money(all_in_cost) or 0,
                carrier_gate_in_cutoff_date=option.carrier_gate_in_cutoff_date,
                shipping_instructions_cutoff_date=option.shipping_instructions_cutoff_date,
                vgm_cutoff_date=option.vgm_cutoff_date,
                source_type=option.source_type,
                source_name=option.source_name,
                source_reference=option.source_reference,
                last_verified_at=option.last_verified_at,
                confidence=option.confidence,
                route_waypoints=option.route_waypoints,
                route_geometry_source_type=option.route_geometry_source_type,
                route_geometry_source_name=option.route_geometry_source_name,
                route_geometry_confidence=option.route_geometry_confidence,
                score=round(total_score, 1),
                components=CarrierScoreComponents(
                    cost=round(cost_score, 3),
                    schedule=round(schedule_score, 3),
                    transit=round(transit_score, 3),
                    depot_proximity=round(depot_score, 3),
                    reliability=round(reliability_score, 3),
                ),
            )
        )

    options = sorted(options, key=lambda option: option.score, reverse=True)
    if len(options) > 1 and options[0].score - options[1].score < 5:
        direct_options = [option for option in options[:2] if option.direct_or_transhipment == "direct"]
        if direct_options:
            direct = direct_options[0]
            options = [direct] + [option for option in options if option != direct]
    return options


def selected_carrier_option(store: Store, container: Container) -> Optional[CarrierOption]:
    if not container.carrier_service_id or not container.estimated_departure:
        return None
    service = store.carrier_services.get(container.carrier_service_id)
    if not service:
        return None
    sailing_option = store.sailing_options.get(container.sailing_option_id or "")
    gate_in_cutoff = container.carrier_cutoff_date
    si_cutoff = container.shipping_instructions_cutoff_date or gate_in_cutoff
    vgm_cutoff = container.vgm_cutoff_date or gate_in_cutoff
    return CarrierOption(
        sailing_option_id=container.sailing_option_id or f"{service.id}-{container.estimated_departure.isoformat()}",
        service_id=service.id,
        carrier_name=service.carrier_name,
        service_name=service.service_name,
        departure_port=service.departure_port,
        arrival_port=service.arrival_port,
        sailing_date=container.estimated_departure,
        eta=container.estimated_arrival or container.estimated_departure + timedelta(days=service.transit_days),
        transit_days=service.transit_days,
        direct_or_transhipment=service.direct_or_transhipment,
        total_all_in_usd=container.container_cost_usd or service.total_all_in_usd,
        carrier_gate_in_cutoff_date=gate_in_cutoff,
        shipping_instructions_cutoff_date=si_cutoff,
        vgm_cutoff_date=vgm_cutoff,
        source_type=container.sailing_source_type,
        source_name=container.sailing_source_name,
        source_reference=container.sailing_source_reference
        or (sailing_option.source_reference if sailing_option else None),
        last_verified_at=container.sailing_source_last_verified_at or now_utc(),
        confidence=container.sailing_source_confidence,
        route_waypoints=container.route_waypoints or (sailing_option.route_waypoints if sailing_option else service.route_waypoints),
        route_geometry_source_type=container.route_geometry_source_type,
        route_geometry_source_name=container.route_geometry_source_name,
        route_geometry_confidence=container.route_geometry_confidence,
        score=100,
        components=CarrierScoreComponents(
            cost=1,
            schedule=1,
            transit=1,
            depot_proximity=1,
            reliability=round(service.schedule_reliability_pct / 100, 3),
        ),
    )


def commit_container(store: Store, container_id: str, request: Optional[CommitContainerRequest] = None) -> ReleaseCheckResult:
    container = store.containers[container_id]
    if container.status == ContainerStatus.committed:
        return ReleaseCheckResult(
            container_id=container_id,
            released=True,
            reasons=["Already committed; no side effects repeated"],
            selected_carrier=selected_carrier_option(store, container),
        )
    if container.status not in {ContainerStatus.open, ContainerStatus.filling}:
        return ReleaseCheckResult(
            container_id=container_id,
            released=False,
            reasons=[f"Container status {container.status.value} cannot be committed"],
        )
    options = rank_carrier_options(store, container_id)
    selected: Optional[CarrierOption] = None
    if request and request.sailing_option_id:
        for option in options:
            if option.sailing_option_id == request.sailing_option_id:
                selected = option
                break
    if request and request.carrier_service_id and not selected:
        for option in options:
            if option.service_id == request.carrier_service_id and (
                request.sailing_date is None or option.sailing_date == request.sailing_date
            ):
                selected = option
                break
    if not selected and options:
        selected = options[0]
    if not selected:
        return ReleaseCheckResult(container_id=container_id, released=False, reasons=["No carrier option available"])

    service = store.carrier_services[selected.service_id]
    gate_in_cutoff = (
        request.confirmed_carrier_cutoff_date
        if request and request.confirmed_carrier_cutoff_date
        else selected.carrier_gate_in_cutoff_date
    )
    si_cutoff = (
        request.confirmed_shipping_instructions_cutoff_date
        if request and request.confirmed_shipping_instructions_cutoff_date
        else selected.shipping_instructions_cutoff_date
    )
    vgm_cutoff = request.confirmed_vgm_cutoff_date if request and request.confirmed_vgm_cutoff_date else selected.vgm_cutoff_date
    container.status = ContainerStatus.committed
    container.container_close_date = date.today()
    container.target_sailing_date = selected.sailing_date
    container.carrier_cutoff_date = gate_in_cutoff
    container.warehouse_receipt_cutoff_date = confirmed_warehouse_cutoff(gate_in_cutoff)
    container.shipping_instructions_cutoff_date = si_cutoff
    container.vgm_cutoff_date = vgm_cutoff
    container.carrier_name = selected.carrier_name
    container.carrier_service_id = selected.service_id
    container.sailing_option_id = selected.sailing_option_id
    container.estimated_departure = selected.sailing_date
    container.estimated_arrival = selected.eta
    container.container_cost_usd = selected.total_all_in_usd
    container.route_waypoints = selected.route_waypoints or service.route_waypoints
    container.route_geometry_source_type = selected.route_geometry_source_type
    container.route_geometry_source_name = selected.route_geometry_source_name
    container.route_geometry_confidence = selected.route_geometry_confidence
    container.vessel_name = f"{selected.carrier_name} {selected.service_name}"
    container.voyage_number = f"{selected.carrier_name[:3].upper()}-{selected.sailing_date.strftime('%m%d')}"
    container.sailing_source_type = SourceType.forwarder_confirmation
    container.sailing_source_name = selected.carrier_name
    container.sailing_source_reference = (
        request.source_reference if request and request.source_reference else selected.source_reference or selected.sailing_option_id
    )
    container.sailing_source_last_verified_at = now_utc()
    container.sailing_source_confidence = SourceConfidence.confirmed
    container.updated_at = now_utc()
    store.containers[container.id] = recalculate_container(store, container)
    for booking_id in container.bookings:
        booking = store.bookings[booking_id]
        decision = evaluate_container_feasibility(store, booking, container)
        apply_feasibility_to_booking(booking, decision)
        booking.updated_at = now_utc()
        store.bookings[booking.id] = booking
    store.containers[container.id] = recalculate_container(store, container)
    warehouse = store.warehouse_for_lane(container.lane_id)
    for booking_id in container.bookings:
        booking = store.bookings[booking_id]
        create_shipment_event(
            store,
            booking.id,
            ShipmentEventCreate(
                stage=ShipmentEventStage.container_committed,
                label=f"Container committed with {selected.carrier_name}",
                occurred_at=now_utc(),
                source_type=SourceType.forwarder_confirmation,
                source_name=selected.carrier_name,
                confidence=SourceConfidence.confirmed,
                notes=f"ETD {selected.sailing_date}, ETA {selected.eta}.",
            ),
        )
        create_shipment_event(
            store,
            booking.id,
            ShipmentEventCreate(
                stage=ShipmentEventStage.departed,
                label="Estimated vessel departure",
                estimated_at=datetime.combine(selected.sailing_date, datetime.min.time()),
                source_type=SourceType.forwarder_confirmation,
                source_name=selected.carrier_name,
                confidence=SourceConfidence.estimated,
            ),
        )
        ensure_invoice(store, booking)
        ensure_booking_workspace(store, booking)
        create_notification(
            store,
            "importer",
            booking.importer_id,
            "container_released",
            (
                f"Container {container.id} is confirmed for sailing {selected.sailing_date} "
                f"on {container.vessel_name}. Deliver to {warehouse.name if warehouse else 'the warehouse'} "
                f"by warehouse cutoff {container.warehouse_receipt_cutoff_date}."
            ),
        )
    create_notification(
        store,
        "admin",
        "ops",
        "warehouse_empty_container",
        (
            f"Empty container for {container.id} arriving from {selected.carrier_name} depot. "
            f"Loading is scheduled before gate-in cutoff {container.carrier_cutoff_date}."
        ),
    )
    create_audit_event(
        store,
        ActorRole.admin,
        "ops",
        "container_committed",
        "container",
        container.id,
        f"Container {container.id} committed with {selected.carrier_name}.",
        {
            "carrier_service_id": selected.service_id,
            "sailing_option_id": selected.sailing_option_id,
            "sailing_date": selected.sailing_date.isoformat(),
            "carrier_gate_in_cutoff_date": container.carrier_cutoff_date.isoformat(),
            "warehouse_receipt_cutoff_date": container.warehouse_receipt_cutoff_date.isoformat()
            if container.warehouse_receipt_cutoff_date
            else None,
            "container_cost_usd": selected.total_all_in_usd,
            "booking_count": len(container.bookings),
            "source_type": container.sailing_source_type.value,
            "source_confidence": container.sailing_source_confidence.value,
        },
    )
    return ReleaseCheckResult(
        container_id=container_id,
        released=True,
        reasons=["Committed with selected carrier"],
        selected_carrier=selected,
    )


def release_reasons(store: Store, container: Container) -> List[str]:
    lane = store.lanes[container.lane_id]
    reasons: List[str] = []
    if container.fill_percentage_cbm >= lane.cbm_release_threshold:
        reasons.append(f"Volume fill at {container.fill_percentage_cbm:.0%}")
    if container.fill_percentage_weight >= lane.weight_release_threshold:
        reasons.append(f"Weight fill at {container.fill_percentage_weight:.0%}")
    warehouse_cutoff = container_warehouse_cutoff(container, lane)
    if (warehouse_cutoff - date.today()).days <= lane.warehouse_receipt_cutoff_days_before_sailing:
        reasons.append(f"Warehouse cutoff is within {lane.warehouse_receipt_cutoff_days_before_sailing} days")
    if (date.today() - container.oldest_booking_date).days >= lane.max_wait_days:
        reasons.append(f"Oldest booking has waited {lane.max_wait_days}+ days")
    return reasons


def run_release_checks(store: Store) -> List[ReleaseCheckResult]:
    results: List[ReleaseCheckResult] = []
    for container in list(store.containers.values()):
        if container.status != ContainerStatus.filling:
            continue
        reasons = release_reasons(store, container)
        if reasons:
            result = commit_container(store, container.id)
            result.reasons = reasons
            results.append(result)
        else:
            results.append(ReleaseCheckResult(container_id=container.id, released=False, reasons=[]))
    return results
