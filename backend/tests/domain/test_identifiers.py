import pytest

from app.domain.errors import InvalidValue
from app.domain.identifiers import normalize_identifier


@pytest.mark.parametrize(
    "raw",
    [
        "+7 (999) 123-45-67",
        "8 999 123-45-67",
        "89991234567",
        "9991234567",
        "  +79991234567  ",
        "+7-999-123-45-67",
    ],
)
def test_russian_phone_in_any_format_becomes_e164(raw):
    # Arrange: номера без «+» трактуются по региону по умолчанию — России

    # Act
    kind, identifier = normalize_identifier(raw, "RU")

    # Assert
    assert (kind, identifier) == ("phone", "+79991234567")


def test_foreign_phone_with_plus_keeps_its_country():
    # Arrange
    raw = "+1 650-253-0000"

    # Act
    kind, identifier = normalize_identifier(raw, "RU")

    # Assert
    assert (kind, identifier) == ("phone", "+16502530000")


def test_default_region_decides_for_numbers_without_plus():
    # Arrange
    raw = "650 253 0000"

    # Act
    _, identifier = normalize_identifier(raw, "US")

    # Assert
    assert identifier == "+16502530000"


def test_email_is_lowercased_and_trimmed():
    # Arrange
    raw = "  Alice.Smith@Example.COM "

    # Act
    kind, identifier = normalize_identifier(raw, "RU")

    # Assert
    assert (kind, identifier) == ("email", "alice.smith@example.com")


@pytest.mark.parametrize(
    "raw", ["", "   ", "abc", "12345", "+999", "name@", "@example.com", "a b@example.com"]
)
def test_garbage_is_rejected(raw):
    # Arrange: входные данные — параметры теста (raw)
    # Act / Assert
    with pytest.raises(InvalidValue, match="телефон или почту"):
        normalize_identifier(raw, "RU")
