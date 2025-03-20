import logging
from flask import Flask, request, jsonify
from flasgger import Swagger
from dotenv import load_dotenv
from utils import (
    dump_weather_data_to_db,
    process_weather_data,
    get_forecast,
    get_gridpoint,
)

# Load environment variables
load_dotenv()

# Flask app initialization
app = Flask(__name__)
Swagger(app)

# Standard logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(),
    ],
)


# --------------------
# Health Check Endpoint
# --------------------
@app.route("/health", methods=["GET"])
def health_check():
    """API Endpoint for Flask server health check."""
    logging.info("Health check request received.")
    return jsonify("Server is healthy"), 200


# --------------------
# Dump Data Endpoint
# --------------------
@app.route("/dump_data", methods=["POST"])
def dump_data():
    """
    API Endpoint to fetch weather data, dump it into the database, and return the stored data.
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
            description: Successfully dumped and retrieved weather data
        400:
            description: Missing or invalid parameters
        500:
            description: Server error while processing data
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
        # ✅ Fetch gridpoint details
        office, grid_x, grid_y = get_gridpoint(latitude, longitude)
        if not all([office, grid_x, grid_y]):
            logging.error("Failed to retrieve gridpoint data.")
            return jsonify({"error": "Failed to retrieve gridpoint data."}), 500

        # ✅ Fetch weather data
        current_forecast, hourly_forecast = get_forecast(office, grid_x, grid_y)
        if not current_forecast or not hourly_forecast:
            logging.error("Failed to retrieve forecast data.")
            return jsonify({"error": "Failed to retrieve forecast data."}), 500

        # ✅ Create a weather data object
        weather_data = {
            "user_id": user_id,
            "latitude": latitude,
            "longitude": longitude,
            "current_forecast": current_forecast,
            "hourly_forecast": hourly_forecast,
        }

        # ✅ Process and store the weather data
        processed_data = process_weather_data(weather_data)
        dump_weather_data_to_db(processed_data)

        logging.info("Successfully dumped weather data into the database.")

        # ✅ Return the dumped weather data in the response
        return jsonify(
            {
                "message": "Data successfully dumped into the database.",
                "dumped_data": processed_data,
            }
        ), 200

    except Exception as e:
        logging.exception(f"Failed to insert data into the database: {str(e)}")
        return jsonify(
            {"error": f"Failed to insert data into the database: {str(e)}"}
        ), 500


# --------------------
# Main Execution
# --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
