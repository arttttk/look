from app.api import schemas
from app.application.ports import FileStorage
from app.domain.catalog import Product
from app.domain.entities import User, WardrobeItem
from app.domain.geo import City
from app.domain.outfits import Outfit, Piece
from app.domain.regions import regional_styles
from app.domain.weather import Weather


class Presenter:
    """Превращает объекты домена в ответы API. Единственное место, где в картинки подставляется
    домен сервера: в домене и use case'ах адреса относительные («/media/...»)."""

    def __init__(self, base_url: str, storage: FileStorage):
        self._base = base_url.rstrip("/")
        self._storage = storage

    def url(self, value: str | None) -> str | None:
        if value is None:
            return None
        return f"{self._base}{value}" if value.startswith("/") else value

    def product(self, product: Product) -> schemas.ProductOut:
        return schemas.ProductOut(
            id=product.id,
            title=product.title,
            brand=product.brand,
            price=product.price,
            category=product.category,
            color=product.color,
            styles=list(product.styles),
            department=product.department,
            image_url=self.url(product.image_url),
        )

    def piece(self, piece: Piece) -> schemas.PieceOut:
        return schemas.PieceOut(
            id=piece.id,
            origin=piece.origin,  # type: ignore[arg-type]
            category=piece.category,
            title=piece.title,
            color=piece.color,
            styles=list(piece.styles),
            image_url=self.url(piece.image_url),
            product=self.product(piece.product) if piece.product else None,
        )

    def outfit(self, outfit: Outfit) -> schemas.OutfitOut:
        return schemas.OutfitOut(
            id=outfit.id,
            title=outfit.title,
            styles=list(outfit.styles),
            pieces=[self.piece(p) for p in outfit.pieces],
            score=outfit.score,
        )

    def item(self, item: WardrobeItem) -> schemas.WardrobeItemOut:
        return schemas.WardrobeItemOut(
            id=item.id,
            category=item.category,  # type: ignore[arg-type]
            color=item.color,  # type: ignore[arg-type]
            title=item.title,
            image_url=self.url(self._storage.public_path(item.image_path)) or "",
            created_at=item.created_at,
        )

    def profile(self, user: User) -> schemas.ProfileOut:
        location = user.location
        return schemas.ProfileOut(
            id=user.id,
            phone=user.phone,
            email=user.email,
            name=user.name,
            birth_year=user.birth_year,
            onboarded=user.onboarded,
            department=user.department,  # type: ignore[arg-type]
            styles=user.styles,  # type: ignore[arg-type]
            budget=user.budget,  # type: ignore[arg-type]
            location=schemas.LocationOut(
                city=location.city,
                country_code=location.country_code,
                lat=location.lat,
                lon=location.lon,
                timezone=location.timezone,
            )
            if location
            else None,
            regional_styles=regional_styles(location.country_code if location else None),  # type: ignore[arg-type]
        )

    @staticmethod
    def city(city: City) -> schemas.CityOut:
        return schemas.CityOut(
            city=city.name,
            region=city.region,
            country=city.country,
            country_code=city.country_code,
            lat=city.lat,
            lon=city.lon,
            timezone=city.timezone,
        )

    @staticmethod
    def weather(city: str, weather: Weather) -> schemas.WeatherOut:
        return schemas.WeatherOut(
            city=city,
            temperature_c=weather.temperature_c,
            feels_like_c=weather.feels_like_c,
            condition=weather.condition,  # type: ignore[arg-type]
            label=weather.label,
            is_day=weather.is_day,
            precipitation_mm=weather.precipitation_mm,
            wind_kmh=weather.wind_kmh,
            observed_at=weather.observed_at,
        )
