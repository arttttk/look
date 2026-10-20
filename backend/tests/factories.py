"""Фабрики сущностей с разумными значениями по умолчанию: тест называет только то, что для него важно."""

import itertools
from datetime import UTC, datetime

from app.domain.entities import Location, User, WardrobeItem

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)
KAZAN = Location("Казань", "RU", 55.79, 49.12, "Europe/Moscow")
TOKYO = Location("Токио", "JP", 35.68, 139.69, "Asia/Tokyo")

_ids = itertools.count(1)


def make_user(**overrides) -> User:
    n = next(_ids)
    values = {"id": f"user{n:04d}", "created_at": NOW, "phone": f"+7999000{n:04d}"} | overrides
    return User(**values)


def make_item(user_id: str, **overrides) -> WardrobeItem:
    n = next(_ids)
    values = {
        "id": f"item{n:04d}",
        "user_id": user_id,
        "category": "top",
        "color": "white",
        "title": "",
        "image_path": f"{user_id}/photo{n}.jpg",
        "created_at": NOW,
    } | overrides
    return WardrobeItem(**values)
