from dataclasses import dataclass

from app.application.catalog_store import CatalogStore
from app.application.errors import NotFound, PayloadTooLarge, UnsupportedMedia
from app.application.personalisation import PersonalisationService
from app.application.policies import WardrobePolicy
from app.application.ports import Clock, FileStorage, UnitOfWork
from app.application.wardrobe_view import engine_items
from app.domain.catalog import Product
from app.domain.entities import User, WardrobeItem, new_id
from app.domain.errors import InvalidValue
from app.domain.images import detect_image_extension
from app.domain.outfits import Outfit, generate_wardrobe_outfits, missing_categories, suggest_products
from app.domain.taxonomy import CATEGORIES, COLORS

MAX_TITLE = 100
MAX_LOOKS = 30

_CATEGORY_IDS = {c["id"] for c in CATEGORIES}


@dataclass(frozen=True)
class MissingCategory:
    category: str
    products: list[Product]


@dataclass(frozen=True)
class Looks:
    outfits: list[Outfit]
    missing: list[MissingCategory]


class ListWardrobeItems:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, user_id: str) -> list[WardrobeItem]:
        with self._uow as uow:
            return uow.wardrobe.list_for_user(user_id)


class AddWardrobeItem:
    def __init__(self, uow: UnitOfWork, storage: FileStorage, clock: Clock, policy: WardrobePolicy):
        self._uow = uow
        self._storage = storage
        self._clock = clock
        self._policy = policy

    def execute(self, user_id: str, category: str, color: str, title: str, photo: bytes) -> WardrobeItem:
        if category not in _CATEGORY_IDS:
            raise InvalidValue("Неизвестная категория")
        if color not in COLORS:
            raise InvalidValue("Неизвестный цвет")
        clean_title = " ".join(title.split())
        if len(clean_title) > MAX_TITLE:
            raise InvalidValue(f"Название не длиннее {MAX_TITLE} символов")
        if len(photo) > self._policy.max_upload_bytes:
            raise PayloadTooLarge("Файл слишком большой")
        extension = detect_image_extension(photo[:16])
        if extension is None:
            raise UnsupportedMedia("Нужна картинка в формате JPEG, PNG или WebP")

        path = self._storage.save(user_id, photo, extension)
        item = WardrobeItem(
            id=new_id(),
            user_id=user_id,
            category=category,
            color=color,
            title=clean_title,
            image_path=path,
            created_at=self._clock.now(),
        )
        try:
            with self._uow as uow:
                uow.wardrobe.add(item)
                uow.commit()
        except Exception:
            self._storage.delete(path)  # вещь не сохранилась — файл-сирота не нужен
            raise
        return item


class DeleteWardrobeItem:
    def __init__(self, uow: UnitOfWork, storage: FileStorage):
        self._uow = uow
        self._storage = storage

    def execute(self, user_id: str, item_id: str) -> None:
        with self._uow as uow:
            item = uow.wardrobe.get(item_id)
            if item is None or item.user_id != user_id:  # чужую вещь не раскрываем
                raise NotFound("Вещь не найдена")
            uow.wardrobe.delete(item_id)
            uow.commit()

        self._storage.delete(item.image_path)  # файл удаляем после успешной фиксации в БД


class GetLooks:
    """Вкладка «Образы»: образы из гардероба и подсказки, чего не хватает.
    Если в обязательной категории пусто, слот закрывается вещью из каталога — её можно купить."""

    def __init__(
        self,
        uow: UnitOfWork,
        catalog: CatalogStore,
        personalisation: PersonalisationService,
        storage: FileStorage,
    ):
        self._uow = uow
        self._catalog = catalog
        self._personalisation = personalisation
        self._storage = storage

    def execute(self, user: User, limit: int = 12) -> Looks:
        with self._uow as uow:
            items = engine_items(uow.wardrobe.list_for_user(user.id), self._storage)

        ctx = self._personalisation.context_for(user)
        catalog = self._catalog.current
        outfits = generate_wardrobe_outfits(
            items, catalog, ctx.department, ctx.styles, max(1, min(limit, MAX_LOOKS)), ctx.conditions
        )
        missing = missing_categories(items) if items else []

        return Looks(
            outfits=outfits,
            missing=[
                MissingCategory(category, suggest_products(catalog, category, ctx.department, ctx.styles))
                for category in missing
            ],
        )
