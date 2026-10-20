"""Правила профиля: что считается допустимым именем, годом рождения, местоположением."""

from app.domain.entities import Location
from app.domain.errors import InvalidValue

MAX_NAME_LENGTH = 40
MIN_BIRTH_YEAR = 1930
MIN_AGE = 10
MAX_CITY_LENGTH = 80
MAX_TIMEZONE_LENGTH = 64


def normalize_name(value: str | None) -> str | None:
    """Лишние пробелы схлопываются; пустое имя — это «имени нет»."""
    if value is None:
        return None
    name = " ".join(value.split())
    if len(name) > MAX_NAME_LENGTH:
        raise InvalidValue(f"Имя не длиннее {MAX_NAME_LENGTH} символов")
    return name or None


def validate_birth_year(value: int | None, current_year: int) -> int | None:
    if value is not None and not MIN_BIRTH_YEAR <= value <= current_year - MIN_AGE:
        raise InvalidValue("Некорректный год рождения")
    return value


def make_location(city: str, country_code: str, lat: float, lon: float, timezone: str | None) -> Location:
    """Собирает место из присланных данных. Координаты огрубляются до ~1 км: для погоды точнее
    не нужно, а хранить точную позицию человека незачем."""
    clean_city = " ".join(city.split())
    if not clean_city or len(clean_city) > MAX_CITY_LENGTH:
        raise InvalidValue("Некорректное название города")

    country = country_code.strip().upper()
    if len(country) != 2 or not country.isalpha():
        raise InvalidValue("Нужен двухбуквенный код страны")

    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise InvalidValue("Некорректные координаты")

    if timezone is not None and len(timezone) > MAX_TIMEZONE_LENGTH:
        raise InvalidValue("Некорректный часовой пояс")

    return Location(
        city=clean_city, country_code=country, lat=round(lat, 2), lon=round(lon, 2), timezone=timezone
    )
