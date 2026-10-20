from fastapi import APIRouter

from app.api.deps import PresenterDep, UseCasesDep, UserDep
from app.api.schemas import OutfitOut

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("", response_model=list[str])
def list_favorite_ids(user: UserDep, use_cases: UseCasesDep) -> list[str]:
    """id избранных образов, последние добавленные — первыми."""
    return use_cases.list_favorite_ids().execute(user.id)


@router.get("/outfits", response_model=list[OutfitOut])
def list_favorite_outfits(user: UserDep, use_cases: UseCasesDep, presenter: PresenterDep) -> list[OutfitOut]:
    return [presenter.outfit(o) for o in use_cases.list_favorite_outfits().execute(user)]


@router.put("/{outfit_id}", status_code=204)
def add_favorite(outfit_id: str, user: UserDep, use_cases: UseCasesDep) -> None:
    use_cases.add_favorite().execute(user, outfit_id)


@router.delete("/{outfit_id}", status_code=204)
def remove_favorite(outfit_id: str, user: UserDep, use_cases: UseCasesDep) -> None:
    use_cases.remove_favorite().execute(user.id, outfit_id)
