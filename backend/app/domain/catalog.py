"""Каталог товаров в памяти и сидовые данные (порт mobile/src/data/catalog.ts)."""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    id: str
    title: str
    brand: str
    price: int
    category: str
    color: str
    styles: tuple[str, ...]
    department: str  # men | women | unisex
    url: str  # реферальная ссылка; клиентам отдаётся только через /products/{id}/click
    image_url: str | None = None
    warmth: int = 0  # 1 — лёгкая, 2 — средняя, 3 — тёплая; у обуви 0
    weatherproof: bool = True  # не боится дождя


# (id, title, brand, price, category, color, styles, department)
SEED_PRODUCTS: list[tuple[str, str, str, int, str, str, tuple[str, ...], str]] = [
    (
        "jacket-leather",
        "Кожаная куртка",
        "Monoline",
        18900,
        "outerwear",
        "black",
        (
            "minimal",
            "street",
        ),
        "unisex",
    ),
    (
        "coat-wool",
        "Шерстяное пальто",
        "Atelier 9",
        24900,
        "outerwear",
        "gray",
        (
            "classic",
            "minimal",
        ),
        "unisex",
    ),
    (
        "trench",
        "Тренч",
        "Atelier 9",
        15900,
        "outerwear",
        "beige",
        (
            "classic",
            "vintage",
        ),
        "unisex",
    ),
    (
        "bomber",
        "Бомбер",
        "Urban Roots",
        8990,
        "outerwear",
        "green",
        (
            "street",
            "sport",
        ),
        "unisex",
    ),
    (
        "denim-jacket",
        "Джинсовая куртка",
        "Nord",
        7490,
        "outerwear",
        "blue",
        (
            "casual",
            "vintage",
        ),
        "unisex",
    ),
    (
        "hoodie",
        "Худи оверсайз",
        "Urban Roots",
        5490,
        "top",
        "gray",
        (
            "street",
            "casual",
        ),
        "unisex",
    ),
    (
        "tee-black",
        "Футболка базовая",
        "Monoline",
        1990,
        "top",
        "black",
        (
            "minimal",
            "casual",
        ),
        "unisex",
    ),
    (
        "tee-white",
        "Футболка белая",
        "Monoline",
        1990,
        "top",
        "white",
        (
            "minimal",
            "casual",
        ),
        "unisex",
    ),
    (
        "shirt-oxford",
        "Рубашка оксфорд",
        "Nord",
        4290,
        "top",
        "blue",
        (
            "classic",
            "casual",
        ),
        "unisex",
    ),
    (
        "knit",
        "Свитер крупной вязки",
        "Kite",
        6990,
        "top",
        "brown",
        (
            "vintage",
            "casual",
        ),
        "unisex",
    ),
    (
        "turtleneck",
        "Водолазка",
        "Monoline",
        3990,
        "top",
        "black",
        (
            "minimal",
            "classic",
        ),
        "unisex",
    ),
    ("longsleeve", "Лонгслив для тренировок", "Slate", 3490, "top", "gray", ("sport",), "unisex"),
    (
        "blouse",
        "Шёлковая блуза",
        "Atelier 9",
        5990,
        "top",
        "white",
        (
            "classic",
            "minimal",
        ),
        "women",
    ),
    (
        "cardigan",
        "Кардиган",
        "Kite",
        6490,
        "top",
        "beige",
        (
            "vintage",
            "casual",
        ),
        "women",
    ),
    (
        "jeans-straight",
        "Джинсы прямые",
        "Nord",
        5990,
        "bottom",
        "blue",
        (
            "casual",
            "street",
        ),
        "unisex",
    ),
    (
        "jeans-black",
        "Чёрные джинсы",
        "Nord",
        5990,
        "bottom",
        "black",
        (
            "street",
            "minimal",
        ),
        "unisex",
    ),
    (
        "trousers-wool",
        "Брюки со стрелками",
        "Atelier 9",
        7490,
        "bottom",
        "gray",
        (
            "classic",
            "minimal",
        ),
        "unisex",
    ),
    (
        "chinos",
        "Брюки чинос",
        "Nord",
        4990,
        "bottom",
        "beige",
        (
            "casual",
            "classic",
        ),
        "unisex",
    ),
    (
        "cargo",
        "Брюки карго",
        "Urban Roots",
        6290,
        "bottom",
        "green",
        (
            "street",
            "sport",
        ),
        "unisex",
    ),
    (
        "joggers",
        "Джоггеры",
        "Slate",
        3990,
        "bottom",
        "black",
        (
            "sport",
            "casual",
        ),
        "unisex",
    ),
    (
        "skirt-midi",
        "Юбка миди",
        "Atelier 9",
        5490,
        "bottom",
        "brown",
        (
            "classic",
            "vintage",
        ),
        "women",
    ),
    (
        "wide-trousers",
        "Широкие брюки",
        "Monoline",
        6990,
        "bottom",
        "black",
        (
            "minimal",
            "casual",
        ),
        "women",
    ),
    (
        "sneakers-white",
        "Кеды белые",
        "Slate",
        7990,
        "shoes",
        "white",
        (
            "casual",
            "minimal",
        ),
        "unisex",
    ),
    (
        "boots",
        "Ботинки челси",
        "Slate",
        12900,
        "shoes",
        "black",
        (
            "classic",
            "vintage",
        ),
        "unisex",
    ),
    (
        "running",
        "Кроссовки беговые",
        "Slate",
        9490,
        "shoes",
        "gray",
        (
            "sport",
            "street",
        ),
        "unisex",
    ),
    ("chunky", "Массивные кроссовки", "Urban Roots", 10900, "shoes", "black", ("street",), "unisex"),
    (
        "derby",
        "Дерби",
        "Slate",
        11900,
        "shoes",
        "brown",
        (
            "classic",
            "vintage",
        ),
        "men",
    ),
    (
        "loafers",
        "Лоферы",
        "Slate",
        9900,
        "shoes",
        "brown",
        (
            "classic",
            "vintage",
        ),
        "women",
    ),
]


