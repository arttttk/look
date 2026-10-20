import pytest

from app.domain.catalog import Catalog, Product, seed_product_data


def make_product(product_id: str, department: str) -> Product:
    return Product(
        id=product_id, title="t", brand="b", price=100, category="top", color="black",
        styles=("casual",), department=department, url="https://example.com/x",
    )  # fmt: skip


@pytest.fixture()
def catalog() -> Catalog:
    return Catalog([make_product("m", "men"), make_product("w", "women"), make_product("u", "unisex")])


@pytest.mark.parametrize(
    ("department", "expected"),
    [("any", {"m", "w", "u"}), ("men", {"m", "u"}), ("women", {"w", "u"})],
)
def test_department_filter(catalog, department, expected):
    # Arrange: фикстуры (catalog) и параметры теста (department, expected)
    # Act
    ids = {p.id for p in catalog.for_department(department)}

    # Assert
    assert ids == expected


def test_products_are_found_by_id(catalog):
    # Arrange: состояние задают фикстуры (catalog)
    # Act
    found, missing = catalog.by_id.get("w"), catalog.by_id.get("nope")

    # Assert
    assert found.id == "w" and missing is None


def test_seed_data_has_unique_ids_and_valid_attributes():
    # Arrange: подготовка не требуется
    # Act
    products = seed_product_data()

    # Assert
    assert len({p.id for p in products}) == len(products)
    assert all(p.price > 0 and p.styles for p in products)
    assert all(p.warmth > 0 for p in products if p.category in ("outerwear", "top", "bottom"))
    assert all(p.warmth == 0 for p in products if p.category == "shoes")


def test_shoes_that_fear_water_are_marked():
    # Arrange: подготовка не требуется
    # Act
    by_id = {p.id: p for p in seed_product_data()}

    # Assert
    assert by_id["sneakers-white"].weatherproof is False
    assert by_id["boots"].weatherproof is True
