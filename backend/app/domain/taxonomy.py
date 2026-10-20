"""Справочники: категории, цвета, стили, «для кого». Совпадают с mobile/src/data/{taxonomy,styles}.ts."""

from dataclasses import dataclass
from typing import Literal

Category = Literal["outerwear", "top", "bottom", "shoes", "accessory"]
ColorId = Literal["black", "white", "gray", "beige", "navy", "blue", "brown", "green", "red"]
StyleId = Literal["minimal", "street", "classic", "casual", "sport", "vintage"]
Department = Literal["men", "women", "any"]
Budget = Literal["low", "mid", "high"]
ProductDepartment = Literal["men", "women", "unisex"]


@dataclass(frozen=True)
class Color:
    id: ColorId
    title: str
    hex: str
    # Нейтральные цвета сочетаются почти со всем; акцентных в образе должно быть не больше одного.
    neutral: bool


COLORS: dict[str, Color] = {
    c.id: c
    for c in (
        Color("black", "Чёрный", "#1F1F1F", True),
        Color("white", "Белый", "#EFEDE8", True),
        Color("gray", "Серый", "#9A9A9A", True),
        Color("beige", "Бежевый", "#CDB99A", True),
        Color("navy", "Тёмно-синий", "#222C47", True),
        Color("blue", "Голубой", "#4F74A8", True),
        Color("brown", "Коричневый", "#6B4A35", True),
        Color("green", "Зелёный", "#52704B", False),
        Color("red", "Красный", "#B23A3A", False),
    )
}

CATEGORIES: list[dict[str, str]] = [
    {"id": "outerwear", "title": "Верхняя одежда", "plural": "Верхняя одежда"},
    {"id": "top", "title": "Верх", "plural": "Верх"},
    {"id": "bottom", "title": "Низ", "plural": "Низ"},
    {"id": "shoes", "title": "Обувь", "plural": "Обувь"},
    {"id": "accessory", "title": "Аксессуар", "plural": "Аксессуары"},
]

STYLES: list[dict[str, str]] = [
    {"id": "minimal", "title": "Минимализм", "description": "Чистые линии и нейтральные цвета"},
    {"id": "street", "title": "Стритвир", "description": "Свободный крой, худи и кроссовки"},
    {"id": "classic", "title": "Классика", "description": "Пальто, рубашки, строгие силуэты"},
    {"id": "casual", "title": "Кэжуал", "description": "Удобно и просто на каждый день"},
    {"id": "sport", "title": "Спорт", "description": "Функционально и динамично"},
    {"id": "vintage", "title": "Винтаж", "description": "Образы из прошлых десятилетий"},
]

DEPARTMENTS: list[dict[str, str]] = [
    {"id": "men", "title": "Мужское", "description": "Мужская и унисекс-одежда"},
    {"id": "women", "title": "Женское", "description": "Женская и унисекс-одежда"},
    {"id": "any", "title": "Без разницы", "description": "Показывать всё подряд"},
]

# Потолок цены образа из каталога (руб.); None — без ограничений.
BUDGET_CAPS: dict[str, int | None] = {"low": 15000, "mid": 30000, "high": None}

BUDGETS: list[dict[str, str]] = [
    {"id": "low", "title": "Эконом", "description": "До 15 000 ₽ за образ"},
    {"id": "mid", "title": "Средний", "description": "До 30 000 ₽ за образ"},
    {"id": "high", "title": "Без ограничений", "description": "Цена не главное"},
]
