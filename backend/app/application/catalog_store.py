from app.domain.catalog import Catalog


class CatalogStore:
    """Держит текущий снимок каталога. Каталог читают все запросы, а меняется он редко
    (при старте или импорте), поэтому снимок живёт в памяти, а не запрашивается из БД каждый раз."""

    def __init__(self, catalog: Catalog | None = None):
        self._catalog = catalog or Catalog([])

    @property
    def current(self) -> Catalog:
        return self._catalog

    def replace(self, catalog: Catalog) -> None:
        self._catalog = catalog
