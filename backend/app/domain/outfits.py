"""Автоподбор образов. Порт mobile/src/lib/outfits.ts (плюс подбор под погоду и бюджет) —
чистые функции без БД и HTTP.

Формат id образа общий с клиентом: id вещей через «~», у вещей каталога префикс «c.»,
у вещей гардероба «w.». Образ целиком восстанавливается из id (resolve_outfit).
"""

from collections.abc import Sequence
from dataclasses import dataclass, replace

from app.domain.catalog import Catalog, Product
from app.domain.taxonomy import BUDGET_CAPS, CATEGORIES, COLORS
from app.domain.weather import Conditions

ORDER = ["outerwear", "top", "bottom", "shoes"]
REQUIRED = ["top", "bottom", "shoes"]
MAX_PER_CATEGORY = 12  # вещей гардероба одной категории в переборе
FILL_PER_CATEGORY = 3  # вещей каталога, закрывающих пустой слот гардероба
MAX_POOL = 12  # вещей каталога одной категории в переборе ленты: ограничивает O(n^4) на большом каталоге
FEED_SIZE = 80
WEATHER_WEIGHT = 1.0  # штраф за каждую единицу расхождения «тепла» образа с погодой
RAIN_PENALTY = 1.5  # обувь, которая плохо переносит дождь
OUTERWEAR_BONUS = 0.5  # без данных о погоде верхняя одежда просто делает образ полнее
FEED_CACHE_LIMIT = 256
MIN_AFFORDABLE = 12  # столько образов в бюджете должно быть, чтобы показывать только их

# У вещей гардероба нет данных о тепле (пока их никто не размечает) — берём типичное по категории.
WARDROBE_WARMTH = {"outerwear": 2, "top": 1, "bottom": 2}

# Сочетания, которые считаются не лучшими: небольшой штраф.
CLASHES = [("navy", "black"), ("brown", "black")]

TITLES: dict[str, list[str]] = {
    "minimal": [
        "Городской минимализм",
        "Чистые линии",
        "Тихая роскошь",
        "Монохромный ритм",
        "Ничего лишнего",
    ],
    "street": ["Уличный ритм", "Свободный крой", "Городской стритвир", "Асфальт и неон", "Район и музыка"],
    "classic": ["Классика без лишнего", "Офисная классика", "Строгий силуэт", "Деловой выход", "Вне времени"],
    "casual": ["Лёгкий кэжуал", "Удобно и просто", "Выходной образ", "Мягкий день", "Без усилий"],
    "sport": ["Активный день", "Спорт-шик", "Динамика", "Тренировка и кофе", "В движении"],
    "vintage": ["Осенний винтаж", "Ретро-настроение", "Тёплый слой", "Привет из 90-х", "Антикварная лавка"],
}

OCCASIONS: list[tuple[str, list[str]]] = [
    ("Работа", ["classic", "minimal"]),
    ("Учёба", ["casual", "street"]),
    ("Прогулка", ["street", "casual", "vintage"]),
    ("Вечер", ["classic", "vintage", "minimal"]),
    ("Спорт", ["sport"]),
    ("Выходные", ["casual", "vintage"]),
]


@dataclass(frozen=True)
class ItemData:
    """Вещь из гардероба пользователя."""

    id: str
    category: str
    color: str
    title: str
    created_at: float  # unix-время: свежие вещи в переборе приоритетнее
    image_url: str | None = None


@dataclass(frozen=True)
class Piece:
    id: str  # 'c.<productId>' — из каталога, 'w.<itemId>' — из гардероба
    origin: str  # 'catalog' | 'wardrobe'
    category: str
    title: str
    color: str
    styles: tuple[str, ...]  # у вещей гардероба пусто: стиль им пока не определяется
    image_url: str | None = None
    product: Product | None = None
    warmth: int = 0
    weatherproof: bool = True


@dataclass(frozen=True)
class Outfit:
    id: str
    title: str
    styles: tuple[str, ...]
    pieces: tuple[Piece, ...]
    score: float


