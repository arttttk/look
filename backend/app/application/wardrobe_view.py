from collections.abc import Iterable

from app.application.ports import FileStorage
from app.domain.entities import WardrobeItem
from app.domain.outfits import ItemData


def engine_items(items: Iterable[WardrobeItem], storage: FileStorage) -> list[ItemData]:
    """Вещи гардероба в том виде, в каком их ждёт движок образов."""
    return [
        ItemData(
            id=item.id,
            category=item.category,
            color=item.color,
            title=item.title,
            created_at=item.created_at.timestamp(),
            image_url=storage.public_path(item.image_path),
        )
        for item in items
    ]
