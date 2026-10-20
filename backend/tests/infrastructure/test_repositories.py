"""Контрактные тесты репозиториев: один набор проверок гоняется и по подделке в памяти (на ней
стоят тесты use case'ов), и по настоящему SQLAlchemy на SQLite. Если подделка отличается от
настоящей реализации, здесь упадёт один из двух прогонов."""

from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.domain.catalog import Product, seed_product_data
from app.domain.entities import AuthSession, ClickEvent, Favorite, Location, OtpCode
from app.infrastructure.db.base import Base, make_engine, make_session_factory
from app.infrastructure.db.uow import SqlAlchemyUnitOfWork
from tests.factories import KAZAN, NOW, make_item, make_user
from tests.fakes import FakeUnitOfWork, InMemoryDatabase

DUPLICATE_ERRORS = (ValueError, IntegrityError)  # подделка и SQL сообщают о дубле по-разному


@pytest.fixture(params=["memory", "sql"])
def make_uow(request):
    """Фабрика транзакций над одним хранилищем. Каждый вызов — новая транзакция."""
    if request.param == "memory":
        database = InMemoryDatabase()
        yield lambda: FakeUnitOfWork(database)
        return

    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = make_session_factory(engine)
    yield lambda: SqlAlchemyUnitOfWork(session_factory)
    engine.dispose()


def save(make_uow, *, users=(), items=(), sessions=(), otps=(), favorites=(), clicks=(), products=()):
    """Кладёт данные отдельной завершённой транзакцией."""
    with make_uow() as uow:
        for user in users:
            uow.users.add(user)
        for item in items:
            uow.wardrobe.add(item)
        for session in sessions:
            uow.sessions.add(session)
        for otp in otps:
            uow.otp_codes.add(otp)
        for favorite in favorites:
            uow.favorites.add(favorite)
        for click in clicks:
            uow.clicks.add(click)
        if products:
            uow.products.add_many(products)
        uow.commit()


class TestUnitOfWork:
    def test_changes_are_visible_inside_the_transaction_before_commit(self, make_uow):
        # Arrange
        user = make_user()

        # Act
        with make_uow() as uow:
            uow.users.add(user)
            inside = uow.users.get(user.id)

        # Assert
        assert inside == user

    def test_an_uncommitted_transaction_is_rolled_back(self, make_uow):
        # Arrange
        user = make_user()
        with make_uow() as uow:
            uow.users.add(user)

        # Act
        with make_uow() as uow:
            found = uow.users.get(user.id)

        # Assert
        assert found is None

    def test_a_committed_transaction_is_visible_to_the_next_one(self, make_uow):
        # Arrange
        user = make_user()
        save(make_uow, users=[user])

        # Act
        with make_uow() as uow:
            found = uow.users.get(user.id)

        # Assert
        assert found == user

    def test_an_exception_rolls_everything_back(self, make_uow):
        # Arrange
        user = make_user()

        # Act
        with pytest.raises(RuntimeError):
            with make_uow() as uow:
                uow.users.add(user)
                raise RuntimeError("boom")

        # Assert
        with make_uow() as uow:
            assert uow.users.get(user.id) is None

    def test_only_what_was_committed_survives_later_uncommitted_changes(self, make_uow):
        # Arrange
        first, second = make_user(), make_user()

        # Act
        with make_uow() as uow:
            uow.users.add(first)
            uow.commit()
            uow.users.add(second)  # без commit

        # Assert
        with make_uow() as uow:
            assert uow.users.get(first.id) is not None and uow.users.get(second.id) is None

    def test_one_object_can_run_several_transactions_in_a_row(self, make_uow):
        # Arrange
        uow = make_uow()
        user = make_user()

        # Act
        with uow:
            uow.users.add(user)
            uow.commit()
        with uow:
            found = uow.users.get(user.id)

        # Assert
        assert found == user


