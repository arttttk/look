from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.container import Container
from app.api.errors import register_error_handlers
from app.api.routers import auth, catalog, favorites, feed, geo, profile, wardrobe
from app.application.catalog_store import CatalogStore
from app.application.policies import AuthPolicy, WardrobePolicy
from app.application.ports import Clock, CodeSender, Geocoder, WeatherProvider
from app.application.use_cases.startup import LoadCatalog, SeedCatalog
from app.config import DEV_SECRET, Settings
from app.infrastructure.clock import SystemClock
from app.infrastructure.db.base import Base, make_engine, make_session_factory
from app.infrastructure.db.uow import SqlAlchemyUnitOfWork
from app.infrastructure.open_meteo import OpenMeteoGeocoder, OpenMeteoWeather
from app.infrastructure.security import HmacSecurity
from app.infrastructure.senders import ConsoleSender
from app.infrastructure.storage import MEDIA_URL_PREFIX, LocalFileStorage
from app.infrastructure.weather_cache import CachedWeatherProvider


def _check_production_settings(settings: Settings, sender: CodeSender) -> None:
    if settings.env != "production":
        return
    if settings.secret_key == DEV_SECRET:
        raise RuntimeError("В проде нужно задать SECRET_KEY (openssl rand -hex 32)")
    if isinstance(sender, ConsoleSender):
        raise RuntimeError("В проде нельзя отправлять коды в лог: подключите SMS/почтового провайдера")
    if settings.dev_return_code:
        raise RuntimeError("DEV_RETURN_CODE нельзя включать в проде")


def create_app(
    settings: Settings | None = None,
    *,
    sender: CodeSender | None = None,
    geocoder: Geocoder | None = None,
    weather_provider: WeatherProvider | None = None,
    clock: Clock | None = None,
) -> FastAPI:
    """Собирает приложение. Всё, что ходит наружу (отправка кодов, геокодер, погода, часы), можно
    подменить — так тесты и локальная разработка не обращаются к реальным сервисам."""
    settings = settings or Settings()
    sender = sender or ConsoleSender()
    _check_production_settings(settings, sender)

    clock = clock or SystemClock()
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)
    storage = LocalFileStorage(settings.media_dir)
    catalog_store = CatalogStore()

    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    geocoder = geocoder or OpenMeteoGeocoder(settings)
    weather = CachedWeatherProvider(
        weather_provider or OpenMeteoWeather(settings), clock, settings.weather_ttl_seconds
    )

    container = Container(
        settings=settings,
        uow_factory=uow_factory,
        clock=clock,
        security=HmacSecurity(settings.secret_key),
        sender=sender,
        geocoder=geocoder,
        weather=weather,
        storage=storage,
        catalog_store=catalog_store,
        auth_policy=AuthPolicy(
            session_days=settings.session_days,
            code_ttl_seconds=settings.code_ttl_seconds,
            code_resend_seconds=settings.code_resend_seconds,
            code_max_per_hour=settings.code_max_per_hour,
            code_max_attempts=settings.code_max_attempts,
            default_phone_region=settings.default_phone_region,
            return_dev_code=settings.dev_return_code,
        ),
        wardrobe_policy=WardrobePolicy(max_upload_bytes=settings.max_upload_bytes),
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        Base.metadata.create_all(engine)
        SeedCatalog(uow_factory()).execute()
        catalog_store.replace(LoadCatalog(uow_factory()).execute())
        yield
        for service in (geocoder, weather):
            close = getattr(service, "close", None)
            if close:
                close()
        engine.dispose()

    app = FastAPI(title="Look API", version="0.3.0", lifespan=lifespan)
    app.state.container = container

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for router in (
        auth.router,
        profile.router,
        geo.router,
        catalog.router,
        feed.router,
        wardrobe.router,
        favorites.router,
    ):
        app.include_router(router)

    app.mount(MEDIA_URL_PREFIX, StaticFiles(directory=storage.root), name="media")
    return app
