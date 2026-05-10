from typing import Callable, Dict, List, Optional

from .models import RouteWaypoint


def waypoint(lat: float, lng: float) -> RouteWaypoint:
    return RouteWaypoint(lat=round(lat, 4), lng=round(lng, 4))


PORT_COORDINATES: Dict[str, RouteWaypoint] = {
    "brisbane": waypoint(-27.3811, 153.1674),
    "port of brisbane": waypoint(-27.3811, 153.1674),
    "sydney": waypoint(-33.8587, 151.2140),
    "melbourne": waypoint(-37.8428, 144.9057),
    "fremantle": waypoint(-32.0569, 115.7439),
    "adelaide": waypoint(-34.8462, 138.5074),
    "yantian": waypoint(22.5949, 114.2767),
    "shekou": waypoint(22.4846, 113.9129),
    "nansha": waypoint(22.8016, 113.5255),
    "hong kong": waypoint(22.3080, 114.2250),
    "shanghai": waypoint(31.2304, 121.4737),
    "ningbo": waypoint(29.8683, 121.5440),
    "xiamen": waypoint(24.4798, 118.0894),
    "qingdao": waypoint(36.0671, 120.3826),
    "singapore": waypoint(1.2655, 103.8409),
    "port klang": waypoint(2.9994, 101.3928),
    "tanjung pelepas": waypoint(1.3620, 103.5480),
    "ho chi minh": waypoint(10.7769, 106.7009),
    "laem chabang": waypoint(13.0827, 100.8830),
    "jakarta": waypoint(-6.1045, 106.8860),
    "jebel ali": waypoint(24.9857, 55.0273),
    "dubai": waypoint(24.9857, 55.0273),
    "rotterdam": waypoint(51.9480, 4.1420),
    "hamburg": waypoint(53.5461, 9.9661),
    "felixstowe": waypoint(51.9560, 1.3510),
    "antwerp": waypoint(51.2636, 4.4011),
    "valencia": waypoint(39.4483, -0.3167),
    "new york": waypoint(40.6681, -74.0451),
    "newark": waypoint(40.6840, -74.1480),
    "los angeles": waypoint(33.7361, -118.2639),
    "long beach": waypoint(33.7542, -118.2165),
    "oakland": waypoint(37.7955, -122.2802),
    "savannah": waypoint(32.1286, -81.1518),
    "miami": waypoint(25.7781, -80.1794),
}


PANAMA_PACIFIC = waypoint(8.9, -79.6)
PANAMA_CARIBBEAN = waypoint(9.9, -79.9)
SUEZ_SOUTH = waypoint(29.8, 32.55)
SUEZ_NORTH = waypoint(31.3, 32.35)
GIBRALTAR = waypoint(36.05, -5.55)
MALACCA = waypoint(1.25, 103.8)
HORMUZ = waypoint(25.6, 56.6)


def normalize_port_name(name: str) -> str:
    normalized = name.lower().strip()
    for prefix in ("port of ", "port "):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
    return normalized.replace("  ", " ")


def port_coordinate(name: str) -> Optional[RouteWaypoint]:
    normalized = normalize_port_name(name)
    if normalized in PORT_COORDINATES:
        return PORT_COORDINATES[normalized]
    for key, value in PORT_COORDINATES.items():
        if key in normalized or normalized in key:
            return value
    return None


def is_east_asia(point: RouteWaypoint) -> bool:
    return 105 <= point.lng <= 130 and 15 <= point.lat <= 42


def is_southeast_asia(point: RouteWaypoint) -> bool:
    return 95 <= point.lng <= 121 and -8 <= point.lat <= 15


def is_australia(point: RouteWaypoint) -> bool:
    return 112 <= point.lng <= 156 and -44 <= point.lat <= -10


def is_europe(point: RouteWaypoint) -> bool:
    return -10 <= point.lng <= 25 and 35 <= point.lat <= 58