class TestUsers:
    def test_a_user_round_trips_with_every_field(self, make_uow):
        # Arrange
        user = make_user(
            email="a@example.com", name="Артём", birth_year=1998, onboarded=True, department="men",
            styles=["street", "minimal"], budget="mid", location=KAZAN,
        )  # fmt: skip
        save(make_uow, users=[user])

        # Act
        with make_uow() as uow:
            found = uow.users.get(user.id)

        # Assert
        assert found == user

    def test_a_missing_user_is_none(self, make_uow):
        # Arrange: состояние задают фикстуры (make_uow)
        # Act
        with make_uow() as uow:
            found = uow.users.get("nobody")

        # Assert
        assert found is None

    def test_a_user_is_found_by_phone_and_by_email(self, make_uow):
        # Arrange
        by_phone = make_user(phone="+79991112233")
        by_email = make_user(phone=None, email="a@example.com")
        save(make_uow, users=[by_phone, by_email])

        # Act
        with make_uow() as uow:
            found_phone = uow.users.get_by_phone("+79991112233")
            found_email = uow.users.get_by_email("a@example.com")

        # Assert
        assert found_phone.id == by_phone.id and found_email.id == by_email.id

    def test_unknown_phone_and_email_give_none(self, make_uow):
        # Arrange
        save(make_uow, users=[make_user()])

        # Act
        with make_uow() as uow:
            by_phone = uow.users.get_by_phone("+70000000000")
            by_email = uow.users.get_by_email("none@example.com")

        # Assert
        assert by_phone is None and by_email is None

    def test_save_updates_fields_and_can_clear_the_location(self, make_uow):
        # Arrange
        user = make_user(location=KAZAN, name="Артём")
        save(make_uow, users=[user])

        # Act
        with make_uow() as uow:
            loaded = uow.users.get(user.id)
            loaded.name, loaded.location, loaded.styles = None, None, ["sport"]
            uow.users.save(loaded)
            uow.commit()

        # Assert
        with make_uow() as uow:
            found = uow.users.get(user.id)
        assert (found.name, found.location, found.styles) == (None, None, ["sport"])

    def test_saving_a_user_that_does_not_exist_is_an_error(self, make_uow):
        # Arrange
        ghost = make_user()

        # Act / Assert
        with make_uow() as uow:
            with pytest.raises(LookupError):
                uow.users.save(ghost)

    def test_changing_a_loaded_user_without_save_changes_nothing(self, make_uow):
        # Arrange
        user = make_user(name="Артём")
        save(make_uow, users=[user])

        # Act
        with make_uow() as uow:
            loaded = uow.users.get(user.id)
            loaded.name = "Изменён в памяти"
            uow.commit()

        # Assert
        with make_uow() as uow:
            assert uow.users.get(user.id).name == "Артём"

    def test_two_users_cannot_share_a_phone(self, make_uow):
        # Arrange
        save(make_uow, users=[make_user(phone="+79991112233")])

        # Act / Assert
        with make_uow() as uow:
            with pytest.raises(DUPLICATE_ERRORS):
                uow.users.add(make_user(phone="+79991112233"))

    def test_the_location_survives_without_timezone(self, make_uow):
        # Arrange
        user = make_user(location=Location("Токио", "JP", 35.68, 139.69))
        save(make_uow, users=[user])

        # Act
        with make_uow() as uow:
            found = uow.users.get(user.id)

        # Assert
        assert found.location.timezone is None


class TestSessions:
    def make(self, **kw) -> AuthSession:
        values = {
            "token_hash": "h" * 64, "user_id": "u1", "created_at": NOW,
            "expires_at": NOW + timedelta(days=90), "last_used_at": NOW,
        } | kw  # fmt: skip
        return AuthSession(**values)

    def test_a_session_round_trips(self, make_uow):
        # Arrange
        session = self.make()
        save(make_uow, sessions=[session])

        # Act
        with make_uow() as uow:
            found = uow.sessions.get(session.token_hash)

        # Assert
        assert found == session

    def test_an_unknown_token_hash_gives_none(self, make_uow):
        # Arrange: состояние задают фикстуры (make_uow)
        # Act
        with make_uow() as uow:
            found = uow.sessions.get("nope")

        # Assert
        assert found is None

    def test_save_updates_the_last_use(self, make_uow):
        # Arrange
        session = self.make()
        save(make_uow, sessions=[session])

        # Act
        with make_uow() as uow:
            loaded = uow.sessions.get(session.token_hash)
            loaded.last_used_at = NOW + timedelta(hours=3)
            uow.sessions.save(loaded)
            uow.commit()

        # Assert
        with make_uow() as uow:
            assert uow.sessions.get(session.token_hash).last_used_at == NOW + timedelta(hours=3)

    def test_saving_a_session_that_does_not_exist_is_an_error(self, make_uow):
        # Arrange
        ghost = self.make(token_hash="g" * 64)

        # Act / Assert
        with make_uow() as uow:
            with pytest.raises(LookupError):
                uow.sessions.save(ghost)

    def test_delete_removes_only_that_session(self, make_uow):
        # Arrange
        keep, drop = self.make(token_hash="k" * 64), self.make(token_hash="d" * 64)
        save(make_uow, sessions=[keep, drop])

        # Act
        with make_uow() as uow:
            uow.sessions.delete(drop.token_hash)
            uow.commit()

        # Assert
        with make_uow() as uow:
            assert uow.sessions.get(drop.token_hash) is None and uow.sessions.get(keep.token_hash) is not None

    def test_deleting_a_missing_session_is_harmless(self, make_uow):
        # Arrange: состояние задают фикстуры (make_uow)
        # Act
        with make_uow() as uow:
            uow.sessions.delete("nope")
            uow.commit()

        # Assert
        with make_uow() as uow:
            assert uow.sessions.get("nope") is None


