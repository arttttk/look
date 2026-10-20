"""Лента образов из каталога: полнота, фильтры, персонализация, кэш."""

import pytest

from app.domain.catalog import NOT_WEATHERPROOF, WARMTH, Catalog, seed_product_data
from app.domain.outfits import generate_feed_outfits, generate_occasion_outfits
from app.domain.taxonomy import COLORS
from app.domain.weather import Conditions
from tests.conftest import CATALOG


def accents(outfit) -> set[str]:
    return {p.color for p in outfit.pieces if not COLORS[p.color].neutral}


def warmth(outfit) -> int:
    return sum(WARMTH.get(p.product.id, 0) for p in outfit.pieces)


def price(outfit) -> int:
    return sum(p.product.price for p in outfit.pieces)


class TestCompleteness:
    def test_catalog_is_seeded_completely(self):
        # Arrange: подготовка не требуется
        # Act
        products = seed_product_data()

        # Assert
        assert len(products) == 28
        assert all(p.url.startswith("https://") for p in products)
        assert {p.category for p in products} == {"outerwear", "top", "bottom", "shoes"}

    def test_feed_has_eighty_distinct_outfits(self):
        # Arrange: подготовка не требуется
        # Act
        outfits = generate_feed_outfits(CATALOG, "any", [])

        # Assert
        assert len(outfits) == 80
        assert len({o.id for o in outfits}) == 80

    def test_every_outfit_is_complete_and_comes_from_the_catalog(self):
        # Arrange: подготовка не требуется
        # Act
        outfits = generate_feed_outfits(CATALOG, "any", [])

        # Assert
        for outfit in outfits:
            assert {"top", "bottom", "shoes"} <= {p.category for p in outfit.pieces}
            assert all(p.origin == "catalog" and p.product for p in outfit.pieces)

    def test_no_outfit_mixes_two_accent_colours(self):
        # Arrange: подготовка не требуется
        # Act
        outfits = generate_feed_outfits(CATALOG, "any", [])

        # Assert
        assert all(len(accents(o)) <= 1 for o in outfits)


class TestDepartment:
    def test_mens_feed_has_no_womens_items(self):
        # Arrange: подготовка не требуется
        # Act
        outfits = generate_feed_outfits(CATALOG, "men", [])

        # Assert
        assert not any(p.product.department == "women" for o in outfits for p in o.pieces)

    def test_womens_feed_has_no_mens_items(self):
        # Arrange: подготовка не требуется
        # Act
        outfits = generate_feed_outfits(CATALOG, "women", [])

        # Assert
        assert not any(p.product.department == "men" for o in outfits for p in o.pieces)

    def test_unisex_items_are_available_to_everyone(self):
        # Arrange
        men = generate_feed_outfits(CATALOG, "men", [])
        # Act
        women = generate_feed_outfits(CATALOG, "women", [])

        # Assert
        assert any(p.product.department == "unisex" for o in men for p in o.pieces)
        assert any(p.product.department == "unisex" for o in women for p in o.pieces)


class TestPersonalisation:
    def test_users_style_comes_first(self):
        # Arrange: подготовка не требуется
        # Act
        outfits = generate_feed_outfits(CATALOG, "any", ["sport"])

        # Assert
        assert "sport" in outfits[0].styles

    def test_different_styles_give_different_feeds(self):
        # Arrange
        sport = generate_feed_outfits(CATALOG, "any", ["sport"])
        # Act
        vintage = generate_feed_outfits(CATALOG, "any", ["vintage"])

        # Assert
        assert sport[0].id != vintage[0].id

    def test_the_same_inputs_always_give_the_same_feed(self):
        # Arrange
        fresh = Catalog(seed_product_data())

        # Act
        first = generate_feed_outfits(CATALOG, "any", ["street"])
        second = generate_feed_outfits(fresh, "any", ["street"])

        # Assert
        assert [o.id for o in first] == [o.id for o in second]

    def test_one_item_does_not_take_over_the_top_of_the_feed(self):
        # Arrange
        top = generate_feed_outfits(CATALOG, "any", [])[:6]
        # Act
        uses = [p.id for o in top for p in o.pieces]

        # Assert
        assert max(uses.count(i) for i in set(uses)) <= 2


