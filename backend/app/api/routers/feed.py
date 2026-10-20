from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import PresenterDep, UseCasesDep, UserDep
from app.api.schemas import FeedPage, OccasionOut, OutfitOut

router = APIRouter(tags=["feed"])


@router.get("/feed", response_model=FeedPage)
def get_feed(
    user: UserDep,
    use_cases: UseCasesDep,
    presenter: PresenterDep,
    cursor: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=20)] = 3,
) -> FeedPage:
    """Лента образов из каталога под «для кого», стили (или стиль региона), погоду и бюджет."""
    page = use_cases.get_feed().execute(user, cursor, limit)
    return FeedPage(items=[presenter.outfit(o) for o in page.items], next_cursor=page.next_cursor)


@router.get("/feed/daily", response_model=list[OutfitOut])
def get_daily(user: UserDep, use_cases: UseCasesDep, presenter: PresenterDep) -> list[OutfitOut]:
    """«Образ дня» на главной — лучшие образы под сегодняшнюю погоду."""
    return [presenter.outfit(o) for o in use_cases.get_daily_outfits().execute(user)]


@router.get("/feed/occasions", response_model=list[OccasionOut])
def get_occasions(user: UserDep, use_cases: UseCasesDep, presenter: PresenterDep) -> list[OccasionOut]:
    """«Рекомендации для вас»: по образу на каждый повод (работа, учёба, вечер...)."""
    pairs = use_cases.get_occasion_outfits().execute(user)
    return [OccasionOut(tag=tag, outfit=presenter.outfit(outfit)) for tag, outfit in pairs]


@router.get("/outfits/{outfit_id}", response_model=OutfitOut)
def get_outfit(outfit_id: str, user: UserDep, use_cases: UseCasesDep, presenter: PresenterDep) -> OutfitOut:
    return presenter.outfit(use_cases.get_outfit().execute(user, outfit_id))