class TestOtpCodes:
    def make(self, identifier="+79991234567", created=NOW, **kw) -> OtpCode:
        return OtpCode(
            identifier=identifier, kind="phone", code_hash="c" * 64,
            created_at=created, expires_at=created + timedelta(minutes=5), **kw,
        )  # fmt: skip

    def test_add_assigns_an_id(self, make_uow):
        # Arrange
        code = self.make()

        # Act
        with make_uow() as uow:
            uow.otp_codes.add(code)

        # Assert
        assert code.id is not None

    def test_recent_returns_newest_first_and_only_for_that_identifier(self, make_uow):
        # Arrange
        old = self.make(created=NOW - timedelta(minutes=30))
        new = self.make(created=NOW - timedelta(minutes=1))
        other = self.make(identifier="+79990000000", created=NOW)
        save(make_uow, otps=[old, new, other])

        # Act
        with make_uow() as uow:
            codes = uow.otp_codes.recent("+79991234567", since=NOW - timedelta(hours=1))

        # Assert
        assert [c.created_at for c in codes] == [new.created_at, old.created_at]

    def test_recent_excludes_codes_older_than_the_window(self, make_uow):
        # Arrange
        stale = self.make(created=NOW - timedelta(hours=2))
        fresh = self.make(created=NOW - timedelta(minutes=10))
        save(make_uow, otps=[stale, fresh])

        # Act
        with make_uow() as uow:
            codes = uow.otp_codes.recent("+79991234567", since=NOW - timedelta(hours=1))

        # Assert
        assert [c.id for c in codes] == [fresh.id]

    def test_recent_window_start_is_exclusive(self, make_uow):
        # Arrange
        boundary = self.make(created=NOW - timedelta(hours=1))
        save(make_uow, otps=[boundary])

        # Act
        with make_uow() as uow:
            codes = uow.otp_codes.recent("+79991234567", since=NOW - timedelta(hours=1))

        # Assert
        assert codes == []

    def test_latest_active_is_the_newest_unused_code(self, make_uow):
        # Arrange
        older = self.make(created=NOW - timedelta(minutes=3))
        newer = self.make(created=NOW - timedelta(minutes=1))
        save(make_uow, otps=[older, newer])

        # Act
        with make_uow() as uow:
            found = uow.otp_codes.latest_active("+79991234567")

        # Assert
        assert found.id == newer.id

    def test_latest_active_skips_consumed_codes(self, make_uow):
        # Arrange
        used = self.make(created=NOW, consumed=True)
        earlier = self.make(created=NOW - timedelta(minutes=2))
        save(make_uow, otps=[used, earlier])

        # Act
        with make_uow() as uow:
            found = uow.otp_codes.latest_active("+79991234567")

        # Assert
        assert found.id == earlier.id

    def test_latest_active_is_none_when_everything_is_consumed(self, make_uow):
        # Arrange
        save(make_uow, otps=[self.make(consumed=True)])

        # Act
        with make_uow() as uow:
            found = uow.otp_codes.latest_active("+79991234567")

        # Assert
        assert found is None

    def test_save_persists_attempts_and_consumption(self, make_uow):
        # Arrange
        code = self.make()
        save(make_uow, otps=[code])

        # Act
        with make_uow() as uow:
            loaded = uow.otp_codes.latest_active("+79991234567")
            loaded.attempts, loaded.consumed = 3, True
            uow.otp_codes.save(loaded)
            uow.commit()

        # Assert
        with make_uow() as uow:
            recent = uow.otp_codes.recent("+79991234567", since=NOW - timedelta(days=1))
        assert (recent[0].attempts, recent[0].consumed) == (3, True)

    def test_saving_an_unknown_code_is_an_error(self, make_uow):
        # Arrange
        ghost = self.make()
        ghost.id = 999

        # Act / Assert
        with make_uow() as uow:
            with pytest.raises(LookupError):
                uow.otp_codes.save(ghost)


class TestProducts:
    def test_an_empty_catalog_has_no_products(self, make_uow):
        # Arrange: состояние задают фикстуры (make_uow)
        # Act
        with make_uow() as uow:
            count = uow.products.count()

        # Assert
        assert count == 0

    def test_products_round_trip_with_every_attribute(self, make_uow):
        # Arrange
        product = Product(
            id="p1", title="Куртка", brand="B", price=1990, category="outerwear", color="black",
            styles=("minimal", "street"), department="unisex", url="https://example.com/p1",
            image_url="https://img/p1.jpg", warmth=2, weatherproof=False,
        )  # fmt: skip
        save(make_uow, products=[product])

        # Act
        with make_uow() as uow:
            loaded = uow.products.list_all()

        # Assert
        assert loaded == [product]

    def test_count_and_list_cover_the_whole_seed(self, make_uow):
        # Arrange
        save(make_uow, products=seed_product_data())

        # Act
        with make_uow() as uow:
            count, loaded = uow.products.count(), uow.products.list_all()

        # Assert
        assert count == 28
        assert {p.id: p for p in loaded} == {p.id: p for p in seed_product_data()}

    def test_listing_is_ordered_by_id(self, make_uow):
        # Arrange
        save(make_uow, products=seed_product_data())

        # Act
        with make_uow() as uow:
            ids = [p.id for p in uow.products.list_all()]

        # Assert
        assert ids == sorted(ids)


