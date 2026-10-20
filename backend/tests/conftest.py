import pytest

from app.application.catalog_store import CatalogStore
from app.application.personalisation import PersonalisationService
from app.application.policies import AuthPolicy, WardrobePolicy
from app.domain.catalog import Catalog, seed_product_data
from app.infrastructure.security import HmacSecurity
from tests.fakes import (
    FakeGeocoder,
    FakeSender,
    FakeStorage,
    FakeUnitOfWork,
    FakeWeatherProvider,
    FrozenClock,
    InMemoryDatabase,
)

SECRET = "test-secret-test-secret-test-secret-0123"

# Общий каталог: он неизменяем, строить его в каждом тесте незачем.
CATALOG = Catalog(seed_product_data())


@pytest.fixture()
def clock() -> FrozenClock:
    return FrozenClock()


@pytest.fixture()
def database() -> InMemoryDatabase:
    return InMemoryDatabase()


@pytest.fixture()
def uow(database) -> FakeUnitOfWork:
    return FakeUnitOfWork(database)


@pytest.fixture()
def sender() -> FakeSender:
    return FakeSender()


@pytest.fixture()
def geocoder() -> FakeGeocoder:
    return FakeGeocoder()


@pytest.fixture()
def weather() -> FakeWeatherProvider:
    return FakeWeatherProvider()


@pytest.fixture()
def storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture()
def security() -> HmacSecurity:
    return HmacSecurity(SECRET)


@pytest.fixture()
def auth_policy() -> AuthPolicy:
    return AuthPolicy()


@pytest.fixture()
def wardrobe_policy() -> WardrobePolicy:
    return WardrobePolicy(max_upload_bytes=1024)


@pytest.fixture()
def catalog_store() -> CatalogStore:
    return CatalogStore(CATALOG)


@pytest.fixture()
def personalisation(weather) -> PersonalisationService:
    return PersonalisationService(weather)
