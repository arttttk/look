"""Контракт API. Здесь только форма данных (типы, допустимые значения): бизнес-правила
проверяют use case'ы и домен, чтобы они одинаково работали из любого интерфейса."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.taxonomy import Budget, Category, ColorId, Department, StyleId


class ProductOut(BaseModel):
    """Реферальная ссылка сюда намеренно не входит: клиент получает её через POST /products/{id}/click."""

    id: str
    title: str
    brand: str
    price: int
    category: str
    color: str
    styles: list[str]
    department: str
    image_url: str | None


class PieceOut(BaseModel):
    id: str
    origin: Literal["catalog", "wardrobe"]
    category: str
    title: str
    color: str
    styles: list[str]
    image_url: str | None
    product: ProductOut | None


class OutfitOut(BaseModel):
    id: str
    title: str
    styles: list[str]
    pieces: list[PieceOut]
    score: float


class FeedPage(BaseModel):
    items: list[OutfitOut]
    next_cursor: int | None


class OccasionOut(BaseModel):
    tag: str
    outfit: OutfitOut


class CodeRequest(BaseModel):
    identifier: str = Field(max_length=120, description="Телефон или почта")


class CodeSent(BaseModel):
    kind: Literal["phone", "email"]
    identifier: str  # в нормализованном виде: +79991234567 / name@example.com
    resend_after: int  # через сколько секунд можно запросить код снова
    dev_code: str | None = None  # только при DEV_RETURN_CODE=true


class VerifyIn(BaseModel):
    identifier: str = Field(max_length=120)
    code: str = Field(pattern=r"^\d{6}$")


class TokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user_id: str
    is_new: bool  # первый вход: приложению пора показать онбординг


class LocationIn(BaseModel):
    city: str
    country_code: str
    lat: float
    lon: float
    timezone: str | None = None


class LocationOut(BaseModel):
    city: str
    country_code: str
    lat: float
    lon: float
    timezone: str | None


class ProfileOut(BaseModel):
    id: str
    phone: str | None
    email: str | None
    name: str | None
    birth_year: int | None
    onboarded: bool
    department: Department
    styles: list[StyleId]
    budget: Budget | None
    location: LocationOut | None
    # Что обычно носят в стране пользователя. Подсказка: в ленте работает, только пока styles пуст.
    regional_styles: list[StyleId]


class ProfilePatch(BaseModel):
    """Частичное обновление: меняются только присланные поля; null очищает необязательные
    (name, birth_year, budget, location). Обязательные (department, styles, onboarded) очистить нельзя."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    birth_year: int | None = None
    onboarded: bool | None = None
    department: Department | None = None
    styles: list[StyleId] | None = Field(default=None, max_length=20)
    budget: Budget | None = None
    location: LocationIn | None = None


class CityOut(BaseModel):
    city: str
    region: str | None
    country: str | None
    country_code: str
    lat: float
    lon: float
    timezone: str | None


class WeatherOut(BaseModel):
    city: str
    temperature_c: float
    feels_like_c: float
    condition: Literal["clear", "cloudy", "fog", "rain", "snow", "storm"]
    label: str
    is_day: bool
    precipitation_mm: float
    wind_kmh: float
    observed_at: str


class WardrobeItemOut(BaseModel):
    id: str
    category: Category
    color: ColorId
    title: str
    image_url: str
    created_at: datetime


class MissingOut(BaseModel):
    category: str
    products: list[ProductOut]


class LooksOut(BaseModel):
    outfits: list[OutfitOut]
    missing: list[MissingOut]


class ClickIn(BaseModel):
    outfit_id: str | None = Field(default=None, max_length=600)
    source: str = Field(default="app", max_length=32)


class ClickOut(BaseModel):
    url: str
