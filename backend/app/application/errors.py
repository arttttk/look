"""Ошибки прикладного слоя. Use case бросает их, не зная про HTTP: в статусы их переводит API."""


class AppError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class Unauthorized(AppError):
    """Нет действующей сессии."""


class NotFound(AppError):
    """Нужного объекта нет (или он чужой — различать для пользователя незачем)."""


class Conflict(AppError):
    """Действие невозможно в текущем состоянии (например, погода без указанного города)."""


class InvalidCode(AppError):
    """Неверный, просроченный или исчерпавший попытки код входа."""


class TooManyRequests(AppError):
    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class DeliveryFailed(AppError):
    """Не удалось отправить код."""


class ProviderUnavailable(AppError):
    """Внешний сервис (погода, геокодер) недоступен или ответил непонятно."""


class PayloadTooLarge(AppError):
    pass


class UnsupportedMedia(AppError):
    pass
