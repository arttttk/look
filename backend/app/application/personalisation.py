import logging
from dataclasses import dataclass

from app.application.errors import ProviderUnavailable
from app.application.ports import WeatherProvider
from app.domain.entities import User
from app.domain.regions import regional_styles
from app.domain.weather import Conditions, Weather, conditions_from

logger = logging.getLogger("look.personalisation")


@dataclass(frozen=True)
class Context:
    """Всё, что влияет на подбор образов для пользователя прямо сейчас."""

    department: str
    styles: list[str]  # стили пользователя или, если «не определился», подсказка по региону
    budget: str | None
    weather: Weather | None
    conditions: Conditions | None


class PersonalisationService:
    def __init__(self, weather: WeatherProvider):
        self._weather = weather

    def context_for(self, user: User) -> Context:
        """Нет места или погода недоступна — подбираем без неё, а не падаем."""
        weather = self._current_weather(user)
        return Context(
            department=user.department,
            styles=list(user.styles)
            or regional_styles(user.location.country_code if user.location else None),
            budget=user.budget,
            weather=weather,
            conditions=conditions_from(weather) if weather else None,
        )

    def _current_weather(self, user: User) -> Weather | None:
        if user.location is None:
            return None
        try:
            return self._weather.fetch(user.location.lat, user.location.lon)
        except ProviderUnavailable:
            logger.warning("Погода недоступна, подбираем образы без неё")
            return None
