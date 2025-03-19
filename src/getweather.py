from unittest.mock import patch
import get_wheather

# Define mock response data
mock_weather_response = {
    "coord": {"lat": 39.91, "lon": 116.39},
    "main": {
        "temp": 15.0, "feels_like": 14.5, "temp_min": 13.0, "temp_max": 16.0,
        "humidity": 50
    },
    "weather": [{"description": "clear sky"}],
    "wind": {"speed": 3.5, "deg": 180},
    "clouds": {"all": 10},
}

mock_forecast_response = {
    "list": [
        {
            "dt": 1711406400,  # Mock timestamp
            "main": {
                "temp": 16.0, "feels_like": 15.5, "temp_min": 14.0, "temp_max": 18.0,
                "humidity": 55
            },
            "weather": [{"description": "partly cloudy"}],
            "wind": {"speed": 4.0, "deg": 190},
            "clouds": {"all": 30},
        }
    ]
}

# Patch the requests.get method
with patch("requests.get") as mock_get:
    # Simulate API responses
    mock_get.side_effect = [
        # First call returns current weather
        type("Response", (), {"json": lambda: mock_weather_response, "raise_for_status": lambda: None}),
        # Second call returns forecast
        type("Response", (), {"json": lambda: mock_forecast_response, "raise_for_status": lambda: None}),
    ]
    
    # Call function with test values
    forecast_data = get_wheather.get_weather_forecast("Beijing", 8)

    # Print results
    print("=== Today's Forecast ===")
    for entry in forecast_data.get("today", []):
        print(entry)

    print("\n=== Tomorrow's Forecast ===")
    for entry in forecast_data.get("tomorrow", []):
        print(entry)

    # Check for errors
    if "error" in forecast_data:
        print("\nError:", forecast_data["error"])

