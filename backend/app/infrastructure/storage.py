import uuid
from pathlib import Path

MEDIA_URL_PREFIX = "/media"


class LocalFileStorage:
    """Файлы на диске: media_dir/<пользователь>/<случайное имя>. Позже заменяется на S3 тем же интерфейсом."""

    def __init__(self, root: Path):
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def save(self, user_id: str, data: bytes, extension: str) -> str:
        relative = Path(user_id) / f"{uuid.uuid4().hex}{extension}"
        target = self._root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return relative.as_posix()

    def delete(self, path: str) -> None:
        target = (self._root / path).resolve()
        if self._root.resolve() not in target.parents:
            return  # путь вне хранилища: не трогаем
        target.unlink(missing_ok=True)

    def public_path(self, path: str) -> str:
        return f"{MEDIA_URL_PREFIX}/{path}"
