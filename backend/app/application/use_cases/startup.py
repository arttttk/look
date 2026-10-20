from app.application.ports import UnitOfWork
from app.domain.catalog import Catalog, seed_product_data


class SeedCatalog:
    """Первый запуск: кладёт в БД стартовый каталог. Потом его заменит импорт из партнёрских фидов."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self) -> bool:
        """True, если каталог был пуст и мы его заполнили."""
        with self._uow as uow:
            if uow.products.count() > 0:
                return False
            uow.products.add_many(seed_product_data())
            uow.commit()
        return True


class LoadCatalog:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self) -> Catalog:
        with self._uow as uow:
            return Catalog(uow.products.list_all())
