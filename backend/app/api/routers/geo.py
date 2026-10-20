from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import PresenterDep, UseCasesDep, UserDep
from app.api.schemas import CityOut, WeatherOut

router = APIRouter(tags=["geo"])


@router.get("/geo/cities", response_model=list[CityOut])
def search_cities(
    _user: UserDep, use_cases: UseCasesDep, presenter: PresenterDep, q: Annotated[str, Query()]
) -> list[CityOut]:
    """Поиск города по названию (для выбора места вручную)."""
    return [presenter.city(c) for c in use_cases.search_cities().execute(q)]


@router.get("/weather", response_model=WeatherOut)
def get_weather(user: UserDep, use_cases: UseCasesDep, presenter: PresenterDep) -> WeatherOut:
    """Погода сейчас в городе пользователя."""
    current = use_cases.get_current_weather().execute(user)
    return presenter.weather(current.city, current.weather)
