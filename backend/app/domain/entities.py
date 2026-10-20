"""Сущности предметной области. Обычные dataclass без привязки к БД и фреймворкам:
репозитории превращают их в строки таблиц и обратно."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta


def new_id() -> str:
    return uuid.uuid4().hex


@dataclass(frozen=True)
class Location:
    city: str
    country_code: str
    lat: float
    lon: float
    timezone: str | None = None


@dataclass
class User:
    id: str
    created_at: datetime
    # Как человек входит: хотя бы одно из двух (нормализованные значения).
    phone: str | None = None
    email: str | None = None
    # Профиль
    name: str | None = None
    birth_year: int | None = None
    onboarded: bool = False
    department: str = "any"
    # Пустой список после онбординга означает «не определился» — тогда подсказкой служит стиль региона.
    styles: list[str] = field(default_factory=list)
    budget: str | None = None
    location: Location | None = None

    @classmethod
    def register(cls, kind: str, identifier: str, now: datetime) -> "User":
        contact = {"phone": identifier} if kind == "phone" else {"email": identifier}
        return cls(id=new_id(), created_at=now, **contact)


@dataclass
class AuthSession:
    """Сессия входа. Хранится только хэш токена: утечка базы не раскрывает рабочих токенов."""

    token_hash: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at <= now

    def needs_touch(self, now: datetime) -> bool:
        # Отметку «последнего использования» обновляем раз в час, а не на каждый запрос.
        return now - self.last_used_at > timedelta(hours=1)


@dataclass
class OtpCode:
    """Одноразовый код входа. Хранится только HMAC-хэш."""

    identifier: str
    kind: str
    code_hash: str
    created_at: datetime
    expires_at: datetime
    attempts: int = 0
    consumed: bool = False
    id: int | None = None  # назначает хранилище

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at <= now


@dataclass
class WardrobeItem:
    id: str
    user_id: str
    category: str
    color: str
    title: str
    image_path: str  # путь в файловом хранилище, не URL
    created_at: datetime


@dataclass(frozen=True)
class Favorite:
    user_id: str
    outfit_id: str
    created_at: datetime


@dataclass
class ClickEvent:
    """Клик «Купить» — основа учёта партнёрских переходов."""

    product_id: str
    created_at: datetime
    user_id: str | None = None
    outfit_id: str | None = None
    source: str = "app"
    id: int | None = None
