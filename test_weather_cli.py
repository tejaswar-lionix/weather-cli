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


class ForecastTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
