# weather-cli

Look up current weather and forecasts with no API key.

## Usage

```bash
python3 -c "from weather import *; print(format_weather(WeatherClient().current('Berlin')))"
```

## Features

- Geocoding and current conditions via Open-Meteo
- Injectable HTTP layer for offline tests
- Three-day forecast formatting with format_forecast(data)

## Tests

```bash
python3 -m unittest -q
```

## License

MIT
