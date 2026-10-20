from typing import Self

from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.db.repositories import (
    SqlClickRepository,
    SqlFavoriteRepository,
    SqlOtpRepository,
    SqlProductRepository,
    SqlSessionRepository,
    SqlUserRepository,
    SqlWardrobeRepository,
)


class SqlAlchemyUnitOfWork:
    """Транзакция на одну сессию SQLAlchemy. `with` можно входить повторно: каждый вход — новая
    сессия и новая транзакция, поэтому один объект годится на весь запрос."""

    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory
        self._session: Session | None = None

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        db = self._session
        self.users = SqlUserRepository(db)
        self.sessions = SqlSessionRepository(db)
        self.otp_codes = SqlOtpRepository(db)
        self.products = SqlProductRepository(db)
        self.wardrobe = SqlWardrobeRepository(db)
        self.favorites = SqlFavoriteRepository(db)
        self.clicks = SqlClickRepository(db)
        return self

    def __exit__(self, *exc_info: object) -> None:
        assert self._session is not None
        try:
            self._session.rollback()  # без commit всё откатится; после commit откатывать нечего
        finally:
            self._session.close()
            self._session = None

    def commit(self) -> None:
        assert self._session is not None
        self._session.commit()