def piece_from_product(product: Product) -> Piece:
    return Piece(
        id=f"c.{product.id}",
        origin="catalog",
        category=product.category,
        title=product.title,
        color=product.color,
        styles=product.styles,
        image_url=product.image_url,
        product=product,
        warmth=product.warmth,
        weatherproof=product.weatherproof,
    )


def item_label(item: ItemData) -> str:
    if item.title.strip():
        return item.title.strip()
    return next((c["title"] for c in CATEGORIES if c["id"] == item.category), item.category)


def piece_from_item(item: ItemData) -> Piece:
    return Piece(
        id=f"w.{item.id}",
        origin="wardrobe",
        category=item.category,
        title=item_label(item),
        color=item.color,
        styles=(),
        image_url=item.image_url,
        warmth=WARDROBE_WARMTH.get(item.category, 0),
    )


def pieces_to_buy(outfit: Outfit) -> list[Piece]:
    """Вещи образа, которых нет в гардеробе и которые можно купить по реферальной ссылке."""
    return [p for p in outfit.pieces if p.origin == "catalog"]


def _hash(text: str) -> int:
    value = 0
    for ch in text:
        value = (value * 31 + ord(ch)) & 0xFFFFFFFF
    return value


def color_score(pieces: Sequence[Piece]) -> float:
    """Не больше одного акцентного цвета; нейтральная база — плюс."""
    colors = [p.color for p in pieces]
    accents = {c for c in colors if not COLORS[c].neutral}

    score = 1.0 if not accents else -(len(accents) - 1) * 3.0
    for a, b in CLASHES:
        if a in colors and b in colors:
            score -= 0.5
    return score


def weather_score(pieces: Sequence[Piece], conditions: Conditions) -> float:
    """Тепло образа (верх + низ + верхняя одежда) должно быть близко к тому, что нужно по погоде;
    в дождь не берём обувь, которая его не переносит."""
    warmth = sum(p.warmth for p in pieces if p.category in ("outerwear", "top", "bottom"))
    score = -abs(warmth - conditions.target_warmth) * WEATHER_WEIGHT
    if conditions.rainy and any(p.category == "shoes" and not p.weatherproof for p in pieces):
        score -= RAIN_PENALTY
    return score


def catalog_total(pieces: Sequence[Piece]) -> int:
    return sum(p.product.price for p in pieces if p.product)


def budget_score(pieces: Sequence[Piece], budget: str | None) -> float:
    """Мягкий штраф за превышение потолка бюджета: до -6 за превышение вдвое и больше.
    Работает, когда образов в бюджете почти нет и жёсткий фильтр (см. generate_feed_outfits) не включается."""
    cap = BUDGET_CAPS.get(budget or "")
    if not cap:
        return 0.0
    return -min(6.0, 6.0 * max(0, catalog_total(pieces) - cap) / cap)


def dominant_styles(pieces: Sequence[Piece], preferred: Sequence[str]) -> tuple[tuple[str, ...], int]:
    """Стиль образа — тот, что совпал минимум у двух вещей; при равенстве выигрывают стили пользователя."""
    counts: dict[str, int] = {}
    for piece in pieces:
        for style in piece.styles:
            counts[style] = counts.get(style, 0) + 1

    top = max(counts.values(), default=0)
    if top < 2:
        return (), 0

    styles = sorted((s for s, n in counts.items() if n == top), key=lambda s: (s not in preferred, s))[:2]
    return tuple(styles), top


def title_for(outfit_id: str, styles: Sequence[str], pieces: Sequence[Piece]) -> str:
    if styles:
        names = TITLES[styles[0]]
        return names[_hash(outfit_id) % len(names)]

    colors = list(dict.fromkeys(p.color for p in pieces))
    if len(colors) == 1:
        color = colors[0]
        if color == "black":
            return "Total black"
        if color == "white":
            return "Total white"
        return f"Монохром: {COLORS[color].title.lower()}"

    accent = next((c for c in colors if not COLORS[c].neutral), None)
    return f"Акцент: {COLORS[accent].title.lower()}" if accent else "Нейтральная база"


