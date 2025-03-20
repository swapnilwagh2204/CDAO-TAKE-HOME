from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
import re
import os
from dotenv import load_dotenv
import hashlib
import requests
import math


load_dotenv()

# InfluxDB Configuration
INFLUXDB_URL = os.getenv("INFLUXDB_HOST_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_INIT_ADMIN_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_INIT_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_INIT_BUCKET")

# URLS:
NWS_BASE_URL = os.environ.get("NWS_BASE_URL")  # National Weather Service API URL
APP_BASE_URL = os.environ.get("APP_BASE_URL")  # Base URL for Flask API


# Initialize InfluxDB client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)


def get_forecast(office, grid_x, grid_y):
    """Fetches the current and hourly forecast data.

    Args:
        office (str): The office identifier for the forecast.
        grid_x (int): The x-coordinate of the grid point.
        grid_y (int): The y-coordinate of the grid point.

    Returns:
        tuple: A tuple containing the current forecast and hourly forecast data.
            The current forecast is a dictionary with the forecast data for the current period.
            The hourly forecast is a list of dictionaries, each containing the forecast data for an hourly period.
            If there is no new data available, both values in the tuple will be None.
    """
    forecast_url = f"{NWS_BASE_URL}/gridpoints/{office}/{grid_x},{grid_y}/forecast"
    hourly_url = f"{NWS_BASE_URL}/gridpoints/{office}/{grid_x},{grid_y}/forecast/hourly"

    headers = {"User-Agent": "flask-weather-app", "Cache-Control": "no-cache"}

    forecast_resp = requests.get(forecast_url, headers=headers)
    hourly_resp = requests.get(hourly_url, headers=headers)

    if forecast_resp.status_code == 304 or hourly_resp.status_code == 304:
        return None, None  # Handle no new data scenario

    if forecast_resp.status_code == 200 and hourly_resp.status_code == 200:
        return forecast_resp.json()["properties"]["periods"][0], hourly_resp.json()[
            "properties"
        ]["periods"][:24]

    return None, None


