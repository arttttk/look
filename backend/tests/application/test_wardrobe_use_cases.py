from datetime import timedelta

import pytest

from app.application.errors import NotFound, PayloadTooLarge, UnsupportedMedia
from app.application.policies import WardrobePolicy
from app.application.use_cases.wardrobe import (
    AddWardrobeItem,
    DeleteWardrobeItem,
    GetLooks,
    ListWardrobeItems,
)
from app.domain.errors import InvalidValue
from tests.application.helpers import persist
from tests.factories import KAZAN, make_item, make_user
from tests.fakes import FakeUnitOfWork

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture()
def user(database):
    stored = make_user()
    persist(database, stored)
    return stored


class TestAddWardrobeItem:
    @pytest.fixture()
    def add(self, uow, storage, clock, wardrobe_policy) -> AddWardrobeItem:
        return AddWardrobeItem(uow, storage, clock, wardrobe_policy)

    def test_the_item_is_saved_with_its_photo(self, add, user, database, storage, clock):
        # Arrange: состояние задают фикстуры (add, user, database, storage, clock)
        # Act
        item = add.execute(user.id, "top", "white", "Любимая футболка", PNG)

        # Assert
        assert database.tables.wardrobe[item.id] == item
        assert (item.user_id, item.category, item.color, item.title) == (
            user.id,
            "top",
            "white",
            "Любимая футболка",
        )
        assert item.created_at == clock.now()
        assert storage.files[item.image_path] == PNG

    def test_the_photo_is_stored_under_the_users_folder_with_the_right_extension(self, add, user):
        # Arrange: состояние задают фикстуры (add, user)
        # Act
        item = add.execute(user.id, "top", "white", "", PNG)

        # Assert
        assert item.image_path.startswith(f"{user.id}/") and item.image_path.endswith(".png")

    def test_the_title_is_cleaned_up(self, add, user):
        # Arrange: состояние задают фикстуры (add, user)
        # Act
        item = add.execute(user.id, "top", "white", "  Моя   футболка ", PNG)

        # Assert
        assert item.title == "Моя футболка"

    def test_the_title_is_optional(self, add, user):
        # Arrange: состояние задают фикстуры (add, user)
        # Act
        item = add.execute(user.id, "top", "white", "", PNG)

        # Assert
        assert item.title == ""

    def test_every_item_gets_its_own_id(self, add, user):
        # Arrange
        first = add.execute(user.id, "top", "white", "", PNG)
        # Act
        second = add.execute(user.id, "top", "white", "", PNG)

        # Assert
        assert first.id != second.id

    @pytest.mark.parametrize(
        ("category", "color", "title"),
        [("hat", "white", ""), ("top", "pink", ""), ("top", "white", "я" * 101)],
    )
    def test_invalid_details_are_refused_without_touching_storage(
        self, add, user, database, storage, category, color, title
    ):
        # Arrange: фикстуры (add, user, database, storage) и параметры теста (category, color, title)
        # Act
        with pytest.raises(InvalidValue):
            add.execute(user.id, category, color, title, PNG)

        # Assert
        assert storage.files == {} and database.tables.wardrobe == {}

    def test_a_file_over_the_limit_is_refused(self, add, user, storage):
        # Arrange
        too_big = PNG + b"\x00" * 1024

        # Act / Assert
        with pytest.raises(PayloadTooLarge):
            add.execute(user.id, "top", "white", "", too_big)
        assert storage.files == {}

    def test_a_file_exactly_at_the_limit_is_accepted(self, uow, storage, clock, user):
        # Arrange
        add = AddWardrobeItem(uow, storage, clock, WardrobePolicy(max_upload_bytes=len(PNG)))

        # Act
        item = add.execute(user.id, "top", "white", "", PNG)

        # Assert
        assert item.image_path in storage.files

    @pytest.mark.parametrize("data", [b"not an image at all", b"", b"%PDF-1.7\n" + b"\x00" * 20, b"<?php ?>"])
    def test_anything_but_jpeg_png_webp_is_refused(self, add, user, storage, data):
        # Arrange: фикстуры (add, user, storage) и параметры теста (data)
        # Act
        with pytest.raises(UnsupportedMedia):
            add.execute(user.id, "top", "white", "", data)

        # Assert
        assert storage.files == {}

    def test_if_saving_to_the_database_fails_the_file_is_removed(
        self, database, storage, clock, wardrobe_policy, user
    ):
        # Arrange
        class FailingUnitOfWork(FakeUnitOfWork):
            def commit(self) -> None:
                raise RuntimeError("database is down")

        add = AddWardrobeItem(FailingUnitOfWork(database), storage, clock, wardrobe_policy)

        # Act
        with pytest.raises(RuntimeError):
            add.execute(user.id, "top", "white", "", PNG)

        # Assert
        assert storage.files == {} and database.tables.wardrobe == {}


class TestListWardrobeItems:
    def test_newest_items_come_first(self, uow, database, user, clock):
        # Arrange
        old = make_item(user.id, created_at=clock.now() - timedelta(days=2))
        new = make_item(user.id, created_at=clock.now())
        mid = make_item(user.id, created_at=clock.now() - timedelta(days=1))
        persist(database, old, new, mid)

        # Act
        items = ListWardrobeItems(uow).execute(user.id)

        # Assert
        assert [i.id for i in items] == [new.id, mid.id, old.id]

    def test_a_user_sees_only_their_own_items(self, uow, database, user):
        # Arrange
        other = make_user()
        mine, theirs = make_item(user.id), make_item(other.id)
        persist(database, other, mine, theirs)

        # Act
        items = ListWardrobeItems(uow).execute(user.id)

        # Assert
        assert [i.id for i in items] == [mine.id]

    def test_an_empty_wardrobe_is_an_empty_list(self, uow, user):
        # Arrange: состояние задают фикстуры (uow, user)
        # Act
        items = ListWardrobeItems(uow).execute(user.id)

        # Assert
        assert items == []


