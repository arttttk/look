"""Порты: что прикладному слою нужно от внешнего мира. Реализации лежат в infrastructure/,
в тестах use case'ов подставляются быстрые подделки в памяти."""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol, Self

from app.domain.catalog import Product
from app.domain.entities import AuthSession, ClickEvent, Favorite, OtpCode, User, WardrobeItem
from app.domain.geo import City
from app.domain.weather import Weather

# --- Репозитории ---------------------------------------------------------------------------


class UserRepository(Protocol):
    def add(self, user: User) -> None: ...
    def get(self, user_id: str) -> User | None: ...
    def get_by_phone(self, phone: str) -> User | None: ...
    def get_by_email(self, email: str) -> User | None: ...
    def save(self, user: User) -> None: ...


class SessionRepository(Protocol):
    def add(self, session: AuthSession) -> None: ...
    def get(self, token_hash: str) -> AuthSession | None: ...
    def save(self, session: AuthSession) -> None: ...
    def delete(self, token_hash: str) -> None: ...


class OtpRepository(Protocol):
    def add(self, code: OtpCode) -> None:
        """Сохраняет код и проставляет ему id."""

    def recent(self, identifier: str, since: datetime) -> list[OtpCode]:
        """Коды, выданные на идентификатор с момента since, новые первыми."""

    def latest_active(self, identifier: str) -> OtpCode | None:
        """Последний ещё не использованный код."""

    def save(self, code: OtpCode) -> None: ...


class ProductRepository(Protocol):
    def count(self) -> int: ...
    def add_many(self, products: Sequence[Product]) -> None: ...
    def list_all(self) -> list[Product]: ...


class WardrobeRepository(Protocol):
    def add(self, item: WardrobeItem) -> None: ...
    def get(self, item_id: str) -> WardrobeItem | None: ...
    def list_for_user(self, user_id: str) -> list[WardrobeItem]:
        """Вещи пользователя, новые первыми."""

    def delete(self, item_id: str) -> None: ...


class FavoriteRepository(Protocol):
    def add(self, favorite: Favorite) -> None: ...
    def exists(self, user_id: str, outfit_id: str) -> bool: ...
    def remove(self, user_id: str, outfit_id: str) -> None: ...
    def ids_for_user(self, user_id: str) -> list[str]:
        """id образов в избранном, последние добавленные первыми."""


class ClickRepository(Protocol):
    def add(self, event: ClickEvent) -> None: ...
    def list_all(self) -> list[ClickEvent]: ...


class UnitOfWork(Protocol):
    """Одна бизнес-транзакция: репозитории видят общие данные, commit фиксирует всё сразу.
    Выход из `with` без commit откатывает изменения."""

    users: UserRepository
    sessions: SessionRepository
    otp_codes: OtpRepository
    products: ProductRepository
    wardrobe: WardrobeRepository
    favorites: FavoriteRepository
    clicks: ClickRepository

    def __enter__(self) -> Self: ...
    def __exit__(self, *exc_info: object) -> None: ...
    def commit(self) -> None: ...


# --- Внешние сервисы -----------------------------------------------------------------------


class Clock(Protocol):
    def now(self) -> datetime:
        """Текущее время в UTC, с часовым поясом."""


class Security(Protocol):
    def new_code(self) -> str: ...
    def hash_code(self, identifier: str, code: str) -> str: ...
    def code_matches(self, identifier: str, code: str, code_hash: str) -> bool: ...
    def new_token(self) -> str: ...
    def hash_token(self, token: str) -> str: ...


class CodeSender(Protocol):
    """Доставляет одноразовый код пользователю. Настоящие реализации (SMS-провайдер, SMTP)
    подключаются здесь, остальной код входа не меняется."""

    def send(self, kind: str, identifier: str, code: str) -> None: ...


class Geocoder(Protocol):
    def search(self, query: str) -> list[City]: ...


class WeatherProvider(Protocol):
    def fetch(self, lat: float, lon: float) -> Weather: ...


class FileStorage(Protocol):
    def save(self, user_id: str, data: bytes, extension: str) -> str:
        """Сохраняет файл и возвращает его путь внутри хранилища."""

    def delete(self, path: str) -> None: ...

    def public_path(self, path: str) -> str:
        """Адрес файла относительно корня сайта: «/media/...». Домен добавляет API."""