def is_middle_east(point: RouteWaypoint) -> bool:
    return 45 <= point.lng <= 60 and 20 <= point.lat <= 30


def is_us_west(point: RouteWaypoint) -> bool:
    return -126 <= point.lng <= -115 and 30 <= point.lat <= 49


def is_us_east(point: RouteWaypoint) -> bool:
    return -83 <= point.lng <= -65 and 24 <= point.lat <= 46


def pair_matches(
    origin: RouteWaypoint,
    destination: RouteWaypoint,
    origin_test: Callable[[RouteWaypoint], bool],
    destination_test: Callable[[RouteWaypoint], bool],
) -> bool:
    return origin_test(origin) and destination_test(destination)


def dedupe_waypoints(points: List[RouteWaypoint]) -> List[RouteWaypoint]:
    unique: List[RouteWaypoint] = []
    for point in points:
        if unique and abs(unique[-1].lat - point.lat) < 0.01 and abs(unique[-1].lng - point.lng) < 0.01:
            continue
        unique.append(point)
    return unique


def east_asia_to_australia(origin: RouteWaypoint, destination: RouteWaypoint) -> List[RouteWaypoint]:
    return [
        origin,
        waypoint(22.35, 114.75),
        waypoint(21.9, 117.0),
        waypoint(21.6, 120.5),
        waypoint(20.0, 123.5),
        waypoint(14.5, 127.5),
        waypoint(7.2, 132.8),
        waypoint(1.5, 143.8),
        waypoint(-1.2, 153.0),
        waypoint(-9.5, 162.5),
        waypoint(-18.8, 160.2),
        waypoint(-25.0, 155.1),
        destination,
    ]


def southeast_asia_to_australia(origin: RouteWaypoint, destination: RouteWaypoint) -> List[RouteWaypoint]:
    return [
        origin,
        waypoint(-3.5, 107.5),
        waypoint(-8.5, 119.0),
        waypoint(-12.5, 137.0),
        waypoint(-16.5, 150.5),
        waypoint(-24.5, 154.8),
        destination,
    ]


def east_asia_to_us_west(origin: RouteWaypoint, destination: RouteWaypoint) -> List[RouteWaypoint]:
    return [
        origin,
        waypoint(24.5, 123.0),
        waypoint(30.0, 142.0),
        waypoint(36.0, 164.0),
        waypoint(39.0, 179.0),
        waypoint(41.0, -166.0),
        waypoint(40.0, -145.0),
        waypoint(36.0, -128.0),
        destination,
    ]


def east_asia_to_us_east(origin: RouteWaypoint, destination: RouteWaypoint) -> List[RouteWaypoint]:
    return [
        origin,
        waypoint(23.5, 122.5),
        waypoint(29.0, 145.0),
        waypoint(34.0, 169.0),
        waypoint(31.0, -163.0),
        waypoint(25.0, -139.0),
        waypoint(17.0, -112.0),
        PANAMA_PACIFIC,
        PANAMA_CARIBBEAN,
        waypoint(19.0, -75.0),
        waypoint(29.0, -69.0),
        waypoint(37.5, -72.0),
        destination,
    ]


def east_asia_to_europe(origin: RouteWaypoint, destination: RouteWaypoint) -> List[RouteWaypoint]:
    return [
        origin,
        waypoint(20.0, 119.0),
        waypoint(12.0, 113.0),
        MALACCA,
        waypoint(5.0, 88.0),
        waypoint(8.0, 70.0),
        waypoint(13.0, 55.0),
        waypoint(14.0, 43.0),
        SUEZ_SOUTH,
        SUEZ_NORTH,
        waypoint(34.5, 22.0),
        GIBRALTAR,
        waypoint(48.5, -5.5),
        destination,
    ]


def europe_to_us_east(origin: RouteWaypoint, destination: RouteWaypoint) -> List[RouteWaypoint]:
    return [
        origin,
        waypoint(49.0, -7.0),
        waypoint(48.0, -24.0),
        waypoint(44.0, -43.0),
        waypoint(39.5, -62.0),
        destination,
    ]


