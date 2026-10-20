"""Помощники для тестов use case'ов: положить данные в «базу» и прочитать их обратно."""

from tests.fakes import FakeUnitOfWork, InMemoryDatabase


def persist(database: InMemoryDatabase, *entities) -> None:
    """Сохраняет сущности как отдельная завершённая транзакция — готовое состояние для теста."""
    with FakeUnitOfWork(database) as uow:
        for entity in entities:
            kind = type(entity).__name__
            if kind == "User":
                uow.users.add(entity)
            elif kind == "WardrobeItem":
                uow.wardrobe.add(entity)
            elif kind == "AuthSession":
                uow.sessions.add(entity)
            elif kind == "Favorite":
                uow.favorites.add(entity)
            else:
                raise TypeError(f"persist не умеет сохранять {kind}")
        uow.commit()
