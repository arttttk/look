def detect_image_extension(head: bytes) -> str | None:
    """Расширение по первым байтам файла, а не по заявленному клиентом типу:
    в хранилище должны попадать только настоящие картинки (JPEG, PNG, WebP)."""
    if head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp"
    return None
