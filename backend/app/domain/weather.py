"""Погода и то, как она влияет на подбор образа."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Weather:
    temperature_c: float
    feels_like_c: float
    condition: str  # clear | cloudy | fog | rain | snow | storm
    label: str  # по-русски, для интерфейса: «облачно»
    is_day: bool
    precipitation_mm: float
    wind_kmh: float
    observed_at: str  # локальное время места, ISO


@dataclass(frozen=True)
class Conditions:
    """Погода, сведённая к тому, что нужно подбору: сколько тепла нужно образу и идёт ли дождь."""

    target_warmth: int
    rainy: bool


# Коды WMO (их отдаёт Open-Meteo) -> (условие, подпись)
_WMO: list[tuple[range | tuple[int, ...], str, str]] = [
    ((0,), "clear", "ясно"),
    ((1,), "clear", "малооблачно"),
    ((2,), "cloudy", "переменная облачность"),
    ((3,), "cloudy", "пасмурно"),
    ((45, 48), "fog", "туман"),
    ((51, 53, 55, 56, 57), "rain", "морось"),
    ((61, 63, 65, 66, 67), "rain", "дождь"),
    ((71, 73, 75, 77), "snow", "снег"),
    ((80, 81, 82), "rain", "ливень"),
    ((85, 86), "snow", "снегопад"),
    ((95, 96, 99), "storm", "гроза"),
]


def describe_code(code: int) -> tuple[str, str]:
    for codes, condition, label in _WMO:
        if code in codes:
            return condition, label
    return "cloudy", "облачно"


def target_warmth(feels_like_c: float) -> int:
    """Сколько «тепла» должно быть в образе (сумма тепла верха, низа и верхней одежды).
    Базовые футболка и джинсы дают ~3: на 20-25° этого хватает, дальше нужны слои.
    25°+ -> 2, 20° -> 3, 10° -> 5, 0° -> 7, -10° и холоднее -> 9."""
    value = 2 + math.floor((25 - feels_like_c) / 5 + 0.5)
    return max(2, min(9, value))


def conditions_from(weather: Weather) -> Conditions:
    rainy = weather.condition in ("rain", "storm") or weather.precipitation_mm >= 0.3
    return Conditions(target_warmth=target_warmth(weather.feels_like_c), rainy=rainy)
