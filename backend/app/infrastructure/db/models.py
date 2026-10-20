"""Таблицы. Знают только про хранение: правила и поведение — в domain/, преобразование — в repositories.py."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, UTCDateTime


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, default=None)
    email: Mapped[str | None] = mapped_column(String(254), unique=True, default=None)
    name: Mapped[str | None] = mapped_column(String(40), default=None)
    birth_year: Mapped[int | None] = mapped_column(Integer, default=None)
    onboarded: Mapped[bool] = mapped_column(Boolean, default=False)
    department: Mapped[str] = mapped_column(String(8), default="any")
    styles: Mapped[list[str]] = mapped_column(JSON, default=list)
    budget: Mapped[str | None] = mapped_column(String(8), default=None)
    city: Mapped[str | None] = mapped_column(String(80), default=None)
    country_code: Mapped[str | None] = mapped_column(String(2), default=None)
    lat: Mapped[float | None] = mapped_column(Float, default=None)
    lon: Mapped[float | None] = mapped_column(Float, default=None)
    timezone: Mapped[str | None] = mapped_column(String(64), default=None)


class AuthSessionRow(Base):
    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    last_used_at: Mapped[datetime] = mapped_column(UTCDateTime)


class OtpCodeRow(Base):
    __tablename__ = "otp_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    identifier: Mapped[str] = mapped_column(String(254), index=True)
    kind: Mapped[str] = mapped_column(String(8))
    code_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)


class ProductRow(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str] = mapped_column(String(100))
    price: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(16), index=True)
    color: Mapped[str] = mapped_column(String(16))
    styles: Mapped[list[str]] = mapped_column(JSON, default=list)
    department: Mapped[str] = mapped_column(String(8))
    warmth: Mapped[int] = mapped_column(Integer, default=0)
    weatherproof: Mapped[bool] = mapped_column(Boolean, default=True)
    image_url: Mapped[str | None] = mapped_column(String(500), default=None)
    url: Mapped[str] = mapped_column(String(1000))


class WardrobeItemRow(Base):
    __tablename__ = "wardrobe_items"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(16))
    color: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(100), default="")
    image_path: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class FavoriteRow(Base):
    __tablename__ = "favorites"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    outfit_id: Mapped[str] = mapped_column(String(600), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class ClickEventRow(Base):
    __tablename__ = "click_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None, index=True
    )
    product_id: Mapped[str] = mapped_column(String(64), index=True)
    outfit_id: Mapped[str | None] = mapped_column(String(600), default=None)
    source: Mapped[str] = mapped_column(String(32), default="app")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
