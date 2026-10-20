"""SQLAlchemy-реализации репозиториев. Принимают и отдают сущности домена, строки таблиц наружу не выходят."""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.domain.catalog import Product
from app.domain.entities import AuthSession, ClickEvent, Favorite, Location, OtpCode, User, WardrobeItem
from app.infrastructure.db.models import (
    AuthSessionRow,
    ClickEventRow,
    FavoriteRow,
    OtpCodeRow,
    ProductRow,
    UserRow,
    WardrobeItemRow,
)


class SqlUserRepository:
    def __init__(self, db: Session):
        self._db = db

    def add(self, user: User) -> None:
        row = UserRow(id=user.id, created_at=user.created_at)
        self._write(row, user)
        self._db.add(row)
        self._db.flush()

    def get(self, user_id: str) -> User | None:
        return self._entity(self._db.get(UserRow, user_id))

    def get_by_phone(self, phone: str) -> User | None:
        return self._entity(self._db.scalar(select(UserRow).where(UserRow.phone == phone)))

    def get_by_email(self, email: str) -> User | None:
        return self._entity(self._db.scalar(select(UserRow).where(UserRow.email == email)))

    def save(self, user: User) -> None:
        row = self._db.get(UserRow, user.id)
        if row is None:
            raise LookupError(f"Нет пользователя {user.id}")
        self._write(row, user)
        self._db.flush()

    @staticmethod
    def _write(row: UserRow, user: User) -> None:
        row.phone, row.email = user.phone, user.email
        row.name, row.birth_year = user.name, user.birth_year
        row.onboarded, row.department = user.onboarded, user.department
        row.styles, row.budget = list(user.styles), user.budget
        location = user.location
        row.city = location.city if location else None
        row.country_code = location.country_code if location else None
        row.lat = location.lat if location else None
        row.lon = location.lon if location else None
        row.timezone = location.timezone if location else None

    @staticmethod
    def _entity(row: UserRow | None) -> User | None:
        if row is None:
            return None
        has_location = row.city and row.country_code and row.lat is not None and row.lon is not None
        return User(
            id=row.id,
            created_at=row.created_at,
            phone=row.phone,
            email=row.email,
            name=row.name,
            birth_year=row.birth_year,
            onboarded=row.onboarded,
            department=row.department,
            styles=list(row.styles),
            budget=row.budget,
            location=Location(row.city, row.country_code, row.lat, row.lon, row.timezone)  # type: ignore[arg-type]
            if has_location
            else None,
        )


class SqlSessionRepository:
    def __init__(self, db: Session):
        self._db = db

    def add(self, session: AuthSession) -> None:
        self._db.add(
            AuthSessionRow(
                token_hash=session.token_hash,
                user_id=session.user_id,
                created_at=session.created_at,
                expires_at=session.expires_at,
                last_used_at=session.last_used_at,
            )
        )
        self._db.flush()

    def get(self, token_hash: str) -> AuthSession | None:
        row = self._db.get(AuthSessionRow, token_hash)
        if row is None:
            return None
        return AuthSession(row.token_hash, row.user_id, row.created_at, row.expires_at, row.last_used_at)

    def save(self, session: AuthSession) -> None:
        row = self._db.get(AuthSessionRow, session.token_hash)
        if row is None:
            raise LookupError("Нет такой сессии")
        row.expires_at, row.last_used_at = session.expires_at, session.last_used_at
        self._db.flush()

    def delete(self, token_hash: str) -> None:
        self._db.execute(delete(AuthSessionRow).where(AuthSessionRow.token_hash == token_hash))


class SqlOtpRepository:
    def __init__(self, db: Session):
        self._db = db

    def add(self, code: OtpCode) -> None:
        row = OtpCodeRow(
            identifier=code.identifier,
            kind=code.kind,
            code_hash=code.code_hash,
            created_at=code.created_at,
            expires_at=code.expires_at,
            attempts=code.attempts,
            consumed=code.consumed,
        )
        self._db.add(row)
        self._db.flush()
        code.id = row.id

    def recent(self, identifier: str, since: datetime) -> list[OtpCode]:
        rows = self._db.scalars(
            select(OtpCodeRow)
            .where(OtpCodeRow.identifier == identifier, OtpCodeRow.created_at > since)
            .order_by(OtpCodeRow.created_at.desc(), OtpCodeRow.id.desc())
        )
        return [self._entity(row) for row in rows]

    def latest_active(self, identifier: str) -> OtpCode | None:
        row = self._db.scalar(
            select(OtpCodeRow)
            .where(OtpCodeRow.identifier == identifier, OtpCodeRow.consumed.is_(False))
            .order_by(OtpCodeRow.created_at.desc(), OtpCodeRow.id.desc())
            .limit(1)
        )
        return self._entity(row) if row else None

    def save(self, code: OtpCode) -> None:
        row = self._db.get(OtpCodeRow, code.id)
        if row is None:
            raise LookupError("Нет такого кода")
        row.attempts, row.consumed, row.expires_at = code.attempts, code.consumed, code.expires_at
        self._db.flush()

    @staticmethod
    def _entity(row: OtpCodeRow) -> OtpCode:
        return OtpCode(
            id=row.id,
            identifier=row.identifier,
            kind=row.kind,
            code_hash=row.code_hash,
            created_at=row.created_at,
            expires_at=row.expires_at,
            attempts=row.attempts,
            consumed=row.consumed,
        )


