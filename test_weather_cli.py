import unittest

from weather import WeatherClient, format_weather


class FakeClient(WeatherClient):
    def __init__(self, results=None):
        self.results = results if results is not None else [
            {"latitude": 52.52, "longitude": 13.41, "name": "Berlin"}
        ]
        super().__init__(http_get=self.fake_get)

    def fake_get(self, url):
        if "geocoding" in url:
            return {"results": self.results}
        return {"current_weather": {"temperature": 12.3, "weathercode": 3}}


class FakeForecastClient(WeatherClient):
    def __init__(self):
        super().__init__(http_get=self.fake_get)

    def fake_get(self, url):
        if "geocoding" in url:
            return {
                "results": [
                    {"latitude": 52.52, "longitude": 13.41, "name": "Berlin"}
                ]
            }
        return {
            "daily": {
                "time": ["2026-11-12", "2026-11-13", "2026-11-14"],
                "temperature_2m_min": [4, 3, 5],
                "temperature_2m_max": [9, 8, 10],
            }
        }


class FakeUnitClient(WeatherClient):
    def __init__(self):
        self.urls = []
        super().__init__(http_get=self.fake_get)

    def fake_get(self, url):
        self.urls.append(url)
        if "geocoding" in url:
            return {
                "results": [
                    {"latitude": 52.52, "longitude": 13.41, "name": "Berlin"}
                ]
            }
        if "current_weather" in url:
            return {"current_weather": {"temperature": 54.1, "weathercode": 3}}
        return {
            "daily": {
                "time": ["2026-11-12"],
                "temperature_2m_min": [39.2],
                "temperature_2m_max": [48.2],
            }
        }


class WeatherTests(unittest.TestCase):
    def test_format_weather(self):
        data = {
            "city": "Berlin",
            "temperature": 12.3,
            "description": "weather code 3",
        }
        self.assertEqual(format_weather(data), "Berlin: 12.3 C, weather code 3")

    def test_current_weather(self):
        data = FakeClient().current("Berlin")
        self.assertEqual(data["city"], "Berlin")
        self.assertEqual(data["temperature"], 12.3)

    def test_unknown_city_raises(self):
        with self.assertRaises(LookupError):
            FakeClient(results=[]).current("Atlantis")


class WeatherCodeTests(unittest.TestCase):
    def test_representative_codes(self):
        from weather import describe_weather_code

        self.assertEqual(describe_weather_code(0), "clear sky")
        self.assertEqual(describe_weather_code(2), "partly cloudy")
        self.assertEqual(describe_weather_code(45), "fog")
        self.assertEqual(describe_weather_code(53), "drizzle")
        self.assertEqual(describe_weather_code(63), "rain")
        self.assertEqual(describe_weather_code(73), "snow")
        self.assertEqual(describe_weather_code(81), "rain showers")
        self.assertEqual(describe_weather_code(96), "thunderstorm")

    def test_unknown_code(self):
        from weather import describe_weather_code

        self.assertEqual(describe_weather_code(42), "unknown")


class FakeManyClient(WeatherClient):
    def __init__(self):
        self.urls = []
        super().__init__(http_get=self.fake_get)

    def fake_get(self, url):
        self.urls.append(url)
        if "geocoding" in url:
            if "name=Paris" in url:
                return {
                    "results": [
                        {"latitude": 48.85, "longitude": 2.35, "name": "Paris"}
                    ]
                }
            if "name=Atlantis" in url:
                return {"results": []}
            return {
                "results": [
                    {"latitude": 52.52, "longitude": 13.41, "name": "Berlin"}
                ]
            }
        return {"current_weather": {"temperature": 12.3, "weathercode": 3}}


class CurrentManyTests(unittest.TestCase):
    def test_returns_current_weather_for_each_city(self):
        data = FakeManyClient().current_many(["Berlin", "Paris"])
        self.assertEqual(len(data), 2)
        self.assertEqual([entry["city"] for entry in data], ["Berlin", "Paris"])
        self.assertEqual([entry["temperature"] for entry in data], [12.3, 12.3])

    def test_preserves_city_order(self):
        data = FakeManyClient().current_many(["Paris", "Berlin"])
        self.assertEqual([entry["city"] for entry in data], ["Paris", "Berlin"])

    def test_fahrenheit_passthrough(self):
        client = FakeManyClient()
        data = client.current_many(["Berlin", "Paris"], units="fahrenheit")
        self.assertEqual([entry["unit"] for entry in data], ["F", "F"])
        self.assertIn("temperature_unit=fahrenheit", client.urls[-1])

    def test_geocode_errors_propagate(self):
        with self.assertRaises(LookupError):
            FakeManyClient().current_many(["Berlin", "Atlantis"])


class ForecastTests(unittest.TestCase):
    def test_forecast_returns_three_days(self):
        data = FakeForecastClient().forecast("Berlin")
        self.assertEqual(data["city"], "Berlin")
        self.assertEqual(len(data["days"]), 3)
        self.assertEqual(
            data["days"][0], {"date": "2026-11-12", "min": 4, "max": 9}
        )
        self.assertEqual(
            data["days"][2], {"date": "2026-11-14", "min": 5, "max": 10}
        )

    def test_format_forecast_limits_three_days(self):
        from weather import format_forecast

        data = {
            "city": "Berlin",
            "days": [
                {"date": "2026-11-12", "min": 4, "max": 9},
                {"date": "2026-11-13", "min": 3, "max": 8},
                {"date": "2026-11-14", "min": 5, "max": 10},
                {"date": "2026-11-15", "min": 1, "max": 6},
            ],
        }
        lines = format_forecast(data).splitlines()
        self.assertEqual(len(lines), 3)
        self.assertIn("2026-11-12: 4..9 C", lines[0])


class UnitTests(unittest.TestCase):
    def test_current_fahrenheit_requests_unit_and_returns_values(self):
        client = FakeUnitClient()
        data = client.current("Berlin", units="fahrenheit")
        self.assertIn("temperature_unit=fahrenheit", client.urls[-1])
        self.assertEqual(data["temperature"], 54.1)
        self.assertEqual(data["unit"], "F")

    def test_forecast_fahrenheit_requests_unit_and_formats_values(self):
        from weather import format_forecast

        client = FakeUnitClient()
        data = client.forecast("Berlin", units="fahrenheit")
        self.assertIn("temperature_unit=fahrenheit", client.urls[-1])
        self.assertEqual(data["days"][0]["min"], 39.2)
        self.assertEqual(data["unit"], "F")
        self.assertIn("39.2..48.2 F", format_forecast(data))

    def test_celsius_omits_unit_parameter(self):
        client = FakeUnitClient()
        client.current("Berlin")
        self.assertNotIn("temperature_unit", client.urls[-1])

    def test_invalid_units_raise(self):
        client = FakeUnitClient()
        with self.assertRaises(ValueError):
            client.current("Berlin", units="kelvin")
        with self.assertRaises(ValueError):
            client.forecast("Berlin", units="kelvin")


if __name__ == "__main__":
    unittest.main()
