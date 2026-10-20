import logging

logger = logging.getLogger("look.auth")


class ConsoleSender:
    """Только для разработки: пишет код в лог сервера. В проде запрещён (см. api/app.py)."""

    def send(self, kind: str, identifier: str, code: str) -> None:
        logger.warning("Код входа для %s: %s", identifier, code)