class TestDeleteWardrobeItem:
    @pytest.fixture()
    def delete(self, uow, storage) -> DeleteWardrobeItem:
        return DeleteWardrobeItem(uow, storage)

    def test_the_item_and_its_photo_are_removed(self, delete, user, database, storage):
        # Arrange
        path = storage.save(user.id, PNG, ".png")
        item = make_item(user.id, image_path=path)
        persist(database, item)

        # Act
        delete.execute(user.id, item.id)

        # Assert
        assert item.id not in database.tables.wardrobe and path not in storage.files

    def test_other_items_are_kept(self, delete, user, database):
        # Arrange
        doomed, kept = make_item(user.id), make_item(user.id)
        persist(database, doomed, kept)

        # Act
        delete.execute(user.id, doomed.id)

        # Assert
        assert set(database.tables.wardrobe) == {kept.id}

    def test_someone_elses_item_is_reported_as_not_found_and_kept(self, delete, user, database, storage):
        # Arrange
        owner = make_user()
        path = storage.save(owner.id, PNG, ".png")
        item = make_item(owner.id, image_path=path)
        persist(database, owner, item)

        # Act
        with pytest.raises(NotFound):
            delete.execute(user.id, item.id)

        # Assert
        assert item.id in database.tables.wardrobe and path in storage.files

    def test_a_missing_item_is_not_found(self, delete, user):
        # Arrange: состояние задают фикстуры (delete, user)
        # Act / Assert
        with pytest.raises(NotFound):
            delete.execute(user.id, "no-such-item")


class TestGetLooks:
    @pytest.fixture()
    def get_looks(self, uow, catalog_store, personalisation, storage) -> GetLooks:
        return GetLooks(uow, catalog_store, personalisation, storage)

    def test_an_empty_wardrobe_gives_no_looks_and_no_hints(self, get_looks, user):
        # Arrange: состояние задают фикстуры (get_looks, user)
        # Act
        looks = get_looks.execute(user)

        # Assert
        assert looks.outfits == [] and looks.missing == []

    def test_looks_are_built_from_the_users_items(self, get_looks, user, database):
        # Arrange
        items = [
            make_item(user.id, category="top", color="white"),
            make_item(user.id, category="bottom", color="gray"),
            make_item(user.id, category="shoes", color="black"),
        ]
        persist(database, *items)

        # Act
        looks = get_looks.execute(user)

        # Assert
        used = {p.id for o in looks.outfits for p in o.pieces if p.origin == "wardrobe"}
        assert used == {f"w.{i.id}" for i in items}
        assert looks.missing == []

    def test_missing_categories_come_with_suggestions_from_the_catalog(self, get_looks, user, database):
        # Arrange: только верх
        persist(database, make_item(user.id, category="top"))

        # Act
        looks = get_looks.execute(user)

        # Assert
        assert [m.category for m in looks.missing] == ["bottom", "shoes"]
        for missing in looks.missing:
            assert missing.products and all(p.category == missing.category for p in missing.products)

    def test_suggestions_follow_the_users_department(self, get_looks, database):
        # Arrange
        man = make_user(department="men")
        persist(database, man, make_item(man.id, category="top"))

        # Act
        looks = get_looks.execute(man)

        # Assert
        assert all(p.department != "women" for m in looks.missing for p in m.products)

    def test_item_photos_get_a_site_relative_url(self, get_looks, user, database):
        # Arrange
        item = make_item(user.id, category="top")
        persist(database, item)

        # Act
        looks = get_looks.execute(user)

        # Assert
        own = next(p for o in looks.outfits for p in o.pieces if p.origin == "wardrobe")
        assert own.image_url == f"/media/{item.image_path}"

    @pytest.mark.parametrize(("limit", "expected"), [(1, 1), (3, 3), (0, 1), (-5, 1)])
    def test_limit_is_respected_and_at_least_one_look_is_returned(
        self, get_looks, user, database, limit, expected
    ):
        # Arrange
        persist(database, *[make_item(user.id, category="top") for _ in range(5)])

        # Act
        looks = get_looks.execute(user, limit=limit)

        # Assert
        assert len(looks.outfits) == expected

    def test_limit_is_capped_at_thirty(self, get_looks, user, database):
        # Arrange
        items = [
            make_item(user.id, category=c) for c in ("top", "bottom", "shoes", "outerwear") for _ in range(5)
        ]
        persist(database, *items)

        # Act
        looks = get_looks.execute(user, limit=1000)

        # Assert
        assert len(looks.outfits) <= 30

    def test_looks_follow_the_weather(self, get_looks, weather, database):
        # Arrange
        person = make_user(location=KAZAN)
        persist(
            database,
            person,
            make_item(person.id, category="top"),
            make_item(person.id, category="bottom", color="gray"),
            make_item(person.id, category="shoes", color="black"),
            make_item(person.id, category="outerwear", color="beige"),
        )
        weather.temperature_c = -8.0
        cold = get_looks.execute(person).outfits[0]
        weather.temperature_c = 30.0

        # Act
        hot = get_looks.execute(person).outfits[0]

        # Assert
        assert any(p.category == "outerwear" for p in cold.pieces)
        assert all(p.category != "outerwear" for p in hot.pieces)

    def test_other_users_items_are_never_used(self, get_looks, user, database):
        # Arrange
        stranger = make_user()
        persist(database, stranger, make_item(stranger.id, category="top", color="red"))

        # Act
        looks = get_looks.execute(user)

        # Assert
        assert looks.outfits == []
