"""Образы из гардероба пользователя, нехватка категорий, подсказки, восстановление образа по id."""

import time

import pytest

from app.domain.outfits import (
    ItemData,
    generate_wardrobe_outfits,
    missing_categories,
    piece_from_item,
    pieces_to_buy,
    resolve_outfit,
    suggest_products,
)
from app.domain.taxonomy import COLORS
from app.domain.weather import Conditions
from tests.conftest import CATALOG


def item(item_id: str, category: str, color: str, created_at: float = 1.0, title: str = "") -> ItemData:
    return ItemData(id=item_id, category=category, color=color, title=title, created_at=created_at)


def accents(outfit) -> set[str]:
    return {p.color for p in outfit.pieces if not COLORS[p.color].neutral}


FULL_SET = [
    item("t1", "top", "white"),
    item("b1", "bottom", "gray"),
    item("s1", "shoes", "black"),
]


class TestGeneration:
    def test_empty_wardrobe_gives_nothing(self):
        # Arrange: подготовка не требуется
        # Act
        outfits = generate_wardrobe_outfits([], CATALOG, "any", [])

        # Assert
        assert outfits == []

    def test_a_full_set_needs_no_purchases(self):
        # Arrange: подготовка не требуется
        # Act
        outfits = generate_wardrobe_outfits(FULL_SET, CATALOG, "any", [])

        # Assert
        assert outfits and all(not pieces_to_buy(o) for o in outfits)

    def test_gaps_are_filled_from_the_catalog(self):
        # Arrange: есть только белый верх
        items = [item("t1", "top", "white")]

        # Act
        outfits = generate_wardrobe_outfits(items, CATALOG, "any", ["minimal"])

        # Assert
        assert outfits
        for outfit in outfits:
            assert {p.category for p in pieces_to_buy(outfit)} == {"bottom", "shoes"}
            assert any(p.origin == "wardrobe" for p in outfit.pieces)

    def test_own_items_beat_purchases(self):
        # Arrange: с обувью из гардероба образов с покупкой меньше, чем без неё
        no_shoes = [item("t1", "top", "white"), item("b1", "bottom", "gray")]
        with_shoes = no_shoes + [item("s1", "shoes", "black")]

        # Act
        first = generate_wardrobe_outfits(no_shoes, CATALOG, "any", [])[0]
        second = generate_wardrobe_outfits(with_shoes, CATALOG, "any", [])[0]

        # Assert
        assert len(pieces_to_buy(first)) == 1 and len(pieces_to_buy(second)) == 0

    def test_gap_suggestions_respect_the_department(self):
        # Arrange
        items = [item("t1", "top", "white")]

        # Act
        outfits = generate_wardrobe_outfits(items, CATALOG, "men", [], limit=30)

        # Assert
        assert not any(p.product and p.product.department == "women" for o in outfits for p in o.pieces)

    def test_two_accent_colours_never_end_up_together(self):
        # Arrange: красный верх и зелёный низ
        items = [
            item("t1", "top", "white"),
            item("t2", "top", "red"),
            item("b1", "bottom", "blue"),
            item("b2", "bottom", "green"),
            item("s1", "shoes", "black"),
        ]

        # Act
        outfits = generate_wardrobe_outfits(items, CATALOG, "any", [])

        # Assert
        assert outfits and all(len(accents(o)) <= 1 for o in outfits)

    def test_limit_caps_the_number_of_outfits(self):
        # Arrange
        items = [item(f"t{i}", "top", "white") for i in range(5)] + FULL_SET[1:]

        # Act
        outfits = generate_wardrobe_outfits(items, CATALOG, "any", [], limit=3)

        # Assert
        assert len(outfits) == 3

    def test_accessories_do_not_take_part_in_outfits(self):
        # Arrange
        items = [*FULL_SET, item("a1", "accessory", "red")]

        # Act
        outfits = generate_wardrobe_outfits(items, CATALOG, "any", [])

        # Assert
        assert all(p.category != "accessory" for o in outfits for p in o.pieces)

    def test_only_the_newest_items_of_a_category_are_used(self):
        # Arrange: 15 верхов, а в перебор попадает 12 самых свежих
        tops = [item(f"t{i:02d}", "top", "white", created_at=float(i)) for i in range(15)]
        items = [*tops, *FULL_SET[1:]]

        # Act
        outfits = generate_wardrobe_outfits(items, CATALOG, "any", [], limit=100)

        # Assert
        used = {p.id for o in outfits for p in o.pieces if p.category == "top"}
        assert "w.t14" in used and "w.t00" not in used


class TestWeather:
    def test_in_the_cold_outfits_with_outerwear_come_first(self):
        # Arrange
        items = [*FULL_SET, item("o1", "outerwear", "beige")]
        cold = Conditions(target_warmth=7, rainy=False)

        # Act
        best = generate_wardrobe_outfits(items, CATALOG, "any", [], conditions=cold)[0]

        # Assert
        assert any(p.category == "outerwear" for p in best.pieces)

    def test_in_the_heat_outfits_come_without_outerwear(self):
        # Arrange
        items = [*FULL_SET, item("o1", "outerwear", "beige")]
        hot = Conditions(target_warmth=2, rainy=False)

        # Act
        best = generate_wardrobe_outfits(items, CATALOG, "any", [], conditions=hot)[0]

        # Assert
        assert all(p.category != "outerwear" for p in best.pieces)

    def test_without_weather_outerwear_is_slightly_preferred(self):
        # Arrange
        items = [*FULL_SET, item("o1", "outerwear", "beige")]

        # Act
        best = generate_wardrobe_outfits(items, CATALOG, "any", [])[0]

        # Assert
        assert any(p.category == "outerwear" for p in best.pieces)

    @pytest.mark.parametrize(
        ("category", "warmth"), [("outerwear", 2), ("top", 1), ("bottom", 2), ("shoes", 0)]
    )
    def test_items_without_data_get_a_typical_warmth_for_their_category(self, category, warmth):
        # Arrange
        thing = item("x", category, "black")

        # Act
        piece = piece_from_item(thing)

        # Assert
        assert piece.warmth == warmth


class TestMissingCategories:
    def test_everything_is_missing_in_an_empty_wardrobe(self):
        # Arrange: подготовка не требуется
        # Act
        missing = missing_categories([])

        # Assert
        assert missing == ["top", "bottom", "shoes"]

    def test_only_absent_required_categories_are_reported(self):
        # Arrange
        items = [item("t1", "top", "white"), item("o1", "outerwear", "black")]

        # Act
        missing = missing_categories(items)

        # Assert
        assert missing == ["bottom", "shoes"]

    def test_a_full_set_misses_nothing(self):
        # Arrange: подготовка не требуется
        # Act
        missing = missing_categories(FULL_SET)

        # Assert
        assert missing == []


class TestSuggestProducts:
    def test_products_belong_to_the_category_and_department(self):
        # Arrange: подготовка не требуется
        # Act
        products = suggest_products(CATALOG, "shoes", "men", [])

        # Assert
        assert products and all(p.category == "shoes" and p.department != "women" for p in products)

    def test_users_styles_come_first(self):
        # Arrange: подготовка не требуется
        # Act
        products = suggest_products(CATALOG, "shoes", "men", ["sport"])

        # Assert
        assert "sport" in products[0].styles

    def test_among_equals_cheaper_goes_first(self):
        # Arrange: подготовка не требуется
        # Act
        products = suggest_products(CATALOG, "top", "any", [])

        # Assert
        assert [p.price for p in products] == sorted(p.price for p in products)

    def test_limit_is_respected(self):
        # Arrange: подготовка не требуется
        # Act
        products = suggest_products(CATALOG, "top", "any", [], limit=2)

        # Assert
        assert len(products) == 2


class TestResolveOutfit:
    def test_outfit_is_rebuilt_from_its_id(self):
        # Arrange
        by_id = {i.id: i for i in FULL_SET}
        original = generate_wardrobe_outfits(FULL_SET, CATALOG, "any", [])[0]

        # Act
        resolved = resolve_outfit(original.id, CATALOG, by_id, [])

        # Assert
        assert resolved is not None and resolved.id == original.id
        assert [p.id for p in resolved.pieces] == [p.id for p in original.pieces]

    def test_catalog_only_outfit_needs_no_wardrobe(self):
        # Arrange
        outfit_id = "c.tee-white~c.chinos~c.sneakers-white"

        # Act
        resolved = resolve_outfit(outfit_id, CATALOG, {}, [])

        # Assert
        assert resolved is not None and len(resolved.pieces) == 3

    def test_id_order_does_not_matter(self):
        # Arrange
        shuffled = "c.sneakers-white~c.tee-white~c.chinos"

        # Act
        resolved = resolve_outfit(shuffled, CATALOG, {}, [])

        # Assert
        assert resolved.id == "c.tee-white~c.chinos~c.sneakers-white"

    def test_deleted_wardrobe_item_makes_the_outfit_unresolvable(self):
        # Arrange
        outfit = generate_wardrobe_outfits(FULL_SET, CATALOG, "any", [])[0]

        # Act
        resolved = resolve_outfit(outfit.id, CATALOG, {}, [])

        # Assert
        assert resolved is None

    @pytest.mark.parametrize("outfit_id", ["", "zzz", "c.no-such-product", "x.foo~c.chinos", "w.", "~"])
    def test_garbage_ids_resolve_to_nothing(self, outfit_id):
        # Arrange: входные данные — параметры теста (outfit_id)
        # Act
        resolved = resolve_outfit(outfit_id, CATALOG, {}, [])

        # Assert
        assert resolved is None

    def test_one_unknown_part_spoils_the_whole_outfit(self):
        # Arrange
        outfit_id = "c.tee-white~c.chinos~c.no-such-shoes"

        # Act
        resolved = resolve_outfit(outfit_id, CATALOG, {}, [])

        # Assert
        assert resolved is None


def test_generation_is_fast_enough_for_a_request():
    # Arrange
    items = [item(f"{c}{i}", c, "white") for c in ("top", "bottom", "shoes", "outerwear") for i in range(12)]

    # Act
    started = time.perf_counter()
    outfits = generate_wardrobe_outfits(items, CATALOG, "any", [])
    elapsed = time.perf_counter() - started

    # Assert: 12 x 12 x 12 x 13 вариантов — меньше секунды даже на медленной машине
    assert len(outfits) == 12 and elapsed < 1.0


class TestPieceLabels:
    def test_a_users_own_title_is_kept_without_extra_spaces(self):
        # Arrange
        thing = item("x", "top", "white", title="  Любимая футболка ")

        # Act
        piece = piece_from_item(thing)

        # Assert
        assert piece.title == "Любимая футболка"

    @pytest.mark.parametrize(
        ("category", "label"),
        [("top", "Верх"), ("bottom", "Низ"), ("shoes", "Обувь"), ("outerwear", "Верхняя одежда")],
    )
    def test_without_a_title_the_item_is_named_after_its_category(self, category, label):
        # Arrange
        thing = item("x", category, "white", title="   ")

        # Act
        piece = piece_from_item(thing)

        # Assert
        assert piece.title == label

    def test_an_unknown_category_falls_back_to_its_raw_id(self):
        # Arrange
        thing = item("x", "scarf", "white")

        # Act
        piece = piece_from_item(thing)

        # Assert
        assert piece.title == "scarf"