def middle_east_to_europe(origin: RouteWaypoint, destination: RouteWaypoint) -> List[RouteWaypoint]:
    return [
        origin,
        HORMUZ,
        waypoint(20.0, 60.0),
        waypoint(13.0, 50.0),
        waypoint(14.0, 43.0),
        SUEZ_SOUTH,
        SUEZ_NORTH,
        waypoint(34.5, 22.0),
        GIBRALTAR,
        waypoint(48.5, -5.5),
        destination,
    ]


def middle_east_to_australia(origin: RouteWaypoint, destination: RouteWaypoint) -> List[RouteWaypoint]:
    return [
        origin,
        HORMUZ,
        waypoint(15.0, 63.0),
        waypoint(2.0, 84.0),
        waypoint(-6.0, 104.0),
        waypoint(-11.0, 122.0),
        waypoint(-15.5, 140.0),
        waypoint(-23.5, 154.5),
        destination,
    ]


def europe_to_australia(origin: RouteWaypoint, destination: RouteWaypoint) -> List[RouteWaypoint]:
    return [
        origin,
        waypoint(48.5, -5.5),
        GIBRALTAR,
        waypoint(34.5, 22.0),
        SUEZ_NORTH,
        SUEZ_SOUTH,
        waypoint(14.0, 43.0),
        waypoint(8.0, 70.0),
        MALACCA,
        waypoint(-6.5, 108.0),
        waypoint(-11.5, 122.0),
        waypoint(-16.0, 141.0),
        waypoint(-24.0, 154.5),
        destination,
    ]


def us_west_to_australia(origin: RouteWaypoint, destination: RouteWaypoint) -> List[RouteWaypoint]:
    return [
        origin,
        waypoint(32.0, -130.0),
        waypoint(21.0, -151.0),
        waypoint(5.0, -170.0),
        waypoint(-6.0, 178.0),
        waypoint(-16.0, 164.0),
        waypoint(-24.0, 155.0),
        destination,
    ]


def generic_ocean_route(origin: RouteWaypoint, destination: RouteWaypoint) -> List[RouteWaypoint]:
    midpoint_lat = (origin.lat + destination.lat) / 2
    midpoint_lng = (origin.lng + destination.lng) / 2
    if abs(origin.lng - destination.lng) > 180:
        midpoint_lng = ((origin.lng + destination.lng + 360) / 2 + 180) % 360 - 180
    return [origin, waypoint(midpoint_lat, midpoint_lng), destination]


def sea_route_between(origin: RouteWaypoint, destination: RouteWaypoint) -> List[RouteWaypoint]:
    routes = [
        (is_east_asia, is_australia, east_asia_to_australia),
        (is_southeast_asia, is_australia, southeast_asia_to_australia),
        (is_east_asia, is_us_west, east_asia_to_us_west),
        (is_east_asia, is_us_east, east_asia_to_us_east),
        (is_east_asia, is_europe, east_asia_to_europe),
        (is_europe, is_us_east, europe_to_us_east),
        (is_middle_east, is_europe, middle_east_to_europe),
        (is_middle_east, is_australia, middle_east_to_australia),
        (is_europe, is_australia, europe_to_australia),
        (is_us_west, is_australia, us_west_to_australia),
    ]

    for origin_test, destination_test, route_builder in routes:
        if pair_matches(origin, destination, origin_test, destination_test):
            return dedupe_waypoints(route_builder(origin, destination))
        if pair_matches(origin, destination, destination_test, origin_test):
            return list(reversed(dedupe_waypoints(route_builder(destination, origin))))
    return generic_ocean_route(origin, destination)


def sea_route_waypoints(departure_port: str, arrival_port: str) -> List[RouteWaypoint]:
    origin = port_coordinate(departure_port)
    destination = port_coordinate(arrival_port)
    if not origin or not destination:
        return []
    return sea_route_between(origin, destination)