class TestWardrobe:
    def test_an_item_round_trips(self, make_uow):
        # Arrange
        item = make_item("u1", category="outerwear", color="beige", title="Тренч")
        save(make_uow, items=[item])

        # Act
        with make_uow() as uow:
            found = uow.wardrobe.get(item.id)

        # Assert
        assert found == item

    def test_a_missing_item_is_none(self, make_uow):
        # Arrange: состояние задают фикстуры (make_uow)
        # Act
        with make_uow() as uow:
            found = uow.wardrobe.get("nope")

        # Assert
        assert found is None

    def test_the_list_is_per_user_and_newest_first(self, make_uow):
        # Arrange
        old = make_item("u1", created_at=NOW - timedelta(days=1))
        new = make_item("u1", created_at=NOW)
        foreign = make_item("u2")
        save(make_uow, items=[old, new, foreign])

        # Act
        with make_uow() as uow:
            items = uow.wardrobe.list_for_user("u1")

        # Assert
        assert [i.id for i in items] == [new.id, old.id]

    def test_delete_removes_only_that_item(self, make_uow):
        # Arrange
        keep, drop = make_item("u1"), make_item("u1")
        save(make_uow, items=[keep, drop])

        # Act
        with make_uow() as uow:
            uow.wardrobe.delete(drop.id)
            uow.commit()

        # Assert
        with make_uow() as uow:
            assert [i.id for i in uow.wardrobe.list_for_user("u1")] == [keep.id]


class TestFavorites:
    def test_exists_reflects_what_was_added(self, make_uow):
        # Arrange
        save(make_uow, favorites=[Favorite("u1", "outfit-a", NOW)])

        # Act
        with make_uow() as uow:
            present, other_user, other_outfit = (
                uow.favorites.exists("u1", "outfit-a"),
                uow.favorites.exists("u2", "outfit-a"),
                uow.favorites.exists("u1", "outfit-b"),
            )

        # Assert
        assert (present, other_user, other_outfit) == (True, False, False)

    def test_ids_come_newest_first_and_per_user(self, make_uow):
        # Arrange
        save(
            make_uow,
            favorites=[
                Favorite("u1", "old", NOW - timedelta(minutes=5)),
                Favorite("u1", "new", NOW),
                Favorite("u2", "foreign", NOW),
            ],
        )

        # Act
        with make_uow() as uow:
            ids = uow.favorites.ids_for_user("u1")

        # Assert
        assert ids == ["new", "old"]

    def test_remove_drops_one_entry_and_tolerates_missing_ones(self, make_uow):
        # Arrange
        save(make_uow, favorites=[Favorite("u1", "a", NOW), Favorite("u1", "b", NOW)])

        # Act
        with make_uow() as uow:
            uow.favorites.remove("u1", "a")
            uow.favorites.remove("u1", "never-added")
            uow.commit()

        # Assert
        with make_uow() as uow:
            assert uow.favorites.ids_for_user("u1") == ["b"]

    def test_a_long_outfit_id_is_stored_whole(self, make_uow):
        # Arrange
        long_id = "~".join(f"c.product-number-{i}" for i in range(20))
        save(make_uow, favorites=[Favorite("u1", long_id, NOW)])

        # Act
        with make_uow() as uow:
            ids = uow.favorites.ids_for_user("u1")

        # Assert
        assert ids == [long_id]


class TestClicks:
    def test_add_assigns_an_id_and_list_returns_events_in_order(self, make_uow):
        # Arrange
        first = ClickEvent("boots", NOW, user_id="u1", outfit_id="c.boots", source="feed")
        second = ClickEvent("trench", NOW, source="redirect")

        # Act
        with make_uow() as uow:
            uow.clicks.add(first)
            uow.clicks.add(second)
            uow.commit()

        # Assert
        with make_uow() as uow:
            events = uow.clicks.list_all()
        assert first.id is not None and first.id < second.id
        assert events == [first, second]

    def test_an_anonymous_click_keeps_no_user(self, make_uow):
        # Arrange
        click = ClickEvent("boots", NOW, source="redirect")
        save(make_uow, clicks=[click])

        # Act
        with make_uow() as uow:
            (event,) = uow.clicks.list_all()

        # Assert
        assert event.user_id is None and event.outfit_id is None
