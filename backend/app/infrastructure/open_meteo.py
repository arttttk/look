"""Open-Meteo: поиск города и погода (бесплатно, без ключа). Приложение ходит только к нам —
провайдера можно заменить, не трогая клиент."""

import httpx

from app.application.errors import ProviderUnavailable
from app.config import Settings
from app.domain.geo import City
from app.domain.weather import Weather, describe_code


class OpenMeteoGeocoder:
    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self._url = settings.geocoding_url
        self._client = client or httpx.Client(timeout=settings.http_timeout_seconds)

    def search(self, query: str) -> list[City]:
        try:
            response = self._client.get(
                self._url, params={"name": query, "count": 10, "language": "ru", "format": "json"}
            )
            response.raise_for_status()
            results = response.json().get("results") or []
        except (httpx.HTTPError, ValueError, AttributeError) as error:
            raise ProviderUnavailable("Сервис поиска городов недоступен") from error

        cities = [
            City(
                name=r["name"],
                region=r.get("admin1"),
                country=r.get("country"),
                country_code=r["country_code"].upper(),
                lat=r["latitude"],
                lon=r["longitude"],
                timezone=r.get("timezone"),
                population=r.get("population"),
            )
            for r in results
            if r.get("name") and r.get("country_code") and "latitude" in r and "longitude" in r
        ]
        # Поиск отдаёт и крошечные деревни с тем же названием — крупные города вперёд.
        cities.sort(key=lambda c: -(c.population or 0))
        return cities[:8]

    def close(self) -> None:
        self._client.close()


class OpenMeteoWeather:
    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self._url = settings.forecast_url
        self._client = client or httpx.Client(timeout=settings.http_timeout_seconds)

    def fetch(self, lat: float, lon: float) -> Weather:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,weather_code,is_day,precipitation,wind_speed_10m",
            "timezone": "auto",
        }
        try:
            response = self._client.get(self._url, params=params)
            response.raise_for_status()
            current = response.json()["current"]
            condition, label = describe_code(int(current["weather_code"]))
            return Weather(
                temperature_c=float(current["temperature_2m"]),
                feels_like_c=float(current["apparent_temperature"]),
                condition=condition,
                label=label,
                is_day=bool(current["is_day"]),
                precipitation_mm=float(current["precipitation"]),
                wind_kmh=float(current["wind_speed_10m"]),
                observed_at=str(current["time"]),
            )
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise ProviderUnavailable("Сервис погоды недоступен") from error

    def close(self) -> None:
        self._client.close()
