"""Подделки для тестов: быстрые реализации портов в памяти. Ведут себя как настоящие —
это проверяют контрактные тесты репозиториев (tests/infrastructure/test_repositories.py)."""

import copy
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Self

from app.application.errors import ProviderUnavailable
from app.domain.catalog import Product
from app.domain.entities import AuthSession, ClickEvent, Favorite, OtpCode, User, WardrobeItem
from app.domain.geo import City
from app.domain.weather import Weather


class FrozenClock:
    """Время стоит на месте, пока тест не сдвинет его сам."""

    def __init__(self, now: datetime | None = None):
        self._now = now or datetime(2026, 10, 20, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, **delta: float) -> None:
        self._now += timedelta(**delta)


# --- Хранилище в памяти с настоящей транзакционностью -------------------------------------


@dataclass
class Tables:
    users: dict[str, User] = field(default_factory=dict)
    sessions: dict[str, AuthSession] = field(default_factory=dict)
    otp_codes: dict[int, OtpCode] = field(default_factory=dict)
    products: dict[str, Product] = field(default_factory=dict)
    wardrobe: dict[str, WardrobeItem] = field(default_factory=dict)
    favorites: dict[tuple[str, str], Favorite] = field(default_factory=dict)
    clicks: dict[int, ClickEvent] = field(default_factory=dict)
    next_id: int = 1


class InMemoryDatabase:
    def __init__(self):
        self.tables = Tables()


def _copy[T](value: T) -> T:
    """Репозиторий отдаёт копии, как БД: правка объекта в use case не видна, пока не вызван save."""
    return copy.deepcopy(value)


class FakeUserRepository:
    def __init__(self, tables: Tables):
        self._t = tables

    def add(self, user: User) -> None:
        if any(
            (user.phone and u.phone == user.phone) or (user.email and u.email == user.email)
            for u in self._t.users.values()
        ):
            raise ValueError("Пользователь с таким телефоном или почтой уже есть")
        self._t.users[user.id] = _copy(user)

    def get(self, user_id: str) -> User | None:
        return _copy(self._t.users.get(user_id))

    def get_by_phone(self, phone: str) -> User | None:
        return next((_copy(u) for u in self._t.users.values() if u.phone == phone), None)

    def get_by_email(self, email: str) -> User | None:
        return next((_copy(u) for u in self._t.users.values() if u.email == email), None)

    def save(self, user: User) -> None:
        if user.id not in self._t.users:
            raise LookupError(f"Нет пользователя {user.id}")
        self._t.users[user.id] = _copy(user)


class FakeSessionRepository:
    def __init__(self, tables: Tables):
        self._t = tables

    def add(self, session: AuthSession) -> None:
        self._t.sessions[session.token_hash] = _copy(session)

    def get(self, token_hash: str) -> AuthSession | None:
        return _copy(self._t.sessions.get(token_hash))

    def save(self, session: AuthSession) -> None:
        if session.token_hash not in self._t.sessions:
            raise LookupError("Нет такой сессии")
        self._t.sessions[session.token_hash] = _copy(session)

    def delete(self, token_hash: str) -> None:
        self._t.sessions.pop(token_hash, None)


class FakeOtpRepository:
    def __init__(self, tables: Tables):
        self._t = tables

    def add(self, code: OtpCode) -> None:
        code.id = self._t.next_id
        self._t.next_id += 1
        self._t.otp_codes[code.id] = _copy(code)

    def recent(self, identifier: str, since: datetime) -> list[OtpCode]:
        rows = [c for c in self._t.otp_codes.values() if c.identifier == identifier and c.created_at > since]
        return [_copy(c) for c in sorted(rows, key=lambda c: (c.created_at, c.id), reverse=True)]

    def latest_active(self, identifier: str) -> OtpCode | None:
        rows = [c for c in self._t.otp_codes.values() if c.identifier == identifier and not c.consumed]
        return _copy(max(rows, key=lambda c: (c.created_at, c.id))) if rows else None

    def save(self, code: OtpCode) -> None:
        if code.id not in self._t.otp_codes:
            raise LookupError("Нет такого кода")
        self._t.otp_codes[code.id] = _copy(code)


class FakeProductRepository:
    def __init__(self, tables: Tables):
        self._t = tables

    def count(self) -> int:
        return len(self._t.products)

    def add_many(self, products: Sequence[Product]) -> None:
        for product in products:
            self._t.products[product.id] = product

    def list_all(self) -> list[Product]:
        return [self._t.products[key] for key in sorted(self._t.products)]


