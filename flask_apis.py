import logging
from flask import Flask, request, jsonify
from flasgger import Swagger
import requests
from dotenv import load_dotenv
from utils import (
    process_weather_data,
    dump_weather_data_to_db,
    get_forecast,
    get_gridpoint,
    calculate_distance,
    APP_BASE_URL,
)

# Load environment variables
load_dotenv()

# Flask app initialization
app = Flask(__name__)
Swagger(app)

# standard logging congifuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # Log to file
        logging.StreamHandler(),  # Log to console
    ],
)


# Health Check Endpoint
@app.route("/health", methods=["GET"])
def health_check():
    """API Endpoint for Flask server health check.
    ---
    responses:
        200:
            description: Server is healthy
    """
    logging.info("Health check request received.")
    return jsonify("Server is healthy"), 200


# Get Weather Endpoint
@app.route("/get_weather", methods=["GET"])
def get_weather():
    """API Endpoint to fetch weather data.
    ---
    parameters:
      - name: user_id
        in: query
        type: string
        required: true
        description: Unique identifier for the user
      - name: latitude
        in: query
        type: number
        format: float
        required: true
        description: Latitude of the location
      - name: longitude
        in: query
        type: number
        format: float
        required: true
        description: Longitude of the location
    responses:
      200:
        description: Successfully retrieved weather data
      400:
        description: Missing or invalid parameters
      500:
        description: Server error while fetching data
    """

    user_id = request.args.get("user_id")
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")

    logging.info(
        f"Received weather request: user_id={user_id}, lat={latitude}, lon={longitude}"
    )

    if not all([user_id, latitude, longitude]):
        logging.warning("Missing parameters in get_weather request.")
        return jsonify(
            {"error": "Missing parameters. Provide user_id, latitude, and longitude."}
        ), 400

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        logging.error("Invalid latitude or longitude format.")
        return jsonify(
            {"error": "Invalid latitude or longitude format. Must be a float."}
        ), 400

    try:
        office, grid_x, grid_y, forecast_lat, forecast_lon = get_gridpoint(
            latitude, longitude
        )
        if not all([office, grid_x, grid_y, forecast_lat, forecast_lon]):
            logging.error("Failed to retrieve gridpoint data.")
            return jsonify({"error": "Failed to retrieve gridpoint data."}), 500

        current_forecast, hourly_forecast = get_forecast(office, grid_x, grid_y)
        if not current_forecast or not hourly_forecast:
            logging.error("Failed to retrieve forecast data.")
            return jsonify({"error": "Failed to retrieve forecast data."}), 500

        lat_distance, lon_distance, total_distance = calculate_distance(
            latitude, longitude, forecast_lat, forecast_lon
        )

        logging.info("Successfully fetched and processed weather data.")

        return jsonify(
            {
                "user_id": user_id,
                "latitude": latitude,
                "longitude": longitude,
                "forecast_latitude": forecast_lat,
                "forecast_longitude": forecast_lon,
                "latitude_distance_km": round(lat_distance, 4),
                "longitude_distance_km": round(lon_distance, 4),
                "great_circle_distance_km": round(total_distance, 4),
                "current_forecast": current_forecast,
                "hourly_forecast": hourly_forecast,
            }
        ), 200

    except Exception as e:
        logging.exception(f"Error in get_weather: {str(e)}")
        return jsonify(
            {"error": "Internal server error while fetching weather data."}
        ), 500


# Dump Data Endpoint
@app.route("/dump_data", methods=["POST"])
def dump_data():
    """API Endpoint to dump weather data into the database.
    ---
    parameters:
        - name: user_id
          in: query
          type: string
          required: true
          description: Unique identifier for the user
        - name: latitude
          in: query
          type: number
          format: float
          required: true
          description: Latitude of the location
        - name: longitude
          in: query
          type: number
          format: float
          required: true
          description: Longitude of the location
    responses:
        200:
            description: Successfully dumped weather data
        400:
            description: Missing or invalid parameters
        500:
            description: Server error while dumping data
    """
    user_id = request.args.get("user_id")
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")

    logging.info(
        f"Received dump_data request: user_id={user_id}, lat={latitude}, lon={longitude}"
    )

    if not all([user_id, latitude, longitude]):
        logging.warning("Missing parameters in dump_data request.")
        return jsonify(
            {"error": "Missing parameters. Provide user_id, latitude, and longitude."}
        ), 400

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        logging.error("Invalid latitude or longitude format.")
        return jsonify(
            {"error": "Invalid latitude or longitude format. Must be a float."}
        ), 400

    try:
        response = requests.get(
            f"{APP_BASE_URL}/get_weather",
            params={"user_id": user_id, "latitude": latitude, "longitude": longitude},
            headers={"User-Agent": "flask-weather-app"},
        )

        if response.status_code != 200:
            logging.error(
                f"Failed to fetch weather data. Status: {response.status_code}"
            )
            return jsonify(
                {
                    "error": f"Failed to fetch weather data. Status: {response.status_code}"
                }
            ), 500

        weather_data = response.json()  # Get the JSON data from the response

    except requests.RequestException as e:
        logging.exception("Failed to fetch weather data.")
        return jsonify({"error": f"Failed to fetch weather data: {str(e)}"}), 500

    try:
        processed_data = process_weather_data(weather_data)
        dump_weather_data_to_db(processed_data)

        logging.info("Successfully dumped weather data into the database.")
        return jsonify({"message": "Data successfully dumped into the database."}), 200

    except Exception as e:
        logging.exception(f"Failed to insert data into the database: {str(e)}")
        return jsonify(
            {"error": f"Failed to insert data into the database: {str(e)}"}
        ), 500


# Main Execution
if __name__ == "__main__":
    app.run(debug=True)