def build_outfit(
    pieces: Sequence[Piece],
    user_styles: Sequence[str],
    conditions: Conditions | None = None,
    budget: str | None = None,
) -> Outfit:
    ordered = sorted(pieces, key=lambda p: ORDER.index(p.category) if p.category in ORDER else len(ORDER))
    outfit_id = "~".join(p.id for p in ordered)
    styles, cohesion = dominant_styles(ordered, user_styles)

    personal = sum(1 for s in styles if s in user_styles)
    score = color_score(ordered) + cohesion + personal * 2 + budget_score(ordered, budget)
    score += weather_score(ordered, conditions) if conditions else _outerwear_bonus(ordered)

    return Outfit(
        id=outfit_id,
        title=title_for(outfit_id, styles, ordered),
        styles=styles,
        pieces=tuple(ordered),
        score=score,
    )


def _outerwear_bonus(pieces: Sequence[Piece]) -> float:
    return OUTERWEAR_BONUS if any(p.category == "outerwear" for p in pieces) else 0.0


def combine(pools: dict[str, list[Piece]]) -> list[list[Piece]]:
    outer_options: list[Piece | None] = [None, *pools.get("outerwear", [])]
    result: list[list[Piece]] = []

    for top in pools.get("top", []):
        for bottom in pools.get("bottom", []):
            for shoes in pools.get("shoes", []):
                for outer in outer_options:
                    result.append([outer, top, bottom, shoes] if outer else [top, bottom, shoes])

    # Явно конфликтующие по цвету образы убираем, если есть из чего выбирать.
    harmonious = [pieces for pieces in result if color_score(pieces) >= 0]
    return harmonious or result


def pick_diverse(outfits: Sequence[Outfit], limit: int, max_uses: int = 2) -> list[Outfit]:
    """Лучшие образы вперёд, но одна вещь не занимает всю ленту: сначала образы, где каждая вещь
    встречается не больше max_uses раз, потом добираем остальные."""
    ranked = sorted(outfits, key=lambda o: (-o.score, o.id))
    uses: dict[str, int] = {}
    picked: list[Outfit] = []
    chosen: set[str] = set()

    def take(outfit: Outfit) -> None:
        picked.append(outfit)
        chosen.add(outfit.id)
        for piece in outfit.pieces:
            uses[piece.id] = uses.get(piece.id, 0) + 1

    for outfit in ranked:
        if len(picked) >= limit:
            break
        if all(uses.get(p.id, 0) < max_uses for p in outfit.pieces):
            take(outfit)
    for outfit in ranked:
        if len(picked) >= limit:
            break
        if outfit.id not in chosen:
            take(outfit)
    return picked


def _overlap(piece: Piece, user_styles: Sequence[str]) -> int:
    return sum(1 for s in piece.styles if s in user_styles)


def generate_feed_outfits(
    catalog: Catalog,
    department: str,
    user_styles: Sequence[str],
    conditions: Conditions | None = None,
    budget: str | None = None,
) -> list[Outfit]:
    """Лента: образы целиком из каталога, отранжированные под стили, погоду и бюджет пользователя."""
    key = (department, tuple(sorted(user_styles)), conditions, budget)
    cached = catalog.feed_cache.get(key)
    if cached is not None:
        return cached

    pools: dict[str, list[Piece]] = {}
    for product in catalog.for_department(department):
        pools.setdefault(product.category, []).append(piece_from_product(product))

    # Ограничиваем пул: сначала вещи, близкие по стилю пользователя (детерминированно).
    for category, pool in pools.items():
        pool.sort(key=lambda p: (-_overlap(p, user_styles), p.id))
        pools[category] = pool[:MAX_POOL]

    outfits = [build_outfit(pieces, user_styles, conditions, budget) for pieces in combine(pools)]

    # Бюджет — ограничение, а не пожелание: если образов в бюджете достаточно, остальные не показываем.
    cap = BUDGET_CAPS.get(budget or "")
    if cap:
        affordable = [o for o in outfits if catalog_total(o.pieces) <= cap]
        if len(affordable) >= MIN_AFFORDABLE:
            outfits = affordable

    result = pick_diverse(outfits, FEED_SIZE)

    if len(catalog.feed_cache) >= FEED_CACHE_LIMIT:
        catalog.feed_cache.clear()
    catalog.feed_cache[key] = result
    return result


