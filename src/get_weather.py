# src/get_weather.py
import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables from .env file
load_dotenv()

def get_weather_forecast(location: str, tz_offset: int) -> dict:
    """Get structured weather data with error handling"""
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    
    if not OPENWEATHER_API_KEY:
        raise ValueError("OpenWeather API key not found in environment variables")

    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return {
            "temp": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"]
        }
        
    except Exception as e:
        print(f"\n⚠️ Weather API error: {str(e)}")
        return {}