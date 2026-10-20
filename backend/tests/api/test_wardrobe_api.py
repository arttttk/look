import pytest

from tests.api.conftest import KAZAN, PNG, login, onboard, upload


class TestUpload:
    def test_an_item_is_created_with_a_photo_url(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        response = upload(client, user, title="  Любимая футболка ")

        # Assert
        item = response.json()
        assert response.status_code == 201
        assert (item["category"], item["color"], item["title"]) == ("top", "white", "Любимая футболка")
        assert item["image_url"].startswith("http://testserver/media/")

    def test_the_photo_is_served_back_unchanged(self, client, user):
        # Arrange
        item = upload(client, user).json()
        path = item["image_url"].removeprefix("http://testserver")

        # Act
        response = client.get(path)

        # Assert
        assert response.status_code == 200 and response.content == PNG

    @pytest.mark.parametrize(
        ("data", "status"),
        [(b"not an image at all", 415), (b"", 415), (PNG + b"\x00" * 2000, 413)],
    )
    def test_bad_files_are_refused(self, client, user, data, status):
        # Arrange: фикстуры (client, user) и параметры теста (data, status)
        # Act
        response = upload(client, user, data=data)

        # Assert
        assert response.status_code == status
        assert client.get("/wardrobe/items", headers=user).json() == []

    @pytest.mark.parametrize("fields", [{"category": "hat"}, {"color": "pink"}, {"title": "я" * 101}])
    def test_bad_details_are_refused(self, client, user, fields):
        # Arrange: фикстуры (client, user) и параметры теста (fields)
        # Act
        response = upload(client, user, **fields)

        # Assert
        assert response.status_code == 422

    def test_missing_details_are_refused(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        response = client.post("/wardrobe/items", headers=user, data={"category": "top", "color": "white"})

        # Assert
        assert response.status_code == 422

    def test_upload_needs_a_token(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        response = client.post(
            "/wardrobe/items",
            files={"photo": ("a.png", PNG, "image/png")},
            data={"category": "top", "color": "white"},
        )

        # Assert
        assert response.status_code == 401


class TestListAndDelete:
    def test_items_are_listed_newest_first(self, client, user, clock):
        # Arrange
        first = upload(client, user).json()
        clock.advance(minutes=1)
        second = upload(client, user, category="bottom", color="gray").json()

        # Act
        items = client.get("/wardrobe/items", headers=user).json()

        # Assert
        assert [i["id"] for i in items] == [second["id"], first["id"]]

    def test_deleting_removes_the_item_and_its_photo(self, client, user):
        # Arrange
        item = upload(client, user).json()
        path = item["image_url"].removeprefix("http://testserver")

        # Act
        response = client.delete(f"/wardrobe/items/{item['id']}", headers=user)

        # Assert
        assert response.status_code == 204
        assert client.get("/wardrobe/items", headers=user).json() == []
        assert client.get(path).status_code == 404

    def test_deleting_a_missing_item_gets_404(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        response = client.delete("/wardrobe/items/nope", headers=user)

        # Assert
        assert response.status_code == 404

    def test_a_wardrobe_is_private(self, client, sender):
        # Arrange
        alice, bob = login(client, sender), login(client, sender)
        item = upload(client, alice).json()

        # Act
        bobs_list = client.get("/wardrobe/items", headers=bob).json()
        bobs_delete = client.delete(f"/wardrobe/items/{item['id']}", headers=bob)

        # Assert
        assert bobs_list == [] and bobs_delete.status_code == 404
        assert len(client.get("/wardrobe/items", headers=alice).json()) == 1


class TestLooks:
    def test_an_empty_wardrobe_has_no_looks(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        looks = client.get("/looks", headers=user).json()

        # Assert
        assert looks == {"outfits": [], "missing": []}

    def test_looks_use_the_item_and_suggest_what_is_missing(self, client, user):
        # Arrange
        item = upload(client, user, category="top", color="white").json()

        # Act
        looks = client.get("/looks", headers=user).json()

        # Assert
        assert looks["outfits"]
        assert all(f"w.{item['id']}" in o["id"].split("~") for o in looks["outfits"])
        assert [m["category"] for m in looks["missing"]] == ["bottom", "shoes"]
        assert all(m["products"] for m in looks["missing"])

    def test_a_full_set_misses_nothing(self, client, user):
        # Arrange
        for category, color in (("top", "white"), ("bottom", "gray"), ("shoes", "black")):
            upload(client, user, category=category, color=color)

        # Act
        looks = client.get("/looks", headers=user).json()

        # Assert
        assert looks["missing"] == []
        assert all(p["origin"] == "wardrobe" for o in looks["outfits"] for p in o["pieces"])

    def test_the_limit_is_respected(self, client, user):
        # Arrange
        for _ in range(4):
            upload(client, user, category="top")

        # Act
        looks = client.get("/looks", headers=user, params={"limit": 2}).json()

        # Assert
        assert len(looks["outfits"]) == 2

    def test_looks_follow_the_weather(self, client, sender, weather):
        # Arrange
        def best_look(temperature: float, city: dict):
            weather.temperature_c = temperature
            onboard(client, headers, location=city)
            return client.get("/looks", headers=headers).json()["outfits"][0]

        headers = login(client, sender)
        for category, color in (
            ("top", "white"),
            ("bottom", "gray"),
            ("shoes", "black"),
            ("outerwear", "beige"),
        ):
            upload(client, headers, category=category, color=color)

        # Act
        cold = best_look(-8.0, KAZAN)
        hot = best_look(30.0, {**KAZAN, "city": "Сочи", "lat": 43.6, "lon": 39.7})

        # Assert
        assert any(p["category"] == "outerwear" for p in cold["pieces"])
        assert all(p["category"] != "outerwear" for p in hot["pieces"])
