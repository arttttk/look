import pytest

from app.application.errors import NotFound
from app.application.use_cases.profile import UNSET, LocationInput, ProfileChanges, UpdateProfile
from app.domain.entities import Location
from app.domain.errors import InvalidValue
from tests.application.helpers import persist
from tests.factories import make_user

KAZAN_INPUT = LocationInput("Казань", "RU", 55.78874, 49.12214, "Europe/Moscow")


@pytest.fixture()
def update(uow, clock) -> UpdateProfile:
    return UpdateProfile(uow, clock)


@pytest.fixture()
def user(database):
    stored = make_user()
    persist(database, stored)
    return stored


def saved(database, user_id):
    return database.tables.users[user_id]


class TestApplyingChanges:
    def test_only_the_sent_fields_change(self, update, user, database):
        # Arrange
        department_before = saved(database, user.id).department

        # Act
        result = update.execute(user.id, ProfileChanges(name="Артём"))

        # Assert
        assert result.name == "Артём" and result.department == department_before == "any"

    def test_the_result_is_what_was_saved(self, update, user, database):
        # Arrange
        changes = ProfileChanges(
            name="Артём", birth_year=1998, department="men", budget="mid", onboarded=True
        )

        # Act
        result = update.execute(user.id, changes)

        # Assert
        assert saved(database, user.id) == result
        assert (result.birth_year, result.department, result.budget, result.onboarded) == (
            1998,
            "men",
            "mid",
            True,
        )

    def test_an_earlier_value_survives_an_unrelated_update(self, update, user, database):
        # Arrange
        update.execute(user.id, ProfileChanges(name="Артём", styles=["street"]))

        # Act
        update.execute(user.id, ProfileChanges(budget="low"))

        # Assert
        stored = saved(database, user.id)
        assert (stored.name, stored.styles, stored.budget) == ("Артём", ["street"], "low")

    def test_styles_are_deduplicated_keeping_the_order_of_choice(self, update, user):
        # Arrange
        changes = ProfileChanges(styles=["street", "minimal", "street"])

        # Act
        result = update.execute(user.id, changes)

        # Assert
        assert result.styles == ["street", "minimal"]

    def test_an_empty_list_of_styles_means_undecided(self, update, user):
        # Arrange
        update.execute(user.id, ProfileChanges(styles=["street"]))

        # Act
        result = update.execute(user.id, ProfileChanges(styles=[]))

        # Assert
        assert result.styles == []

    def test_name_whitespace_is_collapsed(self, update, user):
        # Arrange
        changes = ProfileChanges(name="  Артём   Иванов ")

        # Act
        result = update.execute(user.id, changes)

        # Assert
        assert result.name == "Артём Иванов"

    def test_a_blank_name_clears_the_name(self, update, user):
        # Arrange
        update.execute(user.id, ProfileChanges(name="Артём"))

        # Act
        result = update.execute(user.id, ProfileChanges(name="   "))

        # Assert
        assert result.name is None

    def test_birth_year_is_checked_against_the_current_year_of_the_clock(self, update, user, clock):
        # Arrange: часы стоят на 2026-м, значит 2016-й — младше допустимого возраста не бывает
        ok = ProfileChanges(birth_year=2016)
        too_young = ProfileChanges(birth_year=2017)

        # Act
        result = update.execute(user.id, ok)

        # Assert
        assert result.birth_year == 2016
        with pytest.raises(InvalidValue):
            update.execute(user.id, too_young)