class TestWeather:
    def test_cold_weather_gives_warmer_outfits_than_hot(self):
        # Arrange
        cold, hot = Conditions(9, False), Conditions(2, False)

        # Act
        cold_feed = generate_feed_outfits(CATALOG, "any", [], cold)[:20]
        hot_feed = generate_feed_outfits(CATALOG, "any", [], hot)[:20]

        # Assert
        cold_avg = sum(map(warmth, cold_feed)) / 20
        hot_avg = sum(map(warmth, hot_feed)) / 20
        assert cold_avg >= hot_avg + 3

    def test_weather_changes_the_order_but_not_the_set_of_options(self):
        # Arrange
        cold = generate_feed_outfits(CATALOG, "any", [], Conditions(9, False))
        # Act
        hot = generate_feed_outfits(CATALOG, "any", [], Conditions(2, False))

        # Assert
        assert cold[0].id != hot[0].id
        assert len(cold) == len(hot) == 80

    def test_in_rain_the_first_outfits_wear_waterproof_shoes(self):
        # Arrange: в каталоге три непромокаемые пары, по два образа на пару
        rain = Conditions(target_warmth=5, rainy=True)

        # Act
        top = generate_feed_outfits(CATALOG, "any", [], rain)[:6]

        # Assert
        shoes = {p.product.id for o in top for p in o.pieces if p.category == "shoes"}
        assert not shoes & NOT_WEATHERPROOF

    def test_without_rain_fragile_shoes_are_not_avoided(self):
        # Arrange
        dry = Conditions(target_warmth=5, rainy=False)

        # Act
        top = generate_feed_outfits(CATALOG, "any", [], dry)[:6]

        # Assert
        shoes = {p.product.id for o in top for p in o.pieces if p.category == "shoes"}
        assert shoes & NOT_WEATHERPROOF


class TestBudget:
    def test_middle_budget_removes_everything_above_the_ceiling(self):
        # Arrange: подготовка не требуется
        # Act
        outfits = generate_feed_outfits(CATALOG, "any", [], None, "mid")

        # Assert
        assert max(map(price, outfits)) <= 30000

    def test_unlimited_budget_removes_nothing(self):
        # Arrange: подготовка не требуется
        # Act
        outfits = generate_feed_outfits(CATALOG, "any", [], None, "high")

        # Assert
        assert max(map(price, outfits)) > 30000

    def test_economy_budget_in_a_small_catalog_puts_affordable_outfits_first(self):
        # Arrange: до 15 000 ₽ в мини-каталоге всего 4 образа из 2430 — фильтр не включается, работает штраф

        # Act
        outfits = generate_feed_outfits(CATALOG, "any", [], None, "low")

        # Assert
        assert price(outfits[0]) <= 15000 and price(outfits[1]) <= 15000
        average = sum(map(price, outfits)) / len(outfits)
        assert average < sum(map(price, generate_feed_outfits(CATALOG, "any", [], None, "high"))) / 80

    def test_prices_rise_with_the_budget(self):
        # Arrange: подготовка не требуется
        # Act
        averages = [
            sum(map(price, generate_feed_outfits(CATALOG, "any", [], None, b)[:20])) / 20
            for b in ("low", "mid", "high")
        ]

        # Assert
        assert averages == sorted(averages) and len(set(averages)) == 3


