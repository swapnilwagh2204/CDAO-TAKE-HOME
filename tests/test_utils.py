import pytest
from math import isclose
from utils import calculate_distance, extract_wind_speeds, parse_iso_time
from datetime import datetime


def test_same_location():
    lat1, lon1 = 40.7128, -74.0060  # New York City coordinates
    lat2, lon2 = 40.7128, -74.0060  # Same location
    lat_dist, lon_dist, total_dist = calculate_distance(lat1, lon1, lat2, lon2)

    assert lat_dist == 0, f"Expected 0, but got {lat_dist}"
    assert lon_dist == 0, f"Expected 0, but got {lon_dist}"
    assert total_dist == 0, f"Expected 0, but got {total_dist}"


def test_new_york_to_los_angeles():
    lat1, lon1 = 40.7128, -74.0060  # New York City coordinates
    lat2, lon2 = 34.0522, -118.2437  # Los Angeles coordinates
    lat_dist, lon_dist, total_dist = calculate_distance(lat1, lon1, lat2, lon2)

    # Since this is a real-world example, we'll check that the values are close enough
    assert lat_dist > 0, f"Expected positive latitude distance, but got {lat_dist}"
    assert lon_dist > 0, f"Expected positive longitude distance, but got {lon_dist}"
    assert total_dist > 0, f"Expected positive total distance, but got {total_dist}"
    assert isclose(total_dist, 3935.748, rel_tol=1e-2), (
        f"Expected total distance close to 3935.748 km, but got {total_dist}"
    )


def test_small_distance():
    lat1, lon1 = 40.7128, -74.0060  # New York City coordinates
    lat2, lon2 = 40.7138, -74.0070  # Slightly different location
    lat_dist, lon_dist, total_dist = calculate_distance(lat1, lon1, lat2, lon2)

    assert lat_dist > 0, f"Expected positive latitude distance, but got {lat_dist}"
    assert lon_dist > 0, f"Expected positive longitude distance, but got {lon_dist}"
    assert total_dist > 0, f"Expected positive total distance, but got {total_dist}"
    # Total distance should be small, as the two points are very close
    assert total_dist < 1, (
        f"Expected total distance less than 1 km, but got {total_dist}"
    )


def test_equator_and_prime_meridian():
    lat1, lon1 = (
        0.0,
        0.0,
    )  # Coordinates at the intersection of the equator and prime meridian
    lat2, lon2 = 10.0, 10.0  # A point 10 degrees north and 10 degrees east
    lat_dist, lon_dist, total_dist = calculate_distance(lat1, lon1, lat2, lon2)

    assert lat_dist > 0, f"Expected positive latitude distance, but got {lat_dist}"
    assert lon_dist > 0, f"Expected positive longitude distance, but got {lon_dist}"
    assert total_dist > 0, f"Expected positive total distance, but got {total_dist}"
    # A rough check on the total distance
    assert isclose(total_dist, 1572.96, rel_tol=1e-2), (
        f"Expected total distance close to 1572.96 km, but got {total_dist}"
    )


def test_extract_wind_speeds():
    assert extract_wind_speeds("Wind speed is 15 km/h") == [15]
    assert extract_wind_speeds("Wind speed: 20-25 km/h") == [20, 25]
    assert extract_wind_speeds("No wind speed data") == [0]
    assert extract_wind_speeds("Wind speed 10, 15, and 20 km/h") == [10, 15, 20]
    assert extract_wind_speeds("") == [0]


def test_parse_iso_time():
    assert parse_iso_time("2023-10-01T12:00:00+00:00") == int(
        datetime(2023, 10, 1, 12, 0).timestamp()
    )
    assert parse_iso_time("2023-10-01T12:00:00-05:00") != int(
        datetime(2023, 10, 1, 17, 0).timestamp()
    )
    assert parse_iso_time("2023-10-01T12:00:00+05:30") != int(
        datetime(2023, 10, 1, 6, 30).timestamp()
    )


if __name__ == "__main__":
    pytest.main()
