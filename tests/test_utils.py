import pytest
from utils import process_weather_data


def test_process_weather_data():
    """Test the weather data transformation logic."""

    # Mock input data
    mock_data = {
        "properties": {
            "periods": [
                {
                    "startTime": "2025-03-21T10:00:00Z",
                    "temperature": 22,
                    "windSpeed": "10 mph",
                    "shortForecast": "Sunny",
                }
            ]
        }
    }

    result = process_weather_data(mock_data)

    # Validate transformation
    assert len(result) == 1
    assert result[0]["temperature"] == 22
    assert result[0]["wind_speed"] == "10 mph"
    assert result[0]["forecast"] == "Sunny"
    assert result[0]["time"] == "2025-03-21T10:00:00Z"
