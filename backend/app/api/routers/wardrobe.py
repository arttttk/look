from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from app.api.deps import ContainerDep, PresenterDep, UseCasesDep, UserDep
from app.api.schemas import LooksOut, MissingOut, WardrobeItemOut
from app.domain.taxonomy import Category, ColorId

router = APIRouter(tags=["wardrobe"])


@router.get("/wardrobe/items", response_model=list[WardrobeItemOut])
def list_items(user: UserDep, use_cases: UseCasesDep, presenter: PresenterDep) -> list[WardrobeItemOut]:
    return [presenter.item(i) for i in use_cases.list_wardrobe_items().execute(user.id)]


@router.post("/wardrobe/items", response_model=WardrobeItemOut, status_code=201)
def add_item(
    user: UserDep,
    use_cases: UseCasesDep,
    presenter: PresenterDep,
    container: ContainerDep,
    photo: Annotated[UploadFile, File()],
    category: Annotated[Category, Form()],
    color: Annotated[ColorId, Form()],
    title: Annotated[str, Form()] = "",
) -> WardrobeItemOut:
    # Читаем на байт больше лимита: use case увидит превышение, а память не раздувается от огромных файлов.
    data = photo.file.read(container.wardrobe_policy.max_upload_bytes + 1)
    item = use_cases.add_wardrobe_item().execute(user.id, category, color, title, data)
    return presenter.item(item)


@router.delete("/wardrobe/items/{item_id}", status_code=204)
def delete_item(item_id: str, user: UserDep, use_cases: UseCasesDep) -> None:
    use_cases.delete_wardrobe_item().execute(user.id, item_id)


@router.get("/looks", response_model=LooksOut)
def get_looks(user: UserDep, use_cases: UseCasesDep, presenter: PresenterDep, limit: int = 12) -> LooksOut:
    """Вкладка «Образы»: образы из гардероба пользователя и подсказки, чего не хватает."""
    looks = use_cases.get_looks().execute(user, limit)
    return LooksOut(
        outfits=[presenter.outfit(o) for o in looks.outfits],
        missing=[
            MissingOut(category=m.category, products=[presenter.product(p) for p in m.products])
            for m in looks.missing
        ],
    )
