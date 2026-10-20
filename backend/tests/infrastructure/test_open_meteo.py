"""Адаптеры Open-Meteo проверяются на подставном HTTP-транспорте: настоящая сеть не нужна."""

import httpx
import pytest

from app.application.errors import ProviderUnavailable
from app.config import Settings
from app.infrastructure.open_meteo import OpenMeteoGeocoder, OpenMeteoWeather

SETTINGS = Settings(geocoding_url="https://geo.test/search", forecast_url="https://forecast.test/v1")


def client_for(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def json_response(body, status=200):
    return lambda request: httpx.Response(status, json=body)


GEOCODING_BODY = {
    "results": [
        {"name": "Казань", "admin1": "Кировская область", "country": "Россия", "country_code": "ru",
         "latitude": 59.16, "longitude": 49.93, "timezone": "Europe/Kirov", "population": None},
        {"name": "Казань", "admin1": "Татарстан", "country": "Россия", "country_code": "RU",
         "latitude": 55.79, "longitude": 49.12, "timezone": "Europe/Moscow", "population": 1243500},
        {"name": "Казань", "country_code": "RU", "latitude": 57.87, "longitude": 48.51, "population": 120},
    ]
}  # fmt: skip

WEATHER_BODY = {
    "current": {
        "time": "2026-10-20T11:00", "temperature_2m": 3.4, "apparent_temperature": 0.3,
        "weather_code": 63, "is_day": 1, "precipitation": 1.2, "wind_speed_10m": 5.4,
    }
}  # fmt: skip


class TestGeocoder:
    def test_the_request_asks_for_russian_results(self):
        # Arrange
        seen = {}

        def handler(request):
            seen.update(dict(request.url.params))
            return httpx.Response(200, json=GEOCODING_BODY)

        geocoder = OpenMeteoGeocoder(SETTINGS, client_for(handler))

        # Act
        geocoder.search("Казань")

        # Assert
        assert seen["name"] == "Казань" and seen["language"] == "ru" and seen["format"] == "json"

    def test_bigger_cities_come_first(self):
        # Arrange
        geocoder = OpenMeteoGeocoder(SETTINGS, client_for(json_response(GEOCODING_BODY)))

        # Act
        cities = geocoder.search("Казань")

        # Assert
        assert [c.population for c in cities] == [1243500, 120, None]

    def test_fields_are_mapped_and_the_country_code_is_uppercased(self):
        # Arrange
        geocoder = OpenMeteoGeocoder(SETTINGS, client_for(json_response(GEOCODING_BODY)))

        # Act
        top = geocoder.search("Казань")[0]

        # Assert
        assert (top.name, top.region, top.country, top.country_code) == (
            "Казань",
            "Татарстан",
            "Россия",
            "RU",
        )
        assert (top.lat, top.lon, top.timezone) == (55.79, 49.12, "Europe/Moscow")

    def test_optional_fields_may_be_missing(self):
        # Arrange
        geocoder = OpenMeteoGeocoder(SETTINGS, client_for(json_response(GEOCODING_BODY)))

        # Act
        bare = geocoder.search("Казань")[1]

        # Assert
        assert bare.region is None and bare.country is None and bare.timezone is None

    def test_at_most_eight_cities_are_returned(self):
        # Arrange
        many = {
            "results": [
                {"name": f"Город{i}", "country_code": "RU", "latitude": 1, "longitude": 1, "population": i}
                for i in range(10)
            ]
        }
        geocoder = OpenMeteoGeocoder(SETTINGS, client_for(json_response(many)))

        # Act
        cities = geocoder.search("Город")

        # Assert
        assert len(cities) == 8 and cities[0].population == 9

    def test_entries_without_coordinates_or_country_are_dropped(self):
        # Arrange
        body = {
            "results": [
                {"name": "Без координат", "country_code": "RU"},
                {"name": "Без страны", "latitude": 1, "longitude": 1},
                {"country_code": "RU", "latitude": 1, "longitude": 1},
                {"name": "Годный", "country_code": "RU", "latitude": 1, "longitude": 2},
            ]
        }
        geocoder = OpenMeteoGeocoder(SETTINGS, client_for(json_response(body)))

        # Act
        cities = geocoder.search("x")

        # Assert
        assert [c.name for c in cities] == ["Годный"]

    @pytest.mark.parametrize("body", [{}, {"results": None}, {"results": []}])
    def test_no_results_is_an_empty_list(self, body):
        # Arrange
        geocoder = OpenMeteoGeocoder(SETTINGS, client_for(json_response(body)))

        # Act
        cities = geocoder.search("нигде")

        # Assert
        assert cities == []

    @pytest.mark.parametrize("status", [429, 500, 503])
    def test_an_error_status_means_the_provider_is_unavailable(self, status):
        # Arrange
        geocoder = OpenMeteoGeocoder(SETTINGS, client_for(json_response({}, status)))

        # Act / Assert
        with pytest.raises(ProviderUnavailable, match="поиска городов"):
            geocoder.search("Казань")

    def test_a_network_failure_means_the_provider_is_unavailable(self):
        # Arrange
        def handler(request):
            raise httpx.ConnectError("no route")

        geocoder = OpenMeteoGeocoder(SETTINGS, client_for(handler))

        # Act / Assert
        with pytest.raises(ProviderUnavailable):
            geocoder.search("Казань")

    def test_a_reply_that_is_not_json_means_the_provider_is_unavailable(self):
        # Arrange
        geocoder = OpenMeteoGeocoder(
            SETTINGS, client_for(lambda r: httpx.Response(200, text="<html>oops</html>"))
        )

        # Act / Assert
        with pytest.raises(ProviderUnavailable):
            geocoder.search("Казань")


class TestWeather:
    def test_the_request_names_the_coordinates_and_the_needed_fields(self):
        # Arrange
        seen = {}

        def handler(request):
            seen.update(dict(request.url.params))
            return httpx.Response(200, json=WEATHER_BODY)

        provider = OpenMeteoWeather(SETTINGS, client_for(handler))

        # Act
        provider.fetch(55.79, 49.12)

        # Assert
        assert (seen["latitude"], seen["longitude"]) == ("55.79", "49.12")
        assert "apparent_temperature" in seen["current"] and seen["timezone"] == "auto"

    def test_the_reply_is_mapped_to_a_weather_object(self):
        # Arrange
        provider = OpenMeteoWeather(SETTINGS, client_for(json_response(WEATHER_BODY)))

        # Act
        weather = provider.fetch(55.79, 49.12)

        # Assert
        assert (weather.temperature_c, weather.feels_like_c) == (3.4, 0.3)
        assert (weather.condition, weather.label) == ("rain", "дождь")
        assert (weather.is_day, weather.precipitation_mm, weather.wind_kmh) == (True, 1.2, 5.4)
        assert weather.observed_at == "2026-10-20T11:00"

    def test_night_is_recognised(self):
        # Arrange
        body = {"current": WEATHER_BODY["current"] | {"is_day": 0}}
        provider = OpenMeteoWeather(SETTINGS, client_for(json_response(body)))

        # Act
        weather = provider.fetch(1, 1)

        # Assert
        assert weather.is_day is False

    @pytest.mark.parametrize("status", [400, 429, 500])
    def test_an_error_status_means_the_provider_is_unavailable(self, status):
        # Arrange
        provider = OpenMeteoWeather(SETTINGS, client_for(json_response({}, status)))

        # Act / Assert
        with pytest.raises(ProviderUnavailable, match="погоды"):
            provider.fetch(1, 1)

    @pytest.mark.parametrize(
        "body",
        [{}, {"current": {}}, {"current": {**WEATHER_BODY["current"], "temperature_2m": "warm"}}],
    )
    def test_an_unexpected_reply_means_the_provider_is_unavailable(self, body):
        # Arrange
        provider = OpenMeteoWeather(SETTINGS, client_for(json_response(body)))

        # Act / Assert
        with pytest.raises(ProviderUnavailable):
            provider.fetch(1, 1)

    def test_a_timeout_means_the_provider_is_unavailable(self):
        # Arrange
        def handler(request):
            raise httpx.ReadTimeout("slow")

        provider = OpenMeteoWeather(SETTINGS, client_for(handler))

        # Act / Assert
        with pytest.raises(ProviderUnavailable):
            provider.fetch(1, 1)


@pytest.mark.parametrize("adapter", [OpenMeteoGeocoder, OpenMeteoWeather])
def test_closing_an_adapter_closes_its_http_client(adapter):
    # Arrange
    http = client_for(json_response({}))
    instance = adapter(SETTINGS, http)

    # Act
    instance.close()

    # Assert
    assert http.is_closed
