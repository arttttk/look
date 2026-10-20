import pytest

from app.domain.regions import REGION_STYLES, regional_styles


@pytest.mark.parametrize(
    ("country", "styles"),
    [("RU", ["casual", "classic"]), ("jp", ["minimal", "street"]), ("Jp", ["minimal", "street"])],
)
def test_known_country_gives_its_styles_in_any_case(country, styles):
    # Arrange: входные данные — параметры теста (country, styles)
    # Act
    result = regional_styles(country)

    # Assert
    assert result == styles


@pytest.mark.parametrize("country", ["ZZ", "", None])
def test_unknown_or_missing_country_gives_no_hint(country):
    # Arrange: входные данные — параметры теста (country)
    # Act
    result = regional_styles(country)

    # Assert
    assert result == []


def test_result_is_a_copy_so_the_table_cannot_be_damaged_from_outside():
    # Arrange
    result = regional_styles("RU")

    # Act
    result.append("sport")

    # Assert
    assert regional_styles("RU") == ["casual", "classic"]


def test_every_style_in_the_table_exists():
    # Arrange
    known = {"minimal", "street", "classic", "casual", "sport", "vintage"}

    # Act
    used = {style for styles in REGION_STYLES.values() for style in styles}

    # Assert
    assert used <= known
