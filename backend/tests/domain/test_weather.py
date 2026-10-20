import pytest

from app.domain.weather import Conditions, Weather, conditions_from, describe_code, target_warmth


def make_weather(**overrides) -> Weather:
    values = {
        "temperature_c": 10.0, "feels_like_c": 10.0, "condition": "cloudy", "label": "облачно",
        "is_day": True, "precipitation_mm": 0.0, "wind_kmh": 3.0, "observed_at": "2026-10-20T12:00",
    } | overrides  # fmt: skip
    return Weather(**values)


@pytest.mark.parametrize(
    ("feels_like", "expected"),
    [(35, 2), (25, 2), (20, 3), (18, 3), (10, 5), (0, 7), (-10, 9), (-40, 9)],
)
def test_target_warmth_grows_as_it_gets_colder(feels_like, expected):
    # Arrange: входные данные — параметры теста (feels_like, expected)
    # Act
    warmth = target_warmth(feels_like)

    # Assert
    assert warmth == expected


def test_target_warmth_never_decreases_when_the_temperature_drops():
    # Arrange
    temperatures = range(40, -41, -1)

    # Act
    values = [target_warmth(t) for t in temperatures]

    # Assert
    assert values == sorted(values)


@pytest.mark.parametrize(
    ("code", "condition", "label"),
    [
        (0, "clear", "ясно"),
        (2, "cloudy", "переменная облачность"),
        (3, "cloudy", "пасмурно"),
        (45, "fog", "туман"),
        (63, "rain", "дождь"),
        (73, "snow", "снег"),
        (82, "rain", "ливень"),
        (95, "storm", "гроза"),
        (999, "cloudy", "облачно"),  # неизвестный код — нейтральный ответ, а не ошибка
    ],
)
def test_wmo_codes_are_translated(code, condition, label):
    # Arrange: входные данные — параметры теста (code, condition, label)
    # Act
    result = describe_code(code)

    # Assert
    assert result == (condition, label)


class TestConditionsFrom:
    def test_dry_cool_day(self):
        # Arrange
        weather = make_weather(feels_like_c=10.0)

        # Act
        conditions = conditions_from(weather)

        # Assert
        assert conditions == Conditions(target_warmth=5, rainy=False)

    def test_feels_like_matters_more_than_the_air_temperature(self):
        # Arrange: на термометре +5, но ветер даёт ощущаемые -5
        weather = make_weather(temperature_c=5.0, feels_like_c=-5.0)

        # Act
        conditions = conditions_from(weather)

        # Assert
        assert conditions.target_warmth == target_warmth(-5.0)

    @pytest.mark.parametrize("condition", ["rain", "storm"])
    def test_rain_and_storm_are_rainy(self, condition):
        # Arrange
        weather = make_weather(condition=condition)

        # Act
        rainy = conditions_from(weather).rainy

        # Assert
        assert rainy is True

    @pytest.mark.parametrize(("mm", "rainy"), [(0.0, False), (0.2, False), (0.3, True), (4.0, True)])
    def test_noticeable_precipitation_counts_as_rain_even_if_the_code_says_otherwise(self, mm, rainy):
        # Arrange
        weather = make_weather(condition="cloudy", precipitation_mm=mm)

        # Act
        result = conditions_from(weather).rainy

        # Assert
        assert result is rainy
