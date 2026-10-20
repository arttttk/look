import threading
from datetime import datetime, timedelta

from app.application.ports import Clock, WeatherProvider
from app.domain.weather import Weather

_MAX_ENTRIES = 2000


class CachedWeatherProvider:
    """Погода с кэшем: сто пользователей из одного города — один запрос к провайдеру за период."""

    def __init__(self, provider: WeatherProvider, clock: Clock, ttl_seconds: int):
        self._provider = provider
        self._clock = clock
        self._ttl = timedelta(seconds=ttl_seconds)
        self._cache: dict[tuple[float, float], tuple[datetime, Weather]] = {}
        self._lock = threading.Lock()

    def fetch(self, lat: float, lon: float) -> Weather:
        key = (round(lat, 1), round(lon, 1))  # ~11 км: для погоды достаточно
        now = self._clock.now()

        with self._lock:
            hit = self._cache.get(key)
            if hit and now - hit[0] < self._ttl:
                return hit[1]

        weather = self._provider.fetch(lat, lon)  # без блокировки: сеть медленная
        with self._lock:
            if len(self._cache) >= _MAX_ENTRIES:
                self._cache.clear()
            self._cache[key] = (now, weather)
        return weather

    def close(self) -> None:
        close = getattr(self._provider, "close", None)
        if close:
            close()