# Тепло вещей (1 лёгкая, 2 средняя, 3 тёплая). Обувь не указана: тепло считается по верху и низу.
WARMTH: dict[str, int] = {
    "jacket-leather": 2, "coat-wool": 3, "trench": 2, "bomber": 2, "denim-jacket": 1,
    "hoodie": 2, "tee-black": 1, "tee-white": 1, "shirt-oxford": 1, "knit": 3, "turtleneck": 2,
    "longsleeve": 1, "blouse": 1, "cardigan": 2,
    "jeans-straight": 2, "jeans-black": 2, "trousers-wool": 2, "chinos": 1, "cargo": 2,
    "joggers": 2, "skirt-midi": 1, "wide-trousers": 1,
}  # fmt: skip

# Обувь, которая плохо переносит дождь.
NOT_WEATHERPROOF: set[str] = {"sneakers-white", "running", "loafers"}


def affiliate_url(product_id: str) -> str:
    # Заглушка: тут будет ссылка партнёрской сети с нашим реферальным кодом (и ERID).
    return f"https://example.com/shop/{product_id}?ref=look"


def seed_product_data() -> list[Product]:
    return [
        Product(
            id_,
            title,
            brand,
            price,
            category,
            color,
            styles,
            department,
            affiliate_url(id_),
            warmth=WARMTH.get(id_, 0),
            weatherproof=id_ not in NOT_WEATHERPROOF,
        )
        for id_, title, brand, price, category, color, styles, department in SEED_PRODUCTS
    ]


class Catalog:
    """Неизменяемый снимок каталога. Движок образов работает только с ним, без обращений к БД."""

    def __init__(self, products: Iterable[Product]):
        self.products: list[Product] = list(products)
        self.by_id: dict[str, Product] = {p.id: p for p in self.products}
        # Готовая лента по (для кого, стили, погода, бюджет): каталог неизменяем, пересчитывать незачем.
        self.feed_cache: dict[tuple, list] = {}

    def for_department(self, department: str) -> list[Product]:
        # Мужское — мужское и унисекс, женское — женское и унисекс, «без разницы» — всё.
        if department == "any":
            return self.products
        return [p for p in self.products if p.department in ("unisex", department)]
