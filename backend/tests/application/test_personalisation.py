from app.application.personalisation import PersonalisationService
from app.domain.weather import Conditions
from tests.factories import KAZAN, TOKYO, make_user


class TestWeather:
    def test_without_a_location_there_is_no_weather_and_the_provider_is_not_asked(
        self, personalisation, weather
    ):
        # Arrange
        user = make_user()

        # Act
        ctx = personalisation.context_for(user)

        # Assert
        assert ctx.weather is None and ctx.conditions is None
        assert weather.calls == []

    def test_with_a_location_the_weather_becomes_conditions(self, personalisation, weather):
        # Arrange
        weather.temperature_c = 10.0
        user = make_user(location=KAZAN)

        # Act
        ctx = personalisation.context_for(user)

        # Assert
        assert ctx.weather.temperature_c == 10.0
        assert ctx.conditions == Conditions(target_warmth=5, rainy=False)

    def test_rain_is_detected(self, personalisation, weather):
        # Arrange
        weather.condition, weather.precipitation_mm = "rain", 2.0
        user = make_user(location=KAZAN)

        # Act
        ctx = personalisation.context_for(user)

        # Assert
        assert ctx.conditions.rainy is True

    def test_a_weather_outage_degrades_to_no_weather_instead_of_failing(self, personalisation, weather):
        # Arrange
        weather.fail = True
        user = make_user(location=KAZAN)

        # Act
        ctx = personalisation.context_for(user)

        # Assert
        assert ctx.weather is None and ctx.conditions is None


class TestStyles:
    def test_users_own_styles_are_used_as_they_are(self, personalisation):
        # Arrange: Япония подсказала бы minimal/street, но человек выбрал спорт
        user = make_user(styles=["sport"], location=TOKYO)

        # Act
        ctx = personalisation.context_for(user)

        # Assert
        assert ctx.styles == ["sport"]

    def test_undecided_user_gets_the_regional_hint(self, personalisation):
        # Arrange
        user = make_user(styles=[], location=TOKYO)

        # Act
        ctx = personalisation.context_for(user)

        # Assert
        assert ctx.styles == ["minimal", "street"]

    def test_undecided_user_without_a_location_gets_no_hint(self, personalisation):
        # Arrange
        user = make_user(styles=[])

        # Act
        ctx = personalisation.context_for(user)

        # Assert
        assert ctx.styles == []

    def test_the_users_style_list_is_not_shared_with_the_context(self, personalisation):
        # Arrange
        user = make_user(styles=["sport"])
        ctx = personalisation.context_for(user)

        # Act
        ctx.styles.append("street")

        # Assert
        assert user.styles == ["sport"]


def test_department_and_budget_are_passed_through(weather):
    # Arrange
    user = make_user(department="women", budget="mid")

    # Act
    ctx = PersonalisationService(weather).context_for(user)

    # Assert
    assert (ctx.department, ctx.budget) == ("women", "mid")
