# weather-cli

Look up current weather and forecasts with no API key.

## Usage

```bash
python3 -c "from weather import *; print(format_weather(WeatherClient().current('Berlin')))"
python3 -c "from weather import *; print(format_weather(WeatherClient().current('Berlin', units='fahrenheit')))"
python3 -c "from weather import *; print([format_weather(w) for w in WeatherClient().current_many(['Berlin', 'Paris'])])"
python3 -c "from weather import *; print(format_forecast(WeatherClient().forecast('Berlin')))"
python3 -c "from weather import *; print(describe_weather_code(61))"
```

## Features

- Geocoding and current conditions via Open-Meteo
- Celsius or Fahrenheit via current(city, units=...) and forecast(city, units=...)
- Multiple cities in order via current_many(cities, units=...)
- Injectable HTTP layer for offline tests
- Three-day forecast data with WeatherClient.forecast(city)
- Three-day forecast formatting with format_forecast(data)
- WMO weather code descriptions via describe_weather_code(code)

## Tests

```bash
python3 -m unittest -q
```

## Additional API

- `WeatherClient.current()` now returns a human-readable description derived from `describe_weather_code`.

## License

MIT