def generate_wardrobe_outfits(
    items: Sequence[ItemData],
    catalog: Catalog,
    department: str,
    user_styles: Sequence[str],
    limit: int = 12,
    conditions: Conditions | None = None,
) -> list[Outfit]:
    """Образы из гардероба. Если в обязательной категории (верх/низ/обувь) пусто, слот закрывается
    вещью из каталога — её можно купить по реферальной ссылке."""
    if not items:
        return []

    store = [piece_from_product(p) for p in catalog.for_department(department)]
    own = [piece_from_item(i) for i in sorted(items, key=lambda i: -i.created_at)]
    pools: dict[str, list[Piece]] = {}

    for category in ORDER:
        mine = [p for p in own if p.category == category][:MAX_PER_CATEGORY]
        if mine or category not in REQUIRED:
            pools[category] = mine
            continue

        fill = [p for p in store if p.category == category]
        fill.sort(key=lambda p: (-_overlap(p, user_styles), p.id))
        pools[category] = fill[:FILL_PER_CATEGORY]

    # Свои вещи важнее: каждая вещь «на покупку» сильно снижает оценку образа.
    outfits = []
    for pieces in combine(pools):
        outfit = build_outfit(pieces, user_styles)
        climate = weather_score(outfit.pieces, conditions) if conditions else _outerwear_bonus(outfit.pieces)
        score = color_score(outfit.pieces) + climate - 3 * len(pieces_to_buy(outfit))
        outfits.append(replace(outfit, score=score))

    return pick_diverse(outfits, limit)


def missing_categories(items: Sequence[ItemData]) -> list[str]:
    """Категории, которых не хватает в гардеробе для полного образа."""
    have = {i.category for i in items}
    return [c for c in REQUIRED if c not in have]


def suggest_products(
    catalog: Catalog, category: str, department: str, user_styles: Sequence[str], limit: int = 4
) -> list[Product]:
    products = [p for p in catalog.for_department(department) if p.category == category]
    products.sort(key=lambda p: (-sum(1 for s in p.styles if s in user_styles), p.price))
    return products[:limit]


def resolve_outfit(
    outfit_id: str,
    catalog: Catalog,
    items_by_id: dict[str, ItemData],
    user_styles: Sequence[str],
) -> Outfit | None:
    """Образ целиком из id. None — если какой-то вещи уже нет (например, удалили из гардероба)."""
    pieces: list[Piece] = []

    for token in outfit_id.split("~"):
        if token.startswith("c."):
            product = catalog.by_id.get(token[2:])
            if product is None:
                return None
            pieces.append(piece_from_product(product))
        elif token.startswith("w."):
            item = items_by_id.get(token[2:])
            if item is None:
                return None
            pieces.append(piece_from_item(item))
        else:
            return None

    return build_outfit(pieces, user_styles) if pieces else None


def generate_occasion_outfits(
    catalog: Catalog,
    department: str,
    user_styles: Sequence[str],
    conditions: Conditions | None = None,
    budget: str | None = None,
) -> list[tuple[str, Outfit]]:
    """Подборка «Рекомендации для вас»: по лучшему образу на каждый повод, без повторов."""
    pool = generate_feed_outfits(catalog, department, user_styles, conditions, budget)
    used: set[str] = set()
    result: list[tuple[str, Outfit]] = []

    for tag, styles in OCCASIONS:
        outfit = next((o for o in pool if o.id not in used and any(s in styles for s in o.styles)), None)
        if outfit is None:
            continue
        used.add(outfit.id)
        result.append((tag, outfit))
    return result
