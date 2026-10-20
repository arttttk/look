from dataclasses import dataclass

from app.application.catalog_store import CatalogStore
from app.application.errors import NotFound
from app.application.personalisation import PersonalisationService
from app.application.ports import FileStorage, UnitOfWork
from app.application.wardrobe_view import engine_items
from app.domain.entities import User
from app.domain.outfits import (
    Outfit,
    generate_feed_outfits,
    generate_occasion_outfits,
    resolve_outfit,
)

DAILY_COUNT = 4


@dataclass(frozen=True)
class FeedPage:
    items: list[Outfit]
    next_cursor: int | None


class GetFeed:
    """Лента образов из каталога под «для кого», стили (или стиль региона), погоду и бюджет пользователя."""

    def __init__(self, catalog: CatalogStore, personalisation: PersonalisationService):
        self._catalog = catalog
        self._personalisation = personalisation

    def execute(self, user: User, cursor: int = 0, limit: int = 3) -> FeedPage:
        ctx = self._personalisation.context_for(user)
        outfits = generate_feed_outfits(
            self._catalog.current, ctx.department, ctx.styles, ctx.conditions, ctx.budget
        )
        end = cursor + limit
        return FeedPage(items=outfits[cursor:end], next_cursor=end if end < len(outfits) else None)


class GetDailyOutfits:
    """«Образ дня» на главной — лучшие образы ленты, то есть самые подходящие под сегодняшнюю погоду."""

    def __init__(self, catalog: CatalogStore, personalisation: PersonalisationService):
        self._catalog = catalog
        self._personalisation = personalisation

    def execute(self, user: User) -> list[Outfit]:
        ctx = self._personalisation.context_for(user)
        outfits = generate_feed_outfits(
            self._catalog.current, ctx.department, ctx.styles, ctx.conditions, ctx.budget
        )
        return outfits[:DAILY_COUNT]


class GetOccasionOutfits:
    """«Рекомендации для вас»: по образу на каждый повод (работа, учёба, вечер...)."""

    def __init__(self, catalog: CatalogStore, personalisation: PersonalisationService):
        self._catalog = catalog
        self._personalisation = personalisation

    def execute(self, user: User) -> list[tuple[str, Outfit]]:
        ctx = self._personalisation.context_for(user)
        return generate_occasion_outfits(
            self._catalog.current, ctx.department, ctx.styles, ctx.conditions, ctx.budget
        )


class GetOutfit:
    """Образ целиком по id: из каталога и/или из гардероба пользователя."""

    def __init__(self, uow: UnitOfWork, catalog: CatalogStore, storage: FileStorage):
        self._uow = uow
        self._catalog = catalog
        self._storage = storage

    def execute(self, user: User, outfit_id: str) -> Outfit:
        with self._uow as uow:
            items = engine_items(uow.wardrobe.list_for_user(user.id), self._storage)

        outfit = resolve_outfit(outfit_id, self._catalog.current, {i.id: i for i in items}, user.styles)
        if outfit is None:
            raise NotFound("Образ не найден: возможно, одной из вещей уже нет")
        return outfit
