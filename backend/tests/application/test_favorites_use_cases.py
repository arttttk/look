import pytest

from app.application.errors import NotFound
from app.application.use_cases.favorites import (
    AddFavorite,
    ListFavoriteIds,
    ListFavoriteOutfits,
    RemoveFavorite,
)
from tests.application.helpers import persist
from tests.factories import make_item, make_user

OUTFIT = "c.tee-white~c.chinos~c.sneakers-white"
OTHER_OUTFIT = "c.hoodie~c.jeans-black~c.chunky"


@pytest.fixture()
def user(database):
    stored = make_user()
    persist(database, stored)
    return stored


@pytest.fixture()
def add(uow, catalog_store, storage, clock) -> AddFavorite:
    return AddFavorite(uow, catalog_store, storage, clock)


class TestAddFavorite:
    def test_the_outfit_lands_in_favorites(self, add, user, uow):
        # Arrange: состояние задают фикстуры (add, user, uow)
        # Act
        add.execute(user, OUTFIT)

        # Assert
        assert ListFavoriteIds(uow).execute(user.id) == [OUTFIT]

    def test_adding_twice_keeps_a_single_entry(self, add, user, uow):
        # Arrange
        add.execute(user, OUTFIT)

        # Act
        add.execute(user, OUTFIT)

        # Assert
        assert ListFavoriteIds(uow).execute(user.id) == [OUTFIT]

    def test_the_time_of_adding_is_recorded(self, add, user, database, clock):
        # Arrange: состояние задают фикстуры (add, user, database, clock)
        # Act
        add.execute(user, OUTFIT)

        # Assert
        assert database.tables.favorites[(user.id, OUTFIT)].created_at == clock.now()

    @pytest.mark.parametrize("outfit_id", ["", "garbage", "c.no-such-product~c.chinos", "w.no-such-item"])
    def test_an_outfit_that_does_not_exist_cannot_be_added(self, add, user, database, outfit_id):
        # Arrange: фикстуры (add, user, database) и параметры теста (outfit_id)
        # Act
        with pytest.raises(NotFound):
            add.execute(user, outfit_id)

        # Assert
        assert database.tables.favorites == {}

    def test_an_outfit_with_the_users_own_item_can_be_added(self, add, user, database):
        # Arrange
        item = make_item(user.id, category="top")
        persist(database, item)
        outfit_id = f"w.{item.id}~c.chinos~c.sneakers-white"

        # Act
        add.execute(user, outfit_id)

        # Assert
        assert (user.id, outfit_id) in database.tables.favorites

    def test_someone_elses_item_cannot_be_favourited(self, add, user, database):
        # Arrange
        owner = make_user()
        item = make_item(owner.id)
        persist(database, owner, item)

        # Act / Assert
        with pytest.raises(NotFound):
            add.execute(user, f"w.{item.id}~c.chinos~c.sneakers-white")


class TestListFavorites:
    def test_the_last_added_comes_first(self, add, user, uow, clock):
        # Arrange
        add.execute(user, OUTFIT)
        clock.advance(minutes=1)
        add.execute(user, OTHER_OUTFIT)

        # Act
        ids = ListFavoriteIds(uow).execute(user.id)

        # Assert
        assert ids == [OTHER_OUTFIT, OUTFIT]

    def test_every_user_has_their_own_favorites(self, add, user, uow, database):
        # Arrange
        other = make_user()
        persist(database, other)
        add.execute(user, OUTFIT)
        add.execute(other, OTHER_OUTFIT)

        # Act
        mine, theirs = ListFavoriteIds(uow).execute(user.id), ListFavoriteIds(uow).execute(other.id)

        # Assert
        assert (mine, theirs) == ([OUTFIT], [OTHER_OUTFIT])

    def test_favourite_outfits_are_returned_in_full(self, add, user, uow, catalog_store, storage):
        # Arrange
        add.execute(user, OUTFIT)

        # Act
        outfits = ListFavoriteOutfits(uow, catalog_store, storage).execute(user)

        # Assert
        assert [o.id for o in outfits] == [OUTFIT] and len(outfits[0].pieces) == 3

    def test_an_outfit_whose_item_was_deleted_is_skipped_quietly(
        self, add, user, uow, catalog_store, storage, database
    ):
        # Arrange
        item = make_item(user.id, category="top")
        persist(database, item)
        gone = f"w.{item.id}~c.chinos~c.sneakers-white"
        add.execute(user, gone)
        add.execute(user, OUTFIT)
        del database.tables.wardrobe[item.id]

        # Act
        outfits = ListFavoriteOutfits(uow, catalog_store, storage).execute(user)

        # Assert
        assert [o.id for o in outfits] == [OUTFIT]

    def test_the_id_of_a_deleted_outfit_stays_in_the_list_of_ids(self, add, user, uow, database):
        # Arrange: id-список — «сырое» избранное, чистит его только явное удаление
        item = make_item(user.id, category="top")
        persist(database, item)
        gone = f"w.{item.id}~c.chinos~c.sneakers-white"
        add.execute(user, gone)
        del database.tables.wardrobe[item.id]

        # Act
        ids = ListFavoriteIds(uow).execute(user.id)

        # Assert
        assert ids == [gone]

    def test_no_favorites_is_an_empty_list(self, user, uow):
        # Arrange: состояние задают фикстуры (user, uow)
        # Act
        ids = ListFavoriteIds(uow).execute(user.id)

        # Assert
        assert ids == []


class TestRemoveFavorite:
    def test_the_outfit_leaves_favorites(self, add, user, uow):
        # Arrange
        add.execute(user, OUTFIT)

        # Act
        RemoveFavorite(uow).execute(user.id, OUTFIT)

        # Assert
        assert ListFavoriteIds(uow).execute(user.id) == []

    def test_other_favorites_stay(self, add, user, uow):
        # Arrange
        add.execute(user, OUTFIT)
        add.execute(user, OTHER_OUTFIT)

        # Act
        RemoveFavorite(uow).execute(user.id, OUTFIT)

        # Assert
        assert ListFavoriteIds(uow).execute(user.id) == [OTHER_OUTFIT]

    def test_removing_something_that_is_not_there_is_harmless(self, user, uow):
        # Arrange: состояние задают фикстуры (user, uow)
        # Act
        RemoveFavorite(uow).execute(user.id, OUTFIT)

        # Assert
        assert ListFavoriteIds(uow).execute(user.id) == []

    def test_one_users_removal_does_not_touch_another_users_favorite(self, add, user, uow, database):
        # Arrange
        other = make_user()
        persist(database, other)
        add.execute(other, OUTFIT)

        # Act
        RemoveFavorite(uow).execute(user.id, OUTFIT)

        # Assert
        assert ListFavoriteIds(uow).execute(other.id) == [OUTFIT]


def test_re_adding_an_existing_favorite_does_not_move_it_to_the_top(add, user, uow, clock):
    # Arrange: второй образ добавлен позже по часам
    add.execute(user, OUTFIT)
    clock.advance(seconds=1)
    add.execute(user, OTHER_OUTFIT)
    clock.advance(seconds=1)

    # Act
    add.execute(user, OUTFIT)  # повторное добавление порядок не меняет

    # Assert
    assert ListFavoriteIds(uow).execute(user.id) == [OTHER_OUTFIT, OUTFIT]
