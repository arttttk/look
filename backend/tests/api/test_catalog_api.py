import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.config import Settings
from app.infrastructure.senders import ConsoleSender


class TestProducts:
    def test_everything_can_be_listed(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        products = client.get("/products", params={"limit": 100}).json()

        # Assert
        assert len(products) == 28

    def test_the_affiliate_url_is_never_exposed(self, client):
        # Arrange
        products = client.get("/products", params={"limit": 100}).json()
        # Act
        one = client.get("/products/boots").json()

        # Assert
        assert all("url" not in p for p in products) and "url" not in one

    def test_filters_combine(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        shoes = client.get(
            "/products", params={"category": "shoes", "department": "men", "style": "classic"}
        ).json()

        # Assert
        assert shoes and all(
            p["category"] == "shoes" and p["department"] != "women" and "classic" in p["styles"]
            for p in shoes
        )

    @pytest.mark.parametrize(
        "params",
        [
            {"category": "hat"},
            {"department": "kids"},
            {"style": "goth"},
            {"limit": 0},
            {"limit": 101},
            {"offset": -1},
        ],
    )
    def test_bad_filters_get_422(self, client, params):
        # Arrange: фикстуры (client) и параметры теста (params)
        # Act
        response = client.get("/products", params=params)

        # Assert
        assert response.status_code == 422

    def test_one_product_is_found_by_id(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        product = client.get("/products/boots").json()

        # Assert
        assert product["title"] == "Ботинки челси" and product["price"] == 12900

    def test_an_unknown_product_gets_404(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        response = client.get("/products/nope")

        # Assert
        assert response.status_code == 404


class TestClicks:
    def test_a_click_returns_the_affiliate_link_and_is_recorded(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        response = client.post(
            "/products/boots/click", headers=user, json={"outfit_id": "c.boots", "source": "feed"}
        )

        # Assert
        assert response.status_code == 200 and response.json() == {
            "url": "https://example.com/shop/boots?ref=look"
        }
        with client.app.state.container.uow_factory() as uow:
            (event,) = uow.clicks.list_all()
        assert (event.product_id, event.source, event.outfit_id) == ("boots", "feed", "c.boots")
        assert event.user_id is not None

    def test_a_click_with_an_empty_body_uses_the_defaults(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        response = client.post("/products/boots/click", headers=user, json={})

        # Assert
        assert response.status_code == 200

    def test_a_click_on_an_unknown_product_gets_404_and_records_nothing(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        response = client.post("/products/nope/click", headers=user, json={})

        # Assert
        assert response.status_code == 404
        with client.app.state.container.uow_factory() as uow:
            assert uow.clicks.list_all() == []

    def test_a_click_needs_a_token(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        response = client.post("/products/boots/click", json={})

        # Assert
        assert response.status_code == 401

    def test_the_public_redirect_sends_the_visitor_to_the_shop_and_records_an_anonymous_click(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        response = client.get("/r/boots", follow_redirects=False)

        # Assert
        assert response.status_code == 302 and response.headers["location"].endswith("boots?ref=look")
        with client.app.state.container.uow_factory() as uow:
            (event,) = uow.clicks.list_all()
        assert (event.user_id, event.source) == (None, "redirect")

    def test_the_public_redirect_for_an_unknown_product_gets_404(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        response = client.get("/r/nope", follow_redirects=False)

        # Assert
        assert response.status_code == 404

    def test_the_redirect_is_hidden_from_the_api_docs(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        paths = client.get("/openapi.json").json()["paths"]

        # Assert
        assert "/r/{product_id}" not in paths and "/products/{product_id}/click" in paths


class TestAppAssembly:
    def test_health(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        response = client.get("/health")

        # Assert
        assert response.json() == {"status": "ok"}

    def test_cors_allows_the_web_build_of_the_app(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        response = client.get("/health", headers={"Origin": "http://localhost:8099"})

        # Assert
        assert response.headers["access-control-allow-origin"] == "*"

    def test_the_catalog_is_seeded_on_the_first_start_only(self, tmp_path, sender, geocoder, weather, clock):
        # Arrange
        settings = Settings(database_url=f"sqlite:///{tmp_path / 'shared.db'}", media_dir=tmp_path / "media")

        # Act
        counts = []
        for _ in range(2):
            app = create_app(
                settings, sender=sender, geocoder=geocoder, weather_provider=weather, clock=clock
            )
            with TestClient(app) as started:
                counts.append(len(started.get("/products", params={"limit": 100}).json()))

        # Assert
        assert counts == [28, 28]

    def test_the_api_documents_every_route_the_app_uses(self, client):
        # Arrange
        expected = {
            "/auth/code", "/auth/verify", "/auth/logout", "/me", "/meta", "/geo/cities", "/weather",
            "/products", "/products/{product_id}", "/products/{product_id}/click",
            "/feed", "/feed/daily", "/feed/occasions", "/outfits/{outfit_id}",
            "/wardrobe/items", "/wardrobe/items/{item_id}", "/looks",
            "/favorites", "/favorites/outfits", "/favorites/{outfit_id}", "/health",
        }  # fmt: skip

        # Act
        paths = set(client.get("/openapi.json").json()["paths"])

        # Assert
        assert expected <= paths


class TestProductionGuards:
    @pytest.mark.parametrize(
        ("overrides", "fragment"),
        [
            ({}, "SECRET_KEY"),
            ({"secret_key": "x" * 40}, "лог"),
            ({"secret_key": "x" * 40, "dev_return_code": True}, "DEV_RETURN_CODE"),
        ],
    )
    def test_production_refuses_unsafe_settings(self, tmp_path, sender, overrides, fragment):
        # Arrange
        settings = Settings(
            env="production",
            database_url=f"sqlite:///{tmp_path / 'p.db'}",
            media_dir=tmp_path / "m",
            **overrides,
        )
        chosen_sender = sender if fragment == "DEV_RETURN_CODE" else ConsoleSender()

        # Act / Assert
        with pytest.raises(RuntimeError, match=fragment):
            create_app(settings, sender=chosen_sender)

    def test_production_starts_with_safe_settings(self, tmp_path, sender, geocoder, weather):
        # Arrange
        settings = Settings(
            env="production",
            secret_key="x" * 40,
            database_url=f"sqlite:///{tmp_path / 'p.db'}",
            media_dir=tmp_path / "m",
        )

        # Act
        app = create_app(settings, sender=sender, geocoder=geocoder, weather_provider=weather)

        # Assert
        assert app.title == "Look API"
