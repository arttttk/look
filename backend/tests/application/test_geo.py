import pytest

from app.application.errors import Conflict, ProviderUnavailable
from app.application.use_cases.geo import GetCurrentWeather, SearchCities
from app.domain.errors import InvalidValue
from tests.factories import KAZAN, make_user


class TestSearchCities:
    def test_results_come_from_the_geocoder(self, geocoder):
        # Arrange
        use_case = SearchCities(geocoder)

        # Act
        cities = use_case.execute("Казань")

        # Assert
        assert [c.name for c in cities] == ["Казань", "Kazan"]

    def test_the_query_is_trimmed_before_it_is_sent(self, geocoder):
        # Arrange
        use_case = SearchCities(geocoder)

        # Act
        use_case.execute("  Казань  ")

        # Assert
        assert geocoder.queries == ["Казань"]

    @pytest.mark.parametrize("query", ["", " ", "к", " к ", "я" * 61])
    def test_a_query_of_wrong_length_is_refused_without_calling_the_geocoder(self, geocoder, query):
        # Arrange
        use_case = SearchCities(geocoder)

        # Act / Assert
        with pytest.raises(InvalidValue):
            use_case.execute(query)
        assert geocoder.queries == []

    @pytest.mark.parametrize("query", ["Ка", "я" * 60])
    def test_boundary_lengths_are_accepted(self, geocoder, query):
        # Arrange
        use_case = SearchCities(geocoder)

        # Act
        use_case.execute(query)

        # Assert
        assert geocoder.queries == [query]

    def test_an_unavailable_geocoder_is_reported(self, geocoder):
        # Arrange
        geocoder.fail = True
        use_case = SearchCities(geocoder)

        # Act / Assert
        with pytest.raises(ProviderUnavailable, match="поиска городов"):
            use_case.execute("Казань")


class TestGetCurrentWeather:
    def test_weather_is_taken_for_the_users_coordinates(self, weather):
        # Arrange
        user = make_user(location=KAZAN)
        use_case = GetCurrentWeather(weather)

        # Act
        current = use_case.execute(user)

        # Assert
        assert weather.calls == [(55.79, 49.12)]
        assert current.city == "Казань" and current.weather.temperature_c == 18.0

    def test_without_a_city_there_is_no_weather(self, weather):
        # Arrange
        user = make_user()
        use_case = GetCurrentWeather(weather)

        # Act / Assert
        with pytest.raises(Conflict, match="Город не указан"):
            use_case.execute(user)
        assert weather.calls == []

    def test_an_unavailable_provider_is_reported(self, weather):
        # Arrange
        weather.fail = True
        use_case = GetCurrentWeather(weather)

        # Act / Assert
        with pytest.raises(ProviderUnavailable, match="погоды"):
            use_case.execute(make_user(location=KAZAN))
