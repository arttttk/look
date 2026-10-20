import pytest

from tests.api.conftest import KAZAN, TOKYO, login, onboard


class TestGetProfile:
    def test_a_new_profile_is_empty(self, client, sender):
        # Arrange
        headers = login(client, sender, "+79991234567")

        # Act
        profile = client.get("/me", headers=headers).json()

        # Assert
        assert profile | {"id": None} == {
            "id": None, "phone": "+79991234567", "email": None, "name": None, "birth_year": None,
            "onboarded": False, "department": "any", "styles": [], "budget": None,
            "location": None, "regional_styles": [],
        }  # fmt: skip

    def test_profiles_are_private(self, client, sender):
        # Arrange
        alice, bob = login(client, sender), login(client, sender)
        onboard(client, alice, name="Алиса", styles=["sport"])

        # Act
        profile = client.get("/me", headers=bob).json()

        # Assert
        assert profile["name"] is None and profile["styles"] == []


class TestPatchProfile:
    def test_only_the_sent_fields_change(self, client, user):
        # Arrange
        client.patch("/me", headers=user, json={"name": "  Артём   Иванов ", "birth_year": 1998})

        # Act
        profile = client.patch("/me", headers=user, json={"department": "men", "budget": "mid"}).json()

        # Assert
        assert (profile["name"], profile["birth_year"]) == ("Артём Иванов", 1998)
        assert (profile["department"], profile["budget"]) == ("men", "mid")

    def test_the_change_is_persisted(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        patched = client.patch("/me", headers=user, json={"name": "Артём", "styles": ["street"]}).json()

        # Assert
        assert client.get("/me", headers=user).json() == patched

    def test_null_clears_optional_fields(self, client, user):
        # Arrange
        onboard(client, user, name="Артём", birth_year=2000, budget="low", location=KAZAN)

        # Act
        cleared = client.patch(
            "/me", headers=user, json={"name": None, "birth_year": None, "budget": None, "location": None}
        ).json()

        # Assert
        assert (cleared["name"], cleared["birth_year"], cleared["budget"], cleared["location"]) == (None,) * 4
        assert cleared["onboarded"] is True

    @pytest.mark.parametrize("field", ["department", "styles", "onboarded"])
    def test_null_is_refused_for_required_fields(self, client, user, field):
        # Arrange: фикстуры (client, user) и параметры теста (field)
        # Act
        response = client.patch("/me", headers=user, json={field: None})

        # Assert
        assert response.status_code == 422

    def test_an_empty_name_clears_it(self, client, user):
        # Arrange
        onboard(client, user, name="Артём")

        # Act
        profile = client.patch("/me", headers=user, json={"name": "   "}).json()

        # Assert
        assert profile["name"] is None

    def test_styles_are_deduplicated_in_order(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        profile = onboard(client, user, styles=["street", "minimal", "street"])

        # Assert
        assert profile["styles"] == ["street", "minimal"]

    @pytest.mark.parametrize(
        "body",
        [
            {"styles": ["nonsense"]},
            {"department": "kids"},
            {"budget": "cheap"},
            {"birth_year": 1800},
            {"birth_year": 2999},
            {"birth_year": "ninety"},
            {"name": "я" * 41},
            {"unknown": 1},
            {"onboarded": "maybe"},
            {"location": {**KAZAN, "lat": 123}},
            {"location": {**KAZAN, "lon": -200}},
            {"location": {**KAZAN, "country_code": "RUS"}},
            {"location": {**KAZAN, "country_code": "1!"}},
            {"location": {**KAZAN, "city": "   "}},
            {"location": {"city": "Казань"}},
        ],
    )
    def test_invalid_bodies_get_422_and_change_nothing(self, client, user, body):
        # Arrange
        before = client.get("/me", headers=user).json()

        # Act
        response = client.patch("/me", headers=user, json=body)

        # Assert
        assert response.status_code == 422
        assert client.get("/me", headers=user).json() == before

    def test_an_empty_patch_is_a_harmless_no_op(self, client, user):
        # Arrange
        before = client.get("/me", headers=user).json()

        # Act
        response = client.patch("/me", headers=user, json={})

        # Assert
        assert response.status_code == 200 and response.json() == before

    def test_a_patch_needs_a_token(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        response = client.patch("/me", json={"name": "x"})

        # Assert
        assert response.status_code == 401


class TestLocation:
    def test_coordinates_are_rounded_and_country_uppercased(self, client, user):
        # Arrange
        location = {**KAZAN, "country_code": "ru", "city": " Казань "}

        # Act
        profile = onboard(client, user, location=location)

        # Assert
        assert profile["location"] == {
            "city": "Казань", "country_code": "RU", "lat": 55.79, "lon": 49.12, "timezone": "Europe/Moscow",
        }  # fmt: skip

    def test_the_timezone_is_optional(self, client, user):
        # Arrange
        location = {key: value for key, value in KAZAN.items() if key != "timezone"}

        # Act
        profile = onboard(client, user, location=location)

        # Assert
        assert profile["location"]["timezone"] is None

    def test_regional_styles_follow_the_country(self, client, user):
        # Arrange
        russia = onboard(client, user, location=KAZAN)["regional_styles"]
        japan = onboard(client, user, location=TOKYO)["regional_styles"]
        # Act
        nowhere = onboard(client, user, location={**KAZAN, "country_code": "ZZ"})["regional_styles"]

        # Assert
        assert (russia, japan, nowhere) == (["casual", "classic"], ["minimal", "street"], [])


class TestCitySearch:
    def test_cities_are_returned_in_the_apps_format(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        cities = client.get("/geo/cities", headers=user, params={"q": "Казань"}).json()

        # Assert
        assert [c["city"] for c in cities] == ["Казань", "Kazan"]
        assert cities[0] == {
            "city": "Казань", "region": "Татарстан", "country": "Россия", "country_code": "RU",
            "lat": 55.78874, "lon": 49.12214, "timezone": "Europe/Moscow",
        }  # fmt: skip

    @pytest.mark.parametrize("query", ["к", " ", "я" * 61])
    def test_a_query_of_the_wrong_length_gets_422(self, client, user, query):
        # Arrange: фикстуры (client, user) и параметры теста (query)
        # Act
        response = client.get("/geo/cities", headers=user, params={"q": query})

        # Assert
        assert response.status_code == 422

    def test_a_missing_query_gets_422(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        response = client.get("/geo/cities", headers=user)

        # Assert
        assert response.status_code == 422

    def test_an_unavailable_geocoder_gets_502(self, client, user, geocoder):
        # Arrange
        geocoder.fail = True

        # Act
        response = client.get("/geo/cities", headers=user, params={"q": "Казань"})

        # Assert
        assert response.status_code == 502 and "поиска городов" in response.json()["detail"]

    def test_search_needs_a_token(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        response = client.get("/geo/cities", params={"q": "Казань"})

        # Assert
        assert response.status_code == 401


class TestWeather:
    def test_without_a_city_the_weather_is_a_conflict(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        response = client.get("/weather", headers=user)

        # Assert
        assert response.status_code == 409

    def test_weather_for_the_users_city(self, client, user):
        # Arrange
        onboard(client, user, location=KAZAN)

        # Act
        response = client.get("/weather", headers=user)

        # Assert
        assert response.status_code == 200
        assert response.json() == {
            "city": "Казань", "temperature_c": 18.0, "feels_like_c": 18.0, "condition": "cloudy",
            "label": "облачно", "is_day": True, "precipitation_mm": 0.0, "wind_kmh": 5.0,
            "observed_at": "2026-10-20T12:00",
        }  # fmt: skip

    def test_the_provider_is_asked_once_for_the_same_city(self, client, sender, weather):
        # Arrange
        first, second = login(client, sender), login(client, sender)
        onboard(client, first, location=KAZAN)
        onboard(client, second, location=KAZAN)

        # Act
        client.get("/weather", headers=first)
        client.get("/weather", headers=first)
        client.get("/weather", headers=second)

        # Assert
        assert len(weather.calls) == 1

    def test_the_cache_expires_after_fifteen_minutes(self, client, user, weather, clock):
        # Arrange
        onboard(client, user, location=KAZAN)
        client.get("/weather", headers=user)
        clock.advance(minutes=16)

        # Act
        client.get("/weather", headers=user)

        # Assert
        assert len(weather.calls) == 2

    def test_an_unavailable_provider_gets_502(self, client, user, weather):
        # Arrange
        onboard(client, user, location=KAZAN)
        weather.fail = True

        # Act
        response = client.get("/weather", headers=user)

        # Assert
        assert response.status_code == 502 and "погоды" in response.json()["detail"]


def test_meta_lists_everything_the_forms_need(client):
    # Arrange: состояние задают фикстуры (client)
    # Act
    meta = client.get("/meta").json()

    # Assert
    assert [s["id"] for s in meta["styles"]] == ["minimal", "street", "classic", "casual", "sport", "vintage"]
    assert [d["id"] for d in meta["departments"]] == ["men", "women", "any"]
    assert [b["id"] for b in meta["budgets"]] == ["low", "mid", "high"]
    assert {c["id"] for c in meta["colors"]} >= {"black", "white", "red"}
    assert [c["id"] for c in meta["categories"]][:4] == ["outerwear", "top", "bottom", "shoes"]
