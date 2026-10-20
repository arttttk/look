from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse

from app.api.deps import PresenterDep, UseCasesDep, UserDep
from app.api.schemas import ClickIn, ClickOut, ProductOut
from app.domain.taxonomy import Category, Department, StyleId

router = APIRouter(tags=["catalog"])


@router.get("/products", response_model=list[ProductOut])
def list_products(
    use_cases: UseCasesDep,
    presenter: PresenterDep,
    department: Department = "any",
    category: Category | None = None,
    style: StyleId | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProductOut]:
    products = use_cases.list_products().execute(department, category, style, limit, offset)
    return [presenter.product(p) for p in products]


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: str, use_cases: UseCasesDep, presenter: PresenterDep) -> ProductOut:
    return presenter.product(use_cases.get_product().execute(product_id))


@router.post("/products/{product_id}/click", response_model=ClickOut)
def track_click(product_id: str, body: ClickIn, user: UserDep, use_cases: UseCasesDep) -> ClickOut:
    """Приложение зовёт это при нажатии «Купить»: фиксируем переход и отдаём реферальную ссылку."""
    url = use_cases.track_product_click().execute(product_id, user.id, body.outfit_id, body.source)
    return ClickOut(url=url)


@router.get("/r/{product_id}", include_in_schema=False)
def redirect_to_product(product_id: str, use_cases: UseCasesDep) -> RedirectResponse:
    """Публичный редирект для ссылок вне приложения (шаринг, веб). Пользователь неизвестен."""
    url = use_cases.track_product_click().execute(product_id, source="redirect")
    return RedirectResponse(url, status_code=302)