class SqlProductRepository:
    def __init__(self, db: Session):
        self._db = db

    def count(self) -> int:
        return self._db.scalar(select(func.count()).select_from(ProductRow)) or 0

    def add_many(self, products: Sequence[Product]) -> None:
        self._db.add_all(
            ProductRow(
                id=p.id,
                title=p.title,
                brand=p.brand,
                price=p.price,
                category=p.category,
                color=p.color,
                styles=list(p.styles),
                department=p.department,
                warmth=p.warmth,
                weatherproof=p.weatherproof,
                image_url=p.image_url,
                url=p.url,
            )
            for p in products
        )
        self._db.flush()

    def list_all(self) -> list[Product]:
        rows = self._db.scalars(select(ProductRow).order_by(ProductRow.id))
        return [
            Product(
                id=r.id,
                title=r.title,
                brand=r.brand,
                price=r.price,
                category=r.category,
                color=r.color,
                styles=tuple(r.styles),
                department=r.department,
                url=r.url,
                image_url=r.image_url,
                warmth=r.warmth,
                weatherproof=r.weatherproof,
            )
            for r in rows
        ]


class SqlWardrobeRepository:
    def __init__(self, db: Session):
        self._db = db

    def add(self, item: WardrobeItem) -> None:
        self._db.add(
            WardrobeItemRow(
                id=item.id,
                user_id=item.user_id,
                category=item.category,
                color=item.color,
                title=item.title,
                image_path=item.image_path,
                created_at=item.created_at,
            )
        )
        self._db.flush()

    def get(self, item_id: str) -> WardrobeItem | None:
        row = self._db.get(WardrobeItemRow, item_id)
        return self._entity(row) if row else None

    def list_for_user(self, user_id: str) -> list[WardrobeItem]:
        rows = self._db.scalars(
            select(WardrobeItemRow)
            .where(WardrobeItemRow.user_id == user_id)
            .order_by(WardrobeItemRow.created_at.desc(), WardrobeItemRow.id)
        )
        return [self._entity(row) for row in rows]

    def delete(self, item_id: str) -> None:
        self._db.execute(delete(WardrobeItemRow).where(WardrobeItemRow.id == item_id))

    @staticmethod
    def _entity(row: WardrobeItemRow) -> WardrobeItem:
        return WardrobeItem(
            id=row.id,
            user_id=row.user_id,
            category=row.category,
            color=row.color,
            title=row.title,
            image_path=row.image_path,
            created_at=row.created_at,
        )


class SqlFavoriteRepository:
    def __init__(self, db: Session):
        self._db = db

    def add(self, favorite: Favorite) -> None:
        self._db.add(
            FavoriteRow(
                user_id=favorite.user_id, outfit_id=favorite.outfit_id, created_at=favorite.created_at
            )
        )
        self._db.flush()

    def exists(self, user_id: str, outfit_id: str) -> bool:
        return self._db.get(FavoriteRow, (user_id, outfit_id)) is not None

    def remove(self, user_id: str, outfit_id: str) -> None:
        self._db.execute(
            delete(FavoriteRow).where(FavoriteRow.user_id == user_id, FavoriteRow.outfit_id == outfit_id)
        )

    def ids_for_user(self, user_id: str) -> list[str]:
        return list(
            self._db.scalars(
                select(FavoriteRow.outfit_id)
                .where(FavoriteRow.user_id == user_id)
                .order_by(FavoriteRow.created_at.desc(), FavoriteRow.outfit_id)
            )
        )


class SqlClickRepository:
    def __init__(self, db: Session):
        self._db = db

    def add(self, event: ClickEvent) -> None:
        row = ClickEventRow(
            user_id=event.user_id,
            product_id=event.product_id,
            outfit_id=event.outfit_id,
            source=event.source,
            created_at=event.created_at,
        )
        self._db.add(row)
        self._db.flush()
        event.id = row.id

    def list_all(self) -> list[ClickEvent]:
        rows = self._db.scalars(select(ClickEventRow).order_by(ClickEventRow.id))
        return [
            ClickEvent(
                id=r.id,
                product_id=r.product_id,
                user_id=r.user_id,
                outfit_id=r.outfit_id,
                source=r.source,
                created_at=r.created_at,
            )
            for r in rows
        ]
