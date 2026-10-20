from app.application.catalog_store import CatalogStore
from app.application.errors import NotFound
from app.application.ports import Clock, FileStorage, UnitOfWork
from app.application.wardrobe_view import engine_items
from app.domain.entities import Favorite, User
from app.domain.outfits import Outfit, resolve_outfit


class ListFavoriteIds:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, user_id: str) -> list[str]:
        with self._uow as uow:
            return uow.favorites.ids_for_user(user_id)


class ListFavoriteOutfits:
    def __init__(self, uow: UnitOfWork, catalog: CatalogStore, storage: FileStorage):
        self._uow = uow
        self._catalog = catalog
        self._storage = storage

    def execute(self, user: User) -> list[Outfit]:
        with self._uow as uow:
            ids = uow.favorites.ids_for_user(user.id)
            items = engine_items(uow.wardrobe.list_for_user(user.id), self._storage)

        by_id = {i.id: i for i in items}
        outfits = (resolve_outfit(outfit_id, self._catalog.current, by_id, user.styles) for outfit_id in ids)
        # Образы, из которых удалили вещь, молча пропускаем.
        return [o for o in outfits if o is not None]


class AddFavorite:
    def __init__(self, uow: UnitOfWork, catalog: CatalogStore, storage: FileStorage, clock: Clock):
        self._uow = uow
        self._catalog = catalog
        self._storage = storage
        self._clock = clock

    def execute(self, user: User, outfit_id: str) -> None:
        with self._uow as uow:
            items = engine_items(uow.wardrobe.list_for_user(user.id), self._storage)
            if (
                resolve_outfit(outfit_id, self._catalog.current, {i.id: i for i in items}, user.styles)
                is None
            ):
                raise NotFound("Образ не найден")

            if not uow.favorites.exists(user.id, outfit_id):  # повторное добавление безвредно
                uow.favorites.add(
                    Favorite(user_id=user.id, outfit_id=outfit_id, created_at=self._clock.now())
                )
                uow.commit()


class RemoveFavorite:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, user_id: str, outfit_id: str) -> None:
        with self._uow as uow:
            uow.favorites.remove(user_id, outfit_id)  # убирать то, чего нет, — не ошибка
            uow.commit()
