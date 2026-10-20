from datetime import UTC, datetime

from sqlalchemy import DateTime, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


class UTCDateTime(TypeDecorator):
    """Время всегда в UTC и с часовым поясом. SQLite отдаёт даты без пояса — без этого
    сравнение со «сейчас» (сроки кодов и сессий) падало бы или врало."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Нужен datetime с часовым поясом")
        return value.astimezone(UTC)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def make_engine(url: str) -> Engine:
    # check_same_thread нужен только SQLite: FastAPI гоняет sync-эндпоинты по потокам.
    kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
    if url in ("sqlite://", "sqlite:///:memory:"):
        # База в памяти живёт, пока открыто соединение: нужно одно общее, иначе сессии увидят пустую БД.
        from sqlalchemy.pool import StaticPool

        kwargs["poolclass"] = StaticPool
    return create_engine(url, **kwargs)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
