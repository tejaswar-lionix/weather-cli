#!/usr/bin/env python3
"""Fetch current weather from Open-Meteo without API keys."""
import json
import urllib.parse
import urllib.request


def _http_get(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def describe_weather_code(code):
    if code == 0:
        return "clear sky"
    if 1 <= code <= 3:
        return "partly cloudy"
    if code in (45, 48):
        return "fog"
    if 51 <= code <= 57:
        return "drizzle"
    if 61 <= code <= 67:
        return "rain"
    if 71 <= code <= 77:
        return "snow"
    if 80 <= code <= 82:
        return "rain showers"
    if 95 <= code <= 99:
        return "thunderstorm"
    return "unknown"


def format_weather(data):
    return (
        f"{data['city']}: {data['temperature']} {data.get('unit', 'C')}, "
        f"{data['description']}"
    )


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

    def current(self, city, units="celsius"):
        if units not in ("celsius", "fahrenheit"):
            raise ValueError("units must be 'celsius' or 'fahrenheit'")
        latitude, longitude, name = self.geocode(city)
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true",
        }
        if units == "fahrenheit":
            params["temperature_unit"] = "fahrenheit"
        query = urllib.parse.urlencode(params)
        payload = self._get("https://api.open-meteo.com/v1/forecast?" + query)
        current = payload["current_weather"]
        return {
            "city": name,
            "temperature": current["temperature"],
            "description": f"weather code {current['weathercode']}",
            "unit": "F" if units == "fahrenheit" else "C",
        }

    def current_many(self, cities, units="celsius"):
        return [self.current(city, units=units) for city in cities]

    def forecast(self, city, units="celsius"):
        if units not in ("celsius", "fahrenheit"):
            raise ValueError("units must be 'celsius' or 'fahrenheit'")
        latitude, longitude, name = self.geocode(city)
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_min,temperature_2m_max",
            "forecast_days": 3,
            "timezone": "auto",
        }
        if units == "fahrenheit":
            params["temperature_unit"] = "fahrenheit"
        query = urllib.parse.urlencode(params)
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
        return {
            "city": name,
            "days": days,
            "unit": "F" if units == "fahrenheit" else "C",
        }


def format_forecast(data):
    """Format up to three forecast days, one line per day."""
    unit = data.get("unit", "C")
    lines = []
    for day in data["days"][:3]:
        lines.append(
            f"{data['city']} {day['date']}: {day['min']}..{day['max']} {unit}"
        )
    return "\n".join(lines)
