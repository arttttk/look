from dataclasses import dataclass


@dataclass(frozen=True)
class AuthPolicy:
    """Правила входа по коду. Значения по умолчанию — боевые."""

    session_days: int = 90
    code_ttl_seconds: int = 300
    code_resend_seconds: int = 60
    code_max_per_hour: int = 5
    code_max_attempts: int = 5
    default_phone_region: str = "RU"  # как трактуется номер без «+»
    return_dev_code: bool = False  # только для разработки: вернуть код в ответе


@dataclass(frozen=True)
class WardrobePolicy:
    max_upload_bytes: int = 8 * 1024 * 1024