def get_gridpoint(latitude, longitude):
    """
    Fetches the gridpoint details for the given coordinates.

    Args:
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.

    Returns:
        tuple: A tuple containing the gridpoint details:
            - gridId (str): The grid ID.
            - gridX (int): The grid X coordinate.
            - gridY (int): The grid Y coordinate.
            - forecast_lat (float): The latitude of the forecast area.
            - forecast_lon (float): The longitude of the forecast area.
    """
    url = f"{NWS_BASE_URL}/points/{latitude},{longitude}"
    response = requests.get(url, headers={"User-Agent": "flask-weather-app"})
    if response.status_code == 200:
        data = response.json()

        # Extract forecast area coordinates
        rel_location = data["properties"]["relativeLocation"]["geometry"]["coordinates"]
        forecast_lat = rel_location[1]  # Latitude
        forecast_lon = rel_location[0]  # Longitude

        return (
            data["properties"]["gridId"],
            data["properties"]["gridX"],
            data["properties"]["gridY"],
            forecast_lat,
            forecast_lon,
        )
    return None, None, None, None, None


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the latitude, longitude, and great-circle distance between two points.

    Args:
        lat1 (float): Latitude of the first point in degrees.
        lon1 (float): Longitude of the first point in degrees.
        lat2 (float): Latitude of the second point in degrees.
        lon2 (float): Longitude of the second point in degrees.

    Returns:
        tuple: A tuple containing the absolute latitude distance in kilometers,
               the absolute longitude distance in kilometers, and the total distance
               between the two points in kilometers.
    """
    R = 6371  # Earth radius in km

    # Convert degrees to radians
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)

    # Differences in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula for great-circle distance
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    total_distance_km = R * c

    # Latitude and longitude distances (approximation)
    lat_distance_km = (lat1 - lat2) * 111
    lon_distance_km = (lon1 - lon2) * (111 * math.cos(lat1_rad))

    return abs(lat_distance_km), abs(lon_distance_km), total_distance_km


def extract_wind_speeds(wind_speed):
    numbers = list(map(int, re.findall(r"\d+", wind_speed)))
    return numbers if numbers else [0]  #


def parse_iso_time(iso_time):
    """Convert ISO 8601 time to Unix timestamp."""
    return int(datetime.fromisoformat(iso_time[:-6]).timestamp())


def generate_location_id(latitude, longitude):
    """Generate a unique location_id using city, state, latitude, and longitude."""
    raw_id = f"{latitude}_{longitude}"
    hashed_id = hashlib.md5(raw_id.encode()).hexdigest()[:8]  # Shortened hash
    return f"{hashed_id}"


def process_weather_data(data):
    """
    Process and transform weather data with dynamic location_id and distances.

    Args:
        data (dict): The weather data to be processed.

    Returns:
        dict: Transformed weather data ready for DB insertion.
    """

    # Extract city, state, and coordinates
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    # Generate dynamic location_id
    location_id = generate_location_id(latitude, longitude)

    # Extract distances
    lat_distance = float(data["latitude_distance_km"])
    lon_distance = float(data["longitude_distance_km"])
    total_distance = float(data["great_circle_distance_km"])

    # Daily forecast processing
    daily = data["current_forecast"]
    daily_time = parse_iso_time(daily["startTime"])
    daily_temp = float(daily["temperature"])
    daily_wind_speed = daily["windSpeed"]

    # Calculate average wind speed
    wind_speed_ls = extract_wind_speeds(daily_wind_speed)
    avg_wind_speed = sum(wind_speed_ls) / len(wind_speed_ls) if wind_speed_ls else 0.0

    # Prepare daily forecast data
    daily_forecast = {
        "location_id": location_id,
        "isDaytime": str(daily["isDaytime"]),
        "windDirection": daily["windDirection"],
        "temperature": daily_temp,
        "probabilityOfPrecipitation": daily["probabilityOfPrecipitation"]["value"],
        "windSpeed": avg_wind_speed,
        "latitude_distance_km": lat_distance,
        "longitude_distance_km": lon_distance,
        "great_circle_distance_km": total_distance,
        "time": daily_time,
    }

    # Hourly forecast processing
    hourly_forecasts = []

    for hour in data["hourly_forecast"]:
        hourly_time = parse_iso_time(hour["startTime"])
        hourly_temp = float(hour["temperature"])

        # Extract and normalize wind speed
        wind_speed = (
            float(hour["windSpeed"].split(" ")[0]) if " " in hour["windSpeed"] else 0.0
        )

        # Derived metrics
        temp_ratio = round(hourly_temp / daily_temp, 2) if daily_temp != 0 else 0
        wind_exceeds_avg = int(wind_speed > avg_wind_speed)
        dew_point = float(hour["dewpoint"]["value"])

        # Prepare hourly forecast data
        hourly_forecasts.append(
            {
                "location_id": location_id,
                "isDaytime": str(hour["isDaytime"]),
                "windDirection": hour["windDirection"],
                "temperature": hourly_temp,
                "probabilityOfPrecipitation": hour["probabilityOfPrecipitation"][
                    "value"
                ],
                "humidity": hour["relativeHumidity"]["value"],
                "windSpeed": wind_speed,
                "dewpoint": dew_point,
                "temperature_ratio": temp_ratio,
                "wind_exceeds_avg": wind_exceeds_avg,
                "latitude_distance_km": lat_distance,
                "longitude_distance_km": lon_distance,
                "great_circle_distance_km": total_distance,
                "time": hourly_time,
            }
        )

    # Return structured and transformed data
    return {"daily": daily_forecast, "hourly": hourly_forecasts}


def dump_weather_data_to_db(processed_data):
    """
    Write processed weather data into InfluxDB.

    Args:
        processed_data (dict): Transformed weather data.
    """

    # Write daily forecast data to InfluxDB
    daily = processed_data["daily"]

    daily_point = (
        Point("weather_forecast")
        .tag("location_id", daily["location_id"])
        .tag("isDaytime", daily["isDaytime"])
        .tag("windDirection", daily["windDirection"])
        .field("temperature", daily["temperature"])
        .field("probabilityOfPrecipitation", daily["probabilityOfPrecipitation"])
        .field("windSpeed", daily["windSpeed"])
        .field("latitude_distance_km", daily["latitude_distance_km"])
        .field("longitude_distance_km", daily["longitude_distance_km"])
        .field("great_circle_distance_km", daily["great_circle_distance_km"])
        .time(daily["time"], WritePrecision.S)
    )

    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=daily_point)

    # Write hourly forecasts to InfluxDB
    for hour in processed_data["hourly"]:
        hourly_point = (
            Point("weather_hourly")
            .tag("location_id", hour["location_id"])
            .tag("isDaytime", hour["isDaytime"])
            .tag("windDirection", hour["windDirection"])
            .field("temperature", hour["temperature"])
            .field("probabilityOfPrecipitation", hour["probabilityOfPrecipitation"])
            .field("humidity", hour["humidity"])
            .field("windSpeed", hour["windSpeed"])
            .field("dewpoint", hour["dewpoint"])
            .field("temperature_ratio", hour["temperature_ratio"])
            .field("wind_exceeds_avg", hour["wind_exceeds_avg"])
            .field("latitude_distance_km", hour["latitude_distance_km"])
            .field("longitude_distance_km", hour["longitude_distance_km"])
            .field("great_circle_distance_km", hour["great_circle_distance_km"])
            .time(hour["time"], WritePrecision.S)
        )
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=hourly_point)


#  Key Benefits
# Unique location_id:


# Avoids hardcoding location IDs.
# Automatically generates IDs based on location data.
# Enhanced InfluxDB Records:
