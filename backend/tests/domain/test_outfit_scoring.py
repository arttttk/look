"""Оценка образа: цвета, погода, бюджет, стиль и название."""

from dataclasses import replace

import pytest

from app.domain.outfits import (
    budget_score,
    build_outfit,
    catalog_total,
    color_score,
    dominant_styles,
    piece_from_product,
    title_for,
    weather_score,
)
from app.domain.weather import Conditions
from tests.conftest import CATALOG


def piece(product_id: str):
    return piece_from_product(CATALOG.by_id[product_id])


class TestColorScore:
    def test_all_neutral_outfit_scores_a_point(self):
        # Arrange
        pieces = [piece("tee-white"), piece("jeans-straight"), piece("sneakers-white")]

        # Act
        score = color_score(pieces)

        # Assert
        assert score == 1

    def test_one_accent_is_fine(self):
        # Arrange
        pieces = [
            piece("bomber"),
            piece("tee-white"),
            piece("jeans-straight"),
            piece("boots"),
        ]  # зелёный бомбер

        # Act
        score = color_score(pieces)

        # Assert
        assert score == 0  # нейтральной базы нет, но и штрафа нет

    def test_two_different_accents_are_penalised_heavily(self):
        # Arrange: зелёные карго и красная футболка
        red_tee = replace(piece("tee-white"), color="red")
        pieces = [red_tee, piece("cargo"), piece("boots")]

        # Act
        score = color_score(pieces)

        # Assert
        assert score == -3

    @pytest.mark.parametrize(("other", "penalty"), [("navy", 0.5), ("brown", 0.5)])
    def test_black_next_to_navy_or_brown_costs_half_a_point(self, other, penalty):
        # Arrange
        pieces = [replace(piece("tee-white"), color=other), piece("jeans-black"), piece("boots")]

        # Act
        score = color_score(pieces)

        # Assert
        assert score == 1 - penalty


class TestWeatherScore:
    def test_exact_warmth_costs_nothing(self):
        # Arrange: 3 + 3 + 2 = 8
        cold = Conditions(target_warmth=8, rainy=False)
        pieces = [piece("coat-wool"), piece("knit"), piece("jeans-straight"), piece("boots")]

        # Act
        score = weather_score(pieces, cold)

        # Assert
        assert score == 0

    def test_every_unit_of_mismatch_costs_a_point(self):
        # Arrange: в мороз надели 1 + 1 = 2 вместо 8
        cold = Conditions(target_warmth=8, rainy=False)
        pieces = [piece("tee-white"), piece("chinos"), piece("boots")]

        # Act
        score = weather_score(pieces, cold)

        # Assert
        assert score == -6

    def test_being_too_warm_is_penalised_like_being_too_cold(self):
        # Arrange
        hot = Conditions(target_warmth=2, rainy=False)
        heavy = [piece("coat-wool"), piece("knit"), piece("jeans-straight"), piece("boots")]  # 8

        # Act
        score = weather_score(heavy, hot)

        # Assert
        assert score == -6

    def test_shoes_do_not_add_warmth(self):
        # Arrange
        conditions = Conditions(target_warmth=4, rainy=False)
        base = [piece("hoodie"), piece("jeans-straight")]  # 2 + 2

        # Act
        with_boots = weather_score([*base, piece("boots")], conditions)
        with_sneakers = weather_score([*base, piece("sneakers-white")], conditions)

        # Assert
        assert with_boots == with_sneakers == 0

    def test_rain_penalises_shoes_that_fear_water(self):
        # Arrange
        rain = Conditions(target_warmth=4, rainy=True)
        base = [piece("hoodie"), piece("jeans-straight")]

        # Act
        dry_shoes = weather_score([*base, piece("boots")], rain)
        wet_shoes = weather_score([*base, piece("sneakers-white")], rain)

        # Assert
        assert (dry_shoes, wet_shoes) == (0, -1.5)

    def test_waterproof_or_not_does_not_matter_without_rain(self):
        # Arrange
        dry = Conditions(target_warmth=4, rainy=False)
        pieces = [piece("hoodie"), piece("jeans-straight"), piece("sneakers-white")]

        # Act
        score = weather_score(pieces, dry)

        # Assert
        assert score == 0


class TestBudgetScore:
    def test_inside_the_ceiling_there_is_no_penalty(self):
        # Arrange: 14 970 при потолке 15 000
        pieces = [piece("tee-white"), piece("chinos"), piece("sneakers-white")]

        # Act
        score = budget_score(pieces, "low")

        # Assert
        assert catalog_total(pieces) == 14970 and score == 0

    def test_penalty_grows_with_the_excess_up_to_six(self):
        # Arrange
        pricey = [piece("coat-wool"), piece("knit"), piece("jeans-straight"), piece("boots")]  # 50 780

        # Act
        score = budget_score(pricey, "low")

        # Assert
        assert score == -6

    def test_a_small_excess_costs_little(self):
        # Arrange: 24 380 при потолке 30 000 — внутри; 14 970 + 1000 над 15 000 — чуть выше
        slightly_over = [piece("hoodie"), piece("jeans-black"), piece("boots")]  # 24 380 против 15 000

        # Act
        score = budget_score(slightly_over, "low")

        # Assert
        assert -6 < score < 0

    @pytest.mark.parametrize("budget", ["high", None, "unknown"])
    def test_no_ceiling_means_no_penalty(self, budget):
        # Arrange
        pricey = [piece("coat-wool"), piece("knit"), piece("jeans-straight"), piece("boots")]

        # Act
        score = budget_score(pricey, budget)

        # Assert
        assert score == 0


