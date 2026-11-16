#!/usr/bin/env python3
"""Fetch current weather from Open-Meteo without API keys."""
import json
import urllib.parse
import urllib.request


def _http_get(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def format_weather(data):
    return f"{data['city']}: {data['temperature']} C, {data['description']}"


class WeatherClient:
    def __init__(self, http_get=_http_get):
        self._get = http_get

    def geocode(self, city):
        query = urllib.parse.urlencode({"name": city, "count": 1})
        payload = self._get("https://geocoding-api.open-meteo.com/v1/search?" + query)
        results = payload.get("results") or []
        if not results:
            raise LookupError(f"city not found: {city}")
        result = results[0]
        return result["latitude"], result["longitude"], result["name"]

    def current(self, city):
        latitude, longitude, name = self.geocode(city)
        query = urllib.parse.urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "current_weather": "true",
            }
        )
        payload = self._get("https://api.open-meteo.com/v1/forecast?" + query)
        current = payload["current_weather"]
        return {
            "city": name,
            "temperature": current["temperature"],
            "description": f"weather code {current['weathercode']}",
        }

    def forecast(self, city):
        latitude, longitude, name = self.geocode(city)
        query = urllib.parse.urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "temperature_2m_min,temperature_2m_max",
                "forecast_days": 3,
                "timezone": "auto",
            }
        )
        payload = self._get("https://api.open-meteo.com/v1/forecast?" + query)
        daily = payload["daily"]
        days = [
            {"date": date, "min": minimum, "max": maximum}
            for date, minimum, maximum in zip(
                daily["time"],
                daily["temperature_2m_min"],
                daily["temperature_2m_max"],
            )
        ]
        return {"city": name, "days": days}


def format_forecast(data):
    """Format up to three forecast days, one line per day."""
    lines = []
    for day in data["days"][:3]:
        lines.append(f"{data['city']} {day['date']}: {day['min']}..{day['max']} C")
    return "\n".join(lines)
