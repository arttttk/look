from dataclasses import dataclass

from app.application.errors import Conflict
from app.application.ports import Geocoder, WeatherProvider
from app.domain.entities import User
from app.domain.errors import InvalidValue
from app.domain.geo import City
from app.domain.weather import Weather

MIN_QUERY = 2
MAX_QUERY = 60


@dataclass(frozen=True)
class CurrentWeather:
    city: str
    weather: Weather


class SearchCities:
    """Поиск города по названию — для выбора места вручную."""

    def __init__(self, geocoder: Geocoder):
        self._geocoder = geocoder

    def execute(self, query: str) -> list[City]:
        text = query.strip()
        if not MIN_QUERY <= len(text) <= MAX_QUERY:
            raise InvalidValue(f"Название города: от {MIN_QUERY} до {MAX_QUERY} символов")
        return self._geocoder.search(text)


class GetCurrentWeather:
    """Погода сейчас в городе пользователя."""

    def __init__(self, weather: WeatherProvider):
        self._weather = weather

    def execute(self, user: User) -> CurrentWeather:
        if user.location is None:
            raise Conflict("Город не указан")
        weather = self._weather.fetch(user.location.lat, user.location.lon)
        return CurrentWeather(city=user.location.city, weather=weather)