class TestDominantStyles:
    def test_style_shared_by_most_pieces_wins(self):
        # Arrange: classic у пальто, брюк и ботинок; minimal только у двух из них
        pieces = [piece("coat-wool"), piece("trousers-wool"), piece("boots")]

        # Act
        styles, cohesion = dominant_styles(pieces, preferred=[])

        # Assert
        assert styles == ("classic",) and cohesion == 3

    def test_a_style_on_a_single_piece_does_not_count(self):
        # Arrange: у всех вещей разные стили
        pieces = [piece("running"), piece("knit"), piece("coat-wool")]

        # Act
        styles, cohesion = dominant_styles(pieces, preferred=[])

        # Assert
        assert (styles, cohesion) == ((), 0)

    def test_a_tie_is_broken_alphabetically_when_the_user_has_no_preference(self):
        # Arrange: classic и vintage у двух вещей каждый, у джинсов свои стили
        pieces = [piece("trench"), piece("boots"), piece("jeans-straight")]

        # Act
        styles, _ = dominant_styles(pieces, preferred=[])

        # Assert
        assert styles == ("classic", "vintage")

    def test_a_tie_is_broken_by_the_users_style(self):
        # Arrange: та же ничья, но человек выбрал винтаж
        pieces = [piece("trench"), piece("boots"), piece("jeans-straight")]

        # Act
        styles, _ = dominant_styles(pieces, preferred=["vintage"])

        # Assert
        assert styles == ("vintage", "classic")

    def test_at_most_two_styles_are_reported(self):
        # Arrange: ничья между тремя стилями — classic, vintage и casual встречаются по два раза
        pieces = [piece("trench"), piece("chinos"), piece("knit")]

        # Act
        styles, cohesion = dominant_styles(pieces, preferred=[])

        # Assert
        assert styles == ("casual", "classic") and cohesion == 2


class TestTitles:
    def test_title_is_stable_for_the_same_outfit(self):
        # Arrange
        pieces = [piece("tee-white"), piece("chinos"), piece("boots")]

        # Act
        first = title_for("c.a~c.b", ("minimal",), pieces)
        second = title_for("c.a~c.b", ("minimal",), pieces)

        # Assert
        assert first == second

    def test_title_comes_from_the_dominant_style(self):
        # Arrange
        pieces = [piece("tee-white")]

        # Act
        title = title_for("some-id", ("sport",), pieces)

        # Assert
        assert title in {"Активный день", "Спорт-шик", "Динамика", "Тренировка и кофе", "В движении"}

    @pytest.mark.parametrize(
        ("color", "title"),
        [("black", "Total black"), ("white", "Total white"), ("beige", "Монохром: бежевый")],
    )
    def test_monochrome_outfit_without_style_is_named_after_its_colour(self, color, title):
        # Arrange
        pieces = [replace(piece("tee-white"), color=color), replace(piece("chinos"), color=color)]

        # Act
        result = title_for("id", (), pieces)

        # Assert
        assert result == title

    def test_a_single_accent_names_the_outfit(self):
        # Arrange
        pieces = [piece("bomber"), piece("tee-white")]

        # Act
        result = title_for("id", (), pieces)

        # Assert
        assert result == "Акцент: зелёный"

    def test_neutral_mix_without_style_is_a_neutral_base(self):
        # Arrange
        pieces = [piece("tee-white"), piece("jeans-straight")]

        # Act
        result = title_for("id", (), pieces)

        # Assert
        assert result == "Нейтральная база"


class TestBuildOutfit:
    def test_pieces_are_ordered_outerwear_top_bottom_shoes(self):
        # Arrange
        shuffled = [piece("boots"), piece("jeans-straight"), piece("coat-wool"), piece("tee-white")]

        # Act
        outfit = build_outfit(shuffled, [])

        # Assert
        assert [p.category for p in outfit.pieces] == ["outerwear", "top", "bottom", "shoes"]
        assert outfit.id == "~".join(p.id for p in outfit.pieces)

    def test_without_weather_outerwear_gives_a_small_bonus(self):
        # Arrange: пальто без стилей, чтобы оно не меняло «сплочённость» образа
        plain_coat = replace(piece("coat-wool"), styles=())
        base = [piece("tee-white"), piece("chinos"), piece("boots")]

        # Act
        with_coat = build_outfit([plain_coat, *base], [])
        without = build_outfit(base, [])

        # Assert
        assert with_coat.score - without.score == pytest.approx(0.5)

    def test_with_weather_the_outerwear_bonus_is_replaced_by_the_weather_score(self):
        # Arrange: жара — пальто только вредит
        hot = Conditions(target_warmth=2, rainy=False)
        base = [piece("tee-white"), piece("chinos"), piece("sneakers-white")]
        plain_coat = replace(piece("coat-wool"), styles=())

        # Act
        with_coat = build_outfit([plain_coat, *base], [], hot)
        without = build_outfit(base, [], hot)

        # Assert
        assert with_coat.score < without.score

    def test_users_matching_style_raises_the_score(self):
        # Arrange
        pieces = [piece("hoodie"), piece("jeans-black"), piece("chunky")]  # street x3

        # Act
        liked = build_outfit(pieces, ["street"])
        neutral = build_outfit(pieces, [])

        # Assert
        assert liked.score - neutral.score == 2