class TestCache:
    def test_the_same_context_returns_the_cached_list(self):
        # Arrange
        fresh = Catalog(seed_product_data())
        args = (fresh, "any", ["sport"], Conditions(5, False), "mid")

        # Act
        first = generate_feed_outfits(*args)
        second = generate_feed_outfits(*args)

        # Assert
        assert second is first

    @pytest.mark.parametrize(
        "other",
        [
            ("men", ["sport"], Conditions(5, False), "mid"),
            ("any", ["street"], Conditions(5, False), "mid"),
            ("any", ["sport"], Conditions(5, True), "mid"),
            ("any", ["sport"], Conditions(6, False), "mid"),
            ("any", ["sport"], Conditions(5, False), "low"),
            ("any", ["sport"], None, "mid"),
        ],
    )
    def test_any_change_of_context_gives_a_separate_list(self, other):
        # Arrange
        fresh = Catalog(seed_product_data())
        base = generate_feed_outfits(fresh, "any", ["sport"], Conditions(5, False), "mid")

        # Act
        changed = generate_feed_outfits(fresh, *other)

        # Assert
        assert changed is not base

    def test_style_order_does_not_matter_for_the_cache(self):
        # Arrange
        fresh = Catalog(seed_product_data())

        # Act
        first = generate_feed_outfits(fresh, "any", ["sport", "street"])
        second = generate_feed_outfits(fresh, "any", ["street", "sport"])

        # Assert
        assert second is first

    def test_cache_does_not_leak_between_catalogs(self):
        # Arrange
        first_catalog, second_catalog = Catalog(seed_product_data()), Catalog(seed_product_data())

        # Act
        generate_feed_outfits(first_catalog, "any", [])

        # Assert
        assert second_catalog.feed_cache == {}


class TestOccasions:
    def test_each_occasion_gets_its_own_outfit(self):
        # Arrange: подготовка не требуется
        # Act
        pairs = generate_occasion_outfits(CATALOG, "any", [])

        # Assert
        assert len(pairs) >= 4
        assert len({outfit.id for _, outfit in pairs}) == len(pairs)

    def test_outfit_matches_the_style_of_its_occasion(self):
        # Arrange
        expectations = {"Работа": {"classic", "minimal"}, "Спорт": {"sport"}}

        # Act
        pairs = dict(generate_occasion_outfits(CATALOG, "any", []))

        # Assert
        for tag, styles in expectations.items():
            assert set(pairs[tag].styles) & styles

    def test_occasions_follow_the_department(self):
        # Arrange: подготовка не требуется
        # Act
        pairs = generate_occasion_outfits(CATALOG, "men", [])

        # Assert
        assert not any(p.product.department == "women" for _, o in pairs for p in o.pieces)


class TestCacheLimit:
    def test_the_cache_is_emptied_when_it_reaches_its_limit(self, monkeypatch):
        # Arrange
        monkeypatch.setattr("app.domain.outfits.FEED_CACHE_LIMIT", 2)
        fresh = Catalog(seed_product_data())
        generate_feed_outfits(fresh, "any", ["sport"])
        generate_feed_outfits(fresh, "any", ["street"])
        assert len(fresh.feed_cache) == 2

        # Act
        generate_feed_outfits(fresh, "any", ["vintage"])

        # Assert
        assert len(fresh.feed_cache) == 1

    def test_a_dropped_entry_is_simply_recomputed(self, monkeypatch):
        # Arrange
        monkeypatch.setattr("app.domain.outfits.FEED_CACHE_LIMIT", 1)
        fresh = Catalog(seed_product_data())
        first = generate_feed_outfits(fresh, "any", ["sport"])
        generate_feed_outfits(fresh, "any", ["street"])  # вытесняет первый

        # Act
        again = generate_feed_outfits(fresh, "any", ["sport"])

        # Assert
        assert again is not first and [o.id for o in again] == [o.id for o in first]


class TestOccasionsWithAThinCatalog:
    def test_an_occasion_without_a_suitable_outfit_is_left_out(self):
        # Arrange: каталог без единой спортивной вещи
        no_sport = Catalog([p for p in seed_product_data() if "sport" not in p.styles])

        # Act
        tags = [tag for tag, _ in generate_occasion_outfits(no_sport, "any", [])]

        # Assert
        assert "Спорт" not in tags and "Работа" in tags
