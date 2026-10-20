import pytest

from app.domain.images import detect_image_extension


@pytest.mark.parametrize(
    ("head", "extension"),
    [
        (b"\xff\xd8\xff\xe0" + b"\x00" * 12, ".jpg"),
        (b"\x89PNG\r\n\x1a\n" + b"\x00" * 8, ".png"),
        (b"RIFF\x00\x00\x00\x00WEBPVP8 ", ".webp"),
    ],
)
def test_supported_formats_are_recognised_by_content(head, extension):
    # Arrange: заявленный клиентом тип не учитывается — только первые байты

    # Act
    result = detect_image_extension(head)

    # Assert
    assert result == extension


@pytest.mark.parametrize(
    "head",
    [b"", b"GIF89a" + b"\x00" * 10, b"<?php echo 1; ?>", b"RIFF\x00\x00\x00\x00WAVEfmt ", b"%PDF-1.7\n"],
)
def test_anything_else_is_not_an_image(head):
    # Arrange: входные данные — параметры теста (head)
    # Act
    result = detect_image_extension(head)

    # Assert
    assert result is None
