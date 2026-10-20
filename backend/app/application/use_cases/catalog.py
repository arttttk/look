from app.application.catalog_store import CatalogStore
from app.application.errors import NotFound
from app.application.ports import Clock, UnitOfWork
from app.domain.catalog import Product
from app.domain.entities import ClickEvent


class ListProducts:
    def __init__(self, catalog: CatalogStore):
        self._catalog = catalog

    def execute(
        self,
        department: str = "any",
        category: str | None = None,
        style: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Product]:
        products = self._catalog.current.for_department(department)
        if category:
            products = [p for p in products if p.category == category]
        if style:
            products = [p for p in products if style in p.styles]
        return products[offset : offset + limit]


class GetProduct:
    def __init__(self, catalog: CatalogStore):
        self._catalog = catalog

    def execute(self, product_id: str) -> Product:
        product = self._catalog.current.by_id.get(product_id)
        if product is None:
            raise NotFound("Товар не найден")
        return product


class TrackProductClick:
    """Нажатие «Купить»: фиксируем переход и отдаём реферальную ссылку. Единая точка, куда потом
    добавятся маркировка рекламы (ERID) и параметры партнёрской сети."""

    def __init__(self, uow: UnitOfWork, catalog: CatalogStore, clock: Clock):
        self._uow = uow
        self._catalog = catalog
        self._clock = clock

    def execute(
        self,
        product_id: str,
        user_id: str | None = None,
        outfit_id: str | None = None,
        source: str = "app",
    ) -> str:
        product = self._catalog.current.by_id.get(product_id)
        if product is None:
            raise NotFound("Товар не найден")

        with self._uow as uow:
            uow.clicks.add(
                ClickEvent(
                    product_id=product.id,
                    user_id=user_id,
                    outfit_id=outfit_id,
                    source=source,
                    created_at=self._clock.now(),
                )
            )
            uow.commit()
        return product.url
