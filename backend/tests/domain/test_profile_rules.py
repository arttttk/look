import pytest

from app.domain.entities import Location
from app.domain.errors import InvalidValue
from app.domain.profile_rules import make_location, normalize_name, validate_birth_year


class TestNormalizeName:
    def test_extra_whitespace_is_collapsed(self):
        # Arrange
        raw = "  Артём   Иванов \n"

        # Act
        name = normalize_name(raw)

        # Assert
        assert name == "Артём Иванов"

    @pytest.mark.parametrize("raw", [None, "", "   ", "\t\n"])
    def test_empty_means_no_name(self, raw):
        # Arrange: входные данные — параметры теста (raw)
        # Act
        name = normalize_name(raw)

        # Assert
        assert name is None

    def test_forty_characters_are_allowed(self):
        # Arrange
        raw = "я" * 40

        # Act
        name = normalize_name(raw)

        # Assert
        assert name == raw

    def test_forty_one_characters_are_rejected(self):
        # Arrange
        raw = "я" * 41

        # Act / Assert
        with pytest.raises(InvalidValue, match="40"):
            normalize_name(raw)


class TestValidateBirthYear:
    @pytest.mark.parametrize("year", [1930, 1998, 2016])
    def test_plausible_years_pass(self, year):
        # Arrange: сейчас 2026-й, младшему допустимому 10 лет

        # Act
        result = validate_birth_year(year, current_year=2026)

        # Assert
        assert result == year

    def test_none_passes_because_the_field_is_optional(self):
        # Arrange: подготовка не требуется
        # Act
        result = validate_birth_year(None, current_year=2026)

        # Assert
        assert result is None

    @pytest.mark.parametrize("year", [1929, 1800, 2017, 2026, 2999])
    def test_implausible_years_are_rejected(self, year):
        # Arrange: входные данные — параметры теста (year)
        # Act / Assert
        with pytest.raises(InvalidValue, match="год рождения"):
            validate_birth_year(year, current_year=2026)


class TestMakeLocation:
    def test_coordinates_are_rounded_to_about_a_kilometre(self):
        # Arrange
        lat, lon = 55.78874, 49.12214

        # Act
        location = make_location("Казань", "RU", lat, lon, "Europe/Moscow")

        # Assert
        assert location == Location("Казань", "RU", 55.79, 49.12, "Europe/Moscow")

    def test_country_is_uppercased_and_city_whitespace_collapsed(self):
        # Arrange: подготовка не требуется
        # Act
        location = make_location("  Нижний   Новгород ", " ru ", 56.3, 44.0, None)

        # Assert
        assert (location.city, location.country_code, location.timezone) == ("Нижний Новгород", "RU", None)

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"city": "   "}, "города"),
            ({"city": "я" * 81}, "города"),
            ({"country_code": "RUS"}, "страны"),
            ({"country_code": "1!"}, "страны"),
            ({"lat": 90.5}, "координаты"),
            ({"lat": -91}, "координаты"),
            ({"lon": 180.1}, "координаты"),
            ({"timezone": "x" * 65}, "часовой пояс"),
        ],
    )
    def test_invalid_input_is_rejected(self, kwargs, message):
        # Arrange
        valid = {"city": "Казань", "country_code": "RU", "lat": 55.0, "lon": 49.0, "timezone": None}

        # Act / Assert
        with pytest.raises(InvalidValue, match=message):
            make_location(**(valid | kwargs))

    def test_boundary_coordinates_are_allowed(self):
        # Arrange: подготовка не требуется
        # Act
        location = make_location("Полюс", "AQ", -90, 180, None)

        # Assert
        assert (location.lat, location.lon) == (-90, 180)
