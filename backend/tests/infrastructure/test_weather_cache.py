import pytest

from app.application.errors import ProviderUnavailable
from app.infrastructure.weather_cache import CachedWeatherProvider
from tests.fakes import FakeWeatherProvider, FrozenClock


@pytest.fixture()
def cached(weather, clock) -> CachedWeatherProvider:
    return CachedWeatherProvider(weather, clock, ttl_seconds=900)


def test_the_first_request_goes_to_the_provider(cached, weather):
    # Arrange: состояние задают фикстуры (cached, weather)
    # Act
    result = cached.fetch(55.79, 49.12)

    # Assert
    assert result.temperature_c == 18.0 and len(weather.calls) == 1


def test_the_second_request_for_the_same_place_is_served_from_the_cache(cached, weather):
    # Arrange
    cached.fetch(55.79, 49.12)

    # Act
    cached.fetch(55.79, 49.12)

    # Assert
    assert len(weather.calls) == 1


def test_nearby_places_share_one_cache_entry(cached, weather):
    # Arrange: меньше 0.05° — одна и та же клетка в ~11 км
    cached.fetch(55.79, 49.12)

    # Act
    cached.fetch(55.81, 49.14)

    # Assert
    assert len(weather.calls) == 1


def test_a_distant_place_is_fetched_separately(cached, weather):
    # Arrange
    cached.fetch(55.79, 49.12)

    # Act
    cached.fetch(59.93, 30.31)

    # Assert
    assert len(weather.calls) == 2


def test_the_cache_expires_after_the_ttl(cached, weather, clock):
    # Arrange
    cached.fetch(55.79, 49.12)
    clock.advance(seconds=900)

    # Act
    cached.fetch(55.79, 49.12)

    # Assert
    assert len(weather.calls) == 2


def test_the_cache_still_holds_a_second_before_the_ttl(cached, weather, clock):
    # Arrange
    cached.fetch(55.79, 49.12)
    clock.advance(seconds=899)

    # Act
    cached.fetch(55.79, 49.12)

    # Assert
    assert len(weather.calls) == 1


def test_a_fresh_fetch_returns_the_new_weather(cached, weather, clock):
    # Arrange
    cached.fetch(55.79, 49.12)
    weather.temperature_c = 5.0
    clock.advance(seconds=901)

    # Act
    result = cached.fetch(55.79, 49.12)

    # Assert
    assert result.temperature_c == 5.0


def test_a_provider_failure_is_passed_on_and_nothing_is_cached(cached, weather):
    # Arrange
    weather.fail = True
    with pytest.raises(ProviderUnavailable):
        cached.fetch(55.79, 49.12)
    weather.fail = False

    # Act
    result = cached.fetch(55.79, 49.12)

    # Assert
    assert result.temperature_c == 18.0 and len(weather.calls) == 2


def test_close_is_forwarded_to_the_provider_when_it_has_one():
    # Arrange
    class Closable(FakeWeatherProvider):
        closed = False

        def close(self):
            self.closed = True

    provider = Closable()
    cached = CachedWeatherProvider(provider, FrozenClock(), 900)

    # Act
    cached.close()

    # Assert
    assert provider.closed is True


def test_close_is_harmless_when_the_provider_has_nothing_to_close(cached):
    # Arrange: состояние задают фикстуры (cached)
    # Act
    result = cached.close()

    # Assert
    assert result is None  # исключения нет, закрывать нечего


def test_a_full_cache_is_emptied_instead_of_growing_forever(weather, clock, monkeypatch):
    # Arrange
    monkeypatch.setattr("app.infrastructure.weather_cache._MAX_ENTRIES", 2)
    cached = CachedWeatherProvider(weather, clock, ttl_seconds=900)
    cached.fetch(10.0, 10.0)
    cached.fetch(20.0, 20.0)
    cached.fetch(30.0, 30.0)  # кэш полон — очищается, остаётся только новое место
    calls_before = len(weather.calls)

    # Act
    cached.fetch(10.0, 10.0)  # первое место уже забыто
    cached.fetch(30.0, 30.0)  # последнее ещё помнится

    # Assert
    assert len(weather.calls) == calls_before + 1
