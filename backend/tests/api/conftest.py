import itertools
from contextlib import ExitStack

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.config import Settings
from tests.conftest import SECRET

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
KAZAN = {
    "city": "Казань",
    "country_code": "RU",
    "lat": 55.78874,
    "lon": 49.12214,
    "timezone": "Europe/Moscow",
}
TOKYO = {"city": "Токио", "country_code": "JP", "lat": 35.68, "lon": 139.69, "timezone": "Asia/Tokyo"}

_phones = itertools.count(1)


@pytest.fixture()
def make_client(tmp_path, sender, geocoder, weather, clock):
    """Фабрика приложений с подставными внешними сервисами. Настройки можно переопределить."""
    stack = ExitStack()

    def factory(**overrides) -> TestClient:
        values = {
            "database_url": "sqlite://",
            "media_dir": tmp_path / "media",
            "secret_key": SECRET,
            "max_upload_bytes": 1024,
        } | overrides
        app = create_app(
            Settings(**values), sender=sender, geocoder=geocoder, weather_provider=weather, clock=clock
        )
        return stack.enter_context(TestClient(app))

    with stack:
        yield factory


@pytest.fixture()
def client(make_client) -> TestClient:
    return make_client()


def login(client: TestClient, sender, identifier: str | None = None) -> dict[str, str]:
    """Заголовки авторизации для пользователя, вошедшего по коду (по умолчанию — с новым телефоном)."""
    identifier = identifier or f"+7999000{next(_phones):04d}"
    sent = client.post("/auth/code", json={"identifier": identifier})
    assert sent.status_code == 202, sent.text

    verified = client.post(
        "/auth/verify", json={"identifier": identifier, "code": sender.last_code(sent.json()["identifier"])}
    )
    assert verified.status_code == 200, verified.text
    return {"Authorization": f"Bearer {verified.json()['access_token']}"}


@pytest.fixture()
def user(client, sender) -> dict[str, str]:
    return login(client, sender)


def onboard(client: TestClient, headers: dict[str, str], **profile) -> dict:
    """Заполняет профиль так, как это делает онбординг."""
    body = {"onboarded": True, "department": "any", "styles": []} | profile
    response = client.patch("/me", headers=headers, json=body)
    assert response.status_code == 200, response.text
    return response.json()


def upload(client: TestClient, headers, *, data=PNG, category="top", color="white", title=""):
    return client.post(
        "/wardrobe/items",
        headers=headers,
        files={"photo": ("item.png", data, "image/png")},
        data={"category": category, "color": color, "title": title},
    )
