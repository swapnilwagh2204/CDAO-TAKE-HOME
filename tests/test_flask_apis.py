import json
import pytest


def test_health_check(client):
    """Test the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == "Server is healthy"


def test_dump_data(client, mocker):
    """Test the /dump_data endpoint with mocked InfluxDB interactions."""

    # Mock InfluxDB write method
    mock_write_api = mocker.Mock()
    mocker.patch(
        "influxdb_client.InfluxDBClient.write_api", return_value=mock_write_api
    )

    # Simulate dumping weather data
    response = client.post(
        "/dump_data?user_id=test123&latitude=35.0522&longitude=-97.0892"
    )

    assert response.status_code == 200
    assert "successfully" in response.json["message"]
