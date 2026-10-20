"""Композиция: какие реализации подставлены под порты. Единственное место, где use case'ы
встречаются с инфраструктурой. Каждый запрос получает свежие use case'ы со своей транзакцией."""

from collections.abc import Callable
from dataclasses import dataclass

from app.application.catalog_store import CatalogStore
from app.application.personalisation import PersonalisationService
from app.application.policies import AuthPolicy, WardrobePolicy
from app.application.ports import (
    Clock,
    CodeSender,
    FileStorage,
    Geocoder,
    Security,
    UnitOfWork,
    WeatherProvider,
)
from app.application.use_cases import auth, catalog, favorites, feed, geo, profile, wardrobe
from app.config import Settings


@dataclass
class Container:
    settings: Settings
    uow_factory: Callable[[], UnitOfWork]
    clock: Clock
    security: Security
    sender: CodeSender
    geocoder: Geocoder
    weather: WeatherProvider
    storage: FileStorage
    catalog_store: CatalogStore
    auth_policy: AuthPolicy
    wardrobe_policy: WardrobePolicy

    @property
    def personalisation(self) -> PersonalisationService:
        return PersonalisationService(self.weather)


class UseCases:
    def __init__(self, c: Container):
        self._c = c

    # --- вход
    def request_login_code(self) -> auth.RequestLoginCode:
        c = self._c
        return auth.RequestLoginCode(c.uow_factory(), c.sender, c.clock, c.security, c.auth_policy)

    def verify_login_code(self) -> auth.VerifyLoginCode:
        c = self._c
        return auth.VerifyLoginCode(c.uow_factory(), c.clock, c.security, c.auth_policy)

    def authenticate(self) -> auth.AuthenticateToken:
        c = self._c
        return auth.AuthenticateToken(c.uow_factory(), c.clock, c.security)

    def logout(self) -> auth.Logout:
        return auth.Logout(self._c.uow_factory())

    # --- профиль, город, погода
    def update_profile(self) -> profile.UpdateProfile:
        return profile.UpdateProfile(self._c.uow_factory(), self._c.clock)

    def search_cities(self) -> geo.SearchCities:
        return geo.SearchCities(self._c.geocoder)

    def get_current_weather(self) -> geo.GetCurrentWeather:
        return geo.GetCurrentWeather(self._c.weather)

    # --- каталог и лента
    def list_products(self) -> catalog.ListProducts:
        return catalog.ListProducts(self._c.catalog_store)

    def get_product(self) -> catalog.GetProduct:
        return catalog.GetProduct(self._c.catalog_store)

    def track_product_click(self) -> catalog.TrackProductClick:
        c = self._c
        return catalog.TrackProductClick(c.uow_factory(), c.catalog_store, c.clock)

    def get_feed(self) -> feed.GetFeed:
        return feed.GetFeed(self._c.catalog_store, self._c.personalisation)

    def get_daily_outfits(self) -> feed.GetDailyOutfits:
        return feed.GetDailyOutfits(self._c.catalog_store, self._c.personalisation)

    def get_occasion_outfits(self) -> feed.GetOccasionOutfits:
        return feed.GetOccasionOutfits(self._c.catalog_store, self._c.personalisation)

    def get_outfit(self) -> feed.GetOutfit:
        c = self._c
        return feed.GetOutfit(c.uow_factory(), c.catalog_store, c.storage)

    # --- гардероб
    def list_wardrobe_items(self) -> wardrobe.ListWardrobeItems:
        return wardrobe.ListWardrobeItems(self._c.uow_factory())

    def add_wardrobe_item(self) -> wardrobe.AddWardrobeItem:
        c = self._c
        return wardrobe.AddWardrobeItem(c.uow_factory(), c.storage, c.clock, c.wardrobe_policy)

    def delete_wardrobe_item(self) -> wardrobe.DeleteWardrobeItem:
        return wardrobe.DeleteWardrobeItem(self._c.uow_factory(), self._c.storage)

    def get_looks(self) -> wardrobe.GetLooks:
        c = self._c
        return wardrobe.GetLooks(c.uow_factory(), c.catalog_store, c.personalisation, c.storage)

    # --- избранное
    def list_favorite_ids(self) -> favorites.ListFavoriteIds:
        return favorites.ListFavoriteIds(self._c.uow_factory())

    def list_favorite_outfits(self) -> favorites.ListFavoriteOutfits:
        c = self._c
        return favorites.ListFavoriteOutfits(c.uow_factory(), c.catalog_store, c.storage)

    def add_favorite(self) -> favorites.AddFavorite:
        c = self._c
        return favorites.AddFavorite(c.uow_factory(), c.catalog_store, c.storage, c.clock)

    def remove_favorite(self) -> favorites.RemoveFavorite:
        return favorites.RemoveFavorite(self._c.uow_factory())
