from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET = "dev-only-secret-change-me-before-deploy-0123456789"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: Literal["dev", "production"] = "dev"
    database_url: str = "sqlite:///./look.db"
    media_dir: Path = Path("./media")
    max_upload_bytes: int = 8 * 1024 * 1024
    cors_origins: list[str] = ["*"]

    # Ключ для хэшей одноразовых кодов. В проде обязательно заменить: openssl rand -hex 32
    secret_key: str = DEV_SECRET

    # Вход по одноразовому коду
    session_days: int = 90
    code_ttl_seconds: int = 300
    code_resend_seconds: int = 60
    code_max_per_hour: int = 5
    code_max_attempts: int = 5
    default_phone_region: str = "RU"  # как трактуется номер без «+»
    # Только для разработки: вернуть код в ответе API, чтобы не искать его в логах.
    dev_return_code: bool = False

    # Внешние сервисы (Open-Meteo: бесплатно, без ключа)
    geocoding_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_ttl_seconds: int = 900
    http_timeout_seconds: float = 4.0
