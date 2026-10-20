import pytest

from app.application.catalog_store import CatalogStore
from app.application.errors import NotFound
from app.application.use_cases.catalog import GetProduct, ListProducts, TrackProductClick
from app.application.use_cases.startup import LoadCatalog, SeedCatalog
from app.domain.catalog import Catalog, seed_product_data
from tests.application.helpers import persist
from tests.factories import make_user


class TestListProducts:
    def test_everything_is_listed_by_default(self, catalog_store):
        # Arrange
        use_case = ListProducts(catalog_store)

        # Act
        products = use_case.execute(limit=100)

        # Assert
        assert len(products) == 28

    def test_filters_combine(self, catalog_store):
        # Arrange
        use_case = ListProducts(catalog_store)

        # Act
        products = use_case.execute(department="men", category="shoes", style="classic", limit=100)

        # Assert
        assert products
        assert all(
            p.category == "shoes" and "classic" in p.styles and p.department != "women" for p in products
        )

    def test_pagination_slices_the_list(self, catalog_store):
        # Arrange
        use_case = ListProducts(catalog_store)
        everything = use_case.execute(limit=100)

        # Act
        page = use_case.execute(limit=5, offset=10)

        # Assert
        assert page == everything[10:15]

    def test_a_filter_with_no_matches_gives_an_empty_list(self, catalog_store):
        # Arrange: винтажного низа в мужском разделе нет — юбка миди только женская
        use_case = ListProducts(catalog_store)

        # Act
        products = use_case.execute(department="men", category="bottom", style="vintage")

        # Assert
        assert products == []


class TestGetProduct:
    def test_a_product_is_found_by_id(self, catalog_store):
        # Arrange: состояние задают фикстуры (catalog_store)
        # Act
        product = GetProduct(catalog_store).execute("boots")

        # Assert
        assert product.title == "Ботинки челси"

    def test_an_unknown_product_is_not_found(self, catalog_store):
        # Arrange: состояние задают фикстуры (catalog_store)
        # Act / Assert
        with pytest.raises(NotFound):
            GetProduct(catalog_store).execute("nope")


class TestTrackProductClick:
    @pytest.fixture()
    def track(self, uow, catalog_store, clock) -> TrackProductClick:
        return TrackProductClick(uow, catalog_store, clock)

    def test_the_affiliate_link_is_returned(self, track):
        # Arrange: состояние задают фикстуры (track)
        # Act
        url = track.execute("boots", user_id="u1")

        # Assert
        assert url == "https://example.com/shop/boots?ref=look"

    def test_the_click_is_recorded_with_its_context(self, track, database, clock):
        # Arrange
        user = make_user()
        persist(database, user)

        # Act
        track.execute("boots", user_id=user.id, outfit_id="c.boots~c.tee-white", source="feed")

        # Assert
        (event,) = database.tables.clicks.values()
        assert (event.product_id, event.user_id, event.outfit_id, event.source) == (
            "boots",
            user.id,
            "c.boots~c.tee-white",
            "feed",
        )
        assert event.created_at == clock.now()

    def test_an_anonymous_click_is_recorded_without_a_user(self, track, database):
        # Arrange: состояние задают фикстуры (track, database)
        # Act
        track.execute("boots", source="redirect")

        # Assert
        (event,) = database.tables.clicks.values()
        assert event.user_id is None and event.source == "redirect"

    def test_every_click_is_a_separate_event(self, track, database):
        # Arrange
        track.execute("boots", user_id="u1")
        # Act
        track.execute("boots", user_id="u1")

        # Assert
        assert len(database.tables.clicks) == 2

    def test_an_unknown_product_records_nothing(self, track, database):
        # Arrange: состояние задают фикстуры (track, database)
        # Act
        with pytest.raises(NotFound):
            track.execute("nope", user_id="u1")

        # Assert
        assert database.tables.clicks == {}


class TestStartup:
    def test_an_empty_database_gets_the_starter_catalog(self, uow, database):
        # Arrange: состояние задают фикстуры (uow, database)
        # Act
        seeded = SeedCatalog(uow).execute()

        # Assert
        assert seeded is True and len(database.tables.products) == 28

    def test_seeding_twice_does_not_duplicate_anything(self, uow, database):
        # Arrange
        SeedCatalog(uow).execute()

        # Act
        seeded_again = SeedCatalog(uow).execute()

        # Assert
        assert seeded_again is False and len(database.tables.products) == 28

    def test_a_non_empty_catalog_is_left_alone(self, uow, database):
        # Arrange
        database.tables.products["only"] = seed_product_data()[0]

        # Act
        seeded = SeedCatalog(uow).execute()

        # Assert
        assert seeded is False and set(database.tables.products) == {"only"}

    def test_the_loaded_catalog_matches_what_was_seeded(self, uow):
        # Arrange
        SeedCatalog(uow).execute()

        # Act
        catalog = LoadCatalog(uow).execute()

        # Assert
        assert {p.id for p in catalog.products} == {p.id for p in seed_product_data()}

    def test_the_store_serves_whatever_snapshot_it_was_given(self):
        # Arrange
        store = CatalogStore()
        assert store.current.products == []

        # Act
        store.replace(Catalog(seed_product_data()))

        # Assert
        assert len(store.current.products) == 28