class FakeWardrobeRepository:
    def __init__(self, tables: Tables):
        self._t = tables

    def add(self, item: WardrobeItem) -> None:
        self._t.wardrobe[item.id] = _copy(item)

    def get(self, item_id: str) -> WardrobeItem | None:
        return _copy(self._t.wardrobe.get(item_id))

    def list_for_user(self, user_id: str) -> list[WardrobeItem]:
        rows = [i for i in self._t.wardrobe.values() if i.user_id == user_id]
        return [_copy(i) for i in sorted(rows, key=lambda i: (-i.created_at.timestamp(), i.id))]

    def delete(self, item_id: str) -> None:
        self._t.wardrobe.pop(item_id, None)


class FakeFavoriteRepository:
    def __init__(self, tables: Tables):
        self._t = tables

    def add(self, favorite: Favorite) -> None:
        self._t.favorites[(favorite.user_id, favorite.outfit_id)] = favorite

    def exists(self, user_id: str, outfit_id: str) -> bool:
        return (user_id, outfit_id) in self._t.favorites

    def remove(self, user_id: str, outfit_id: str) -> None:
        self._t.favorites.pop((user_id, outfit_id), None)

    def ids_for_user(self, user_id: str) -> list[str]:
        rows = [f for f in self._t.favorites.values() if f.user_id == user_id]
        return [f.outfit_id for f in sorted(rows, key=lambda f: (-f.created_at.timestamp(), f.outfit_id))]


class FakeClickRepository:
    def __init__(self, tables: Tables):
        self._t = tables

    def add(self, event: ClickEvent) -> None:
        event.id = self._t.next_id
        self._t.next_id += 1
        self._t.clicks[event.id] = _copy(event)

    def list_all(self) -> list[ClickEvent]:
        return [_copy(self._t.clicks[key]) for key in sorted(self._t.clicks)]


class FakeUnitOfWork:
    """Транзакция над InMemoryDatabase: то, что не зафиксировано commit(), при выходе из with откатывается."""

    def __init__(self, database: InMemoryDatabase):
        self._db = database
        self._committed: Tables | None = None
        self.commits = 0

    def __enter__(self) -> Self:
        t = self._db.tables
        self._committed = copy.deepcopy(t)
        self.users = FakeUserRepository(t)
        self.sessions = FakeSessionRepository(t)
        self.otp_codes = FakeOtpRepository(t)
        self.products = FakeProductRepository(t)
        self.wardrobe = FakeWardrobeRepository(t)
        self.favorites = FakeFavoriteRepository(t)
        self.clicks = FakeClickRepository(t)
        return self

    def __exit__(self, *exc_info: object) -> None:
        assert self._committed is not None
        self._db.tables = self._committed  # до commit — откат; после commit — состояние на момент commit
        self._committed = None

    def commit(self) -> None:
        self._committed = copy.deepcopy(self._db.tables)
        self.commits += 1


# --- Внешние сервисы -----------------------------------------------------------------------


class FakeSender:
    """Вместо SMS/почты: запоминает отправленные коды."""

    def __init__(self):
        self.sent: list[tuple[str, str, str]] = []  # (вид, идентификатор, код)
        self.fail = False

    def send(self, kind: str, identifier: str, code: str) -> None:
        if self.fail:
            raise RuntimeError("provider is down")
        self.sent.append((kind, identifier, code))

    def last_code(self, identifier: str) -> str:
        return next(code for _, ident, code in reversed(self.sent) if ident == identifier)


class FakeGeocoder:
    def __init__(self):
        self.fail = False
        self.queries: list[str] = []

    def search(self, query: str) -> list[City]:
        self.queries.append(query)
        if self.fail:
            raise ProviderUnavailable("Сервис поиска городов недоступен")
        return [
            City("Казань", "Татарстан", "Россия", "RU", 55.78874, 49.12214, "Europe/Moscow", 1243500),
            City("Kazan", None, "Turkey", "TR", 40.2307, 32.6836, "Europe/Istanbul", 48000),
        ]


class FakeWeatherProvider:
    """Погода, которой тест управляет сам."""

    def __init__(self):
        self.fail = False
        self.calls: list[tuple[float, float]] = []
        self.temperature_c = 18.0
        self.condition = "cloudy"
        self.precipitation_mm = 0.0

    def fetch(self, lat: float, lon: float) -> Weather:
        self.calls.append((lat, lon))
        if self.fail:
            raise ProviderUnavailable("Сервис погоды недоступен")
        return Weather(
            temperature_c=self.temperature_c,
            feels_like_c=self.temperature_c,
            condition=self.condition,
            label="облачно",
            is_day=True,
            precipitation_mm=self.precipitation_mm,
            wind_kmh=5.0,
            observed_at="2026-10-20T12:00",
        )


class FakeStorage:
    def __init__(self):
        self.files: dict[str, bytes] = {}
        self._counter = 0

    def save(self, user_id: str, data: bytes, extension: str) -> str:
        self._counter += 1
        path = f"{user_id}/file{self._counter}{extension}"
        self.files[path] = data
        return path

    def delete(self, path: str) -> None:
        self.files.pop(path, None)

    def public_path(self, path: str) -> str:
        return f"/media/{path}"