class TestClearingFields:
    def test_none_clears_every_optional_field(self, update, user):
        # Arrange
        update.execute(
            user.id,
            ProfileChanges(name="Артём", birth_year=2000, budget="low", location=KAZAN_INPUT),
        )

        # Act
        result = update.execute(
            user.id, ProfileChanges(name=None, birth_year=None, budget=None, location=None)
        )

        # Assert
        assert (result.name, result.birth_year, result.budget, result.location) == (None, None, None, None)

    @pytest.mark.parametrize("field", ["onboarded", "department", "styles"])
    def test_required_fields_cannot_be_cleared(self, update, user, field):
        # Arrange
        changes = ProfileChanges(**{field: None})

        # Act / Assert
        with pytest.raises(InvalidValue, match=field):
            update.execute(user.id, changes)

    def test_unset_means_leave_it_alone(self, update, user):
        # Arrange
        update.execute(user.id, ProfileChanges(name="Артём", location=KAZAN_INPUT))

        # Act
        result = update.execute(user.id, ProfileChanges(name=UNSET, location=UNSET, budget="mid"))

        # Assert
        assert result.name == "Артём" and result.location is not None and result.budget == "mid"


class TestLocation:
    def test_coordinates_are_rounded_before_saving(self, update, user, database):
        # Arrange
        changes = ProfileChanges(location=KAZAN_INPUT)

        # Act
        update.execute(user.id, changes)

        # Assert
        assert saved(database, user.id).location == Location("Казань", "RU", 55.79, 49.12, "Europe/Moscow")

    def test_country_code_is_normalised(self, update, user):
        # Arrange
        changes = ProfileChanges(location=LocationInput(" Казань ", "ru", 55.0, 49.0))

        # Act
        result = update.execute(user.id, changes)

        # Assert
        assert (result.location.city, result.location.country_code) == ("Казань", "RU")

    def test_a_new_location_replaces_the_old_one(self, update, user):
        # Arrange
        update.execute(user.id, ProfileChanges(location=KAZAN_INPUT))

        # Act
        result = update.execute(user.id, ProfileChanges(location=LocationInput("Токио", "JP", 35.68, 139.69)))

        # Assert
        assert result.location.city == "Токио" and result.location.timezone is None

    @pytest.mark.parametrize(
        "bad",
        [
            LocationInput("", "RU", 55.0, 49.0),
            LocationInput("Казань", "RUS", 55.0, 49.0),
            LocationInput("Казань", "RU", 95.0, 49.0),
            LocationInput("Казань", "RU", 55.0, 190.0),
        ],
    )
    def test_invalid_locations_are_refused(self, update, user, bad):
        # Arrange
        changes = ProfileChanges(location=bad)

        # Act / Assert
        with pytest.raises(InvalidValue):
            update.execute(user.id, changes)


class TestValidation:
    @pytest.mark.parametrize(
        "changes",
        [
            ProfileChanges(department="kids"),
            ProfileChanges(styles=["nonsense"]),
            ProfileChanges(styles=["street", "nonsense"]),
            ProfileChanges(budget="cheap"),
            ProfileChanges(birth_year=1800),
            ProfileChanges(name="я" * 41),
        ],
    )
    def test_invalid_values_are_refused(self, update, user, changes):
        # Arrange: фикстуры (update, user) и параметры теста (changes)
        # Act / Assert
        with pytest.raises(InvalidValue):
            update.execute(user.id, changes)

    def test_a_refused_update_changes_nothing_at_all(self, update, user, database):
        # Arrange: имя корректное, а стиль — нет
        before = saved(database, user.id)
        changes = ProfileChanges(name="Артём", styles=["nonsense"])

        # Act
        with pytest.raises(InvalidValue):
            update.execute(user.id, changes)

        # Assert
        assert saved(database, user.id) == before

    def test_an_update_for_a_missing_user_is_refused(self, update):
        # Arrange: состояние задают фикстуры (update)
        # Act / Assert
        with pytest.raises(NotFound):
            update.execute("no-such-user", ProfileChanges(name="Артём"))

    def test_other_users_are_not_touched(self, update, user, database):
        # Arrange
        other = make_user(name="Другой")
        persist(database, other)

        # Act
        update.execute(user.id, ProfileChanges(name="Артём", location=KAZAN_INPUT))

        # Assert
        assert saved(database, other.id).name == "Другой" and saved(database, other.id).location is None
