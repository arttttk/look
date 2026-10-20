import pytest

from app.application.errors import NotFound
from app.application.use_cases.feed import GetDailyOutfits, GetFeed, GetOccasionOutfits, GetOutfit
from app.application.wardrobe_view import engine_items
from app.domain.outfits import generate_wardrobe_outfits
from tests.application.helpers import persist
from tests.factories import KAZAN, TOKYO, make_item, make_user


@pytest.fixture()
def get_feed(catalog_store, personalisation) -> GetFeed:
    return GetFeed(catalog_store, personalisation)


class TestGetFeed:
    def test_first_page_has_the_requested_number_of_outfits(self, get_feed):
        # Arrange
        user = make_user()

        # Act
        page = get_feed.execute(user, cursor=0, limit=3)

        # Assert
        assert len(page.items) == 3 and page.next_cursor == 3

    def test_pages_follow_one_another_without_gaps_or_repeats(self, get_feed):
        # Arrange
        user = make_user()

        # Act
        first = get_feed.execute(user, cursor=0, limit=5)
        second = get_feed.execute(user, cursor=first.next_cursor, limit=5)

        # Assert
        assert not {o.id for o in first.items} & {o.id for o in second.items}
        whole = get_feed.execute(user, cursor=0, limit=10)
        assert [o.id for o in whole.items] == [o.id for o in first.items + second.items]

    def test_walking_all_pages_yields_the_whole_feed_once(self, get_feed):
        # Arrange
        user = make_user()
        seen, cursor = [], 0

        # Act
        while cursor is not None:
            page = get_feed.execute(user, cursor=cursor, limit=20)
            seen += [o.id for o in page.items]
            cursor = page.next_cursor

        # Assert
        assert len(seen) == 80 and len(set(seen)) == 80

    def test_the_last_page_has_no_next_cursor(self, get_feed):
        # Arrange
        user = make_user()

        # Act
        page = get_feed.execute(user, cursor=78, limit=5)

        # Assert
        assert len(page.items) == 2 and page.next_cursor is None

    def test_a_cursor_past_the_end_gives_an_empty_page(self, get_feed):
        # Arrange
        user = make_user()

        # Act
        page = get_feed.execute(user, cursor=500, limit=3)

        # Assert
        assert page.items == [] and page.next_cursor is None

    def test_the_feed_follows_the_users_styles(self, get_feed):
        # Arrange
        user = make_user(styles=["sport"])

        # Act
        page = get_feed.execute(user, limit=1)

        # Assert
        assert "sport" in page.items[0].styles

    def test_the_feed_follows_the_users_department(self, get_feed):
        # Arrange
        user = make_user(department="women")

        # Act
        page = get_feed.execute(user, limit=20)

        # Assert
        assert not any(p.product.department == "men" for o in page.items for p in o.pieces)

    def test_the_feed_follows_the_weather(self, get_feed, weather):
        # Arrange
        user = make_user(location=KAZAN)
        weather.temperature_c = 30.0
        hot = get_feed.execute(user, limit=1).items[0]

        # Act
        weather.temperature_c = -15.0
        cold = get_feed.execute(user, limit=1).items[0]

        # Assert
        assert cold.id != hot.id

    def test_a_weather_outage_does_not_break_the_feed(self, get_feed, weather):
        # Arrange
        weather.fail = True
        user = make_user(location=KAZAN)

        # Act
        page = get_feed.execute(user, limit=3)

        # Assert
        assert len(page.items) == 3

    def test_an_undecided_user_from_japan_sees_the_regional_styles_first(self, get_feed):
        # Arrange
        user = make_user(styles=[], location=TOKYO)

        # Act
        page = get_feed.execute(user, limit=6)

        # Assert
        assert all({"minimal", "street"} & set(o.styles) for o in page.items)


class TestDailyAndOccasions:
    def test_the_outfit_of_the_day_is_the_top_four_of_the_feed(
        self, catalog_store, personalisation, get_feed
    ):
        # Arrange
        user = make_user(styles=["street"])

        # Act
        daily = GetDailyOutfits(catalog_store, personalisation).execute(user)

        # Assert
        assert [o.id for o in daily] == [o.id for o in get_feed.execute(user, limit=4).items]

    def test_each_occasion_gets_a_different_outfit(self, catalog_store, personalisation):
        # Arrange
        user = make_user()

        # Act
        pairs = GetOccasionOutfits(catalog_store, personalisation).execute(user)

        # Assert
        assert len(pairs) >= 4 and len({o.id for _, o in pairs}) == len(pairs)
        assert "Работа" in dict(pairs)


class TestGetOutfit:
    @pytest.fixture()
    def get_outfit(self, uow, catalog_store, storage) -> GetOutfit:
        return GetOutfit(uow, catalog_store, storage)

    def test_a_catalog_outfit_is_found_by_id(self, get_outfit):
        # Arrange
        user = make_user()
        outfit_id = "c.tee-white~c.chinos~c.sneakers-white"

        # Act
        outfit = get_outfit.execute(user, outfit_id)

        # Assert
        assert outfit.id == outfit_id and len(outfit.pieces) == 3

    def test_an_outfit_with_the_users_own_item_is_found(self, get_outfit, database):
        # Arrange
        user = make_user()
        item = make_item(user.id, category="top", color="white")
        persist(database, user, item)

        # Act
        outfit = get_outfit.execute(user, f"w.{item.id}~c.chinos~c.sneakers-white")

        # Assert
        own = [p for p in outfit.pieces if p.origin == "wardrobe"]
        assert len(own) == 1 and own[0].image_url == f"/media/{item.image_path}"

    def test_someone_elses_item_cannot_be_used(self, get_outfit, database):
        # Arrange
        owner, stranger = make_user(), make_user()
        item = make_item(owner.id)
        persist(database, owner, stranger, item)

        # Act / Assert
        with pytest.raises(NotFound):
            get_outfit.execute(stranger, f"w.{item.id}~c.chinos~c.sneakers-white")

    @pytest.mark.parametrize("outfit_id", ["", "garbage", "c.no-such-product", "w.no-such-item"])
    def test_unknown_outfits_are_not_found(self, get_outfit, outfit_id):
        # Arrange
        user = make_user()

        # Act / Assert
        with pytest.raises(NotFound):
            get_outfit.execute(user, outfit_id)


def test_generated_wardrobe_outfit_ids_can_be_opened_again(uow, catalog_store, storage, database):
    # Arrange: образ, который приложение получило из /looks, потом открывают по id
    user = make_user()
    items = [
        make_item(user.id, category="top"),
        make_item(user.id, category="bottom", color="gray"),
        make_item(user.id, category="shoes", color="black"),
    ]
    persist(database, user, *items)
    generated = generate_wardrobe_outfits(engine_items(items, storage), catalog_store.current, "any", [])[0]

    # Act
    opened = GetOutfit(uow, catalog_store, storage).execute(user, generated.id)

    # Assert
    assert opened.id == generated.id
