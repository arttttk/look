import pytest

from tests.api.conftest import KAZAN, TOKYO, login, onboard, upload


def feed(client, headers, **params):
    return client.get("/feed", headers=headers, params=params)


class TestFeedPaging:
    def test_a_page_has_items_and_a_cursor(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        page = feed(client, user).json()

        # Assert
        assert len(page["items"]) == 3 and page["next_cursor"] == 3

    def test_walking_the_pages_gives_the_whole_feed_once(self, client, user):
        # Arrange
        seen, cursor = [], 0

        # Act
        while cursor is not None:
            page = feed(client, user, cursor=cursor, limit=20).json()
            seen += [o["id"] for o in page["items"]]
            cursor = page["next_cursor"]

        # Assert
        assert len(seen) == 80 and len(set(seen)) == 80

    @pytest.mark.parametrize(
        "params", [{"limit": 0}, {"limit": 21}, {"limit": -1}, {"cursor": -1}, {"limit": "x"}]
    )
    def test_bad_paging_parameters_get_422(self, client, user, params):
        # Arrange: фикстуры (client, user) и параметры теста (params)
        # Act
        response = feed(client, user, **params)

        # Assert
        assert response.status_code == 422

    def test_outfits_have_the_shape_the_app_needs(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        outfit = feed(client, user).json()["items"][0]

        # Assert
        assert set(outfit) == {"id", "title", "styles", "pieces", "score"}
        piece = outfit["pieces"][0]
        assert piece["origin"] == "catalog" and piece["product"]["price"] > 0


class TestPersonalisation:
    def test_the_feed_follows_the_profile(self, client, user):
        # Arrange
        onboard(client, user, department="women", styles=["sport"])

        # Act
        items = feed(client, user, limit=20).json()["items"]

        # Assert
        assert "sport" in items[0]["styles"]
        assert all(p["product"]["department"] != "men" for o in items for p in o["pieces"])

    def test_cold_weather_changes_what_comes_first(self, client, sender, weather):
        # Arrange
        weather.temperature_c = 30.0
        hot_user = login(client, sender)
        onboard(client, hot_user, location=KAZAN)
        hot_first = feed(client, hot_user, limit=1).json()["items"][0]["id"]

        # Act
        # (тот же человек, но на улице мороз; город другой, чтобы не попасть в кэш погоды)
        weather.temperature_c = -15.0
        onboard(client, hot_user, location={**KAZAN, "city": "Якутск", "lat": 62.0, "lon": 129.7})
        cold_first = feed(client, hot_user, limit=1).json()["items"][0]["id"]

        # Assert
        assert hot_first != cold_first

    def test_a_weather_outage_does_not_break_the_feed(self, client, user, weather):
        # Arrange
        weather.fail = True
        onboard(client, user, location=KAZAN)

        # Act
        response = feed(client, user)

        # Assert
        assert response.status_code == 200 and len(response.json()["items"]) == 3

    def test_an_undecided_user_gets_the_regional_styles(self, client, user):
        # Arrange
        onboard(client, user, location=TOKYO)

        # Act
        items = feed(client, user, limit=6).json()["items"]

        # Assert
        assert all({"minimal", "street"} & set(o["styles"]) for o in items)

    def test_the_budget_keeps_prices_down(self, client, sender):
        # Arrange
        def total(outfit):
            return sum(p["product"]["price"] for p in outfit["pieces"])

        mid, high = login(client, sender), login(client, sender)
        onboard(client, mid, budget="mid")
        onboard(client, high, budget="high")

        # Act
        mid_items = feed(client, mid, limit=20).json()["items"]
        high_items = feed(client, high, limit=20).json()["items"]

        # Assert
        assert max(map(total, mid_items)) <= 30000 < max(map(total, high_items))


class TestHomeBlocks:
    def test_the_outfit_of_the_day_has_four_outfits_and_is_the_top_of_the_feed(self, client, user):
        # Arrange
        top = [o["id"] for o in feed(client, user, limit=4).json()["items"]]

        # Act
        daily = client.get("/feed/daily", headers=user).json()

        # Assert
        assert [o["id"] for o in daily] == top

    def test_occasions_are_tagged_and_distinct(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        occasions = client.get("/feed/occasions", headers=user).json()

        # Assert
        assert len(occasions) >= 4 and "Работа" in {o["tag"] for o in occasions}
        assert len({o["outfit"]["id"] for o in occasions}) == len(occasions)

    @pytest.mark.parametrize("path", ["/feed/daily", "/feed/occasions"])
    def test_home_blocks_need_a_token(self, client, path):
        # Arrange: фикстуры (client) и параметры теста (path)
        # Act
        response = client.get(path)

        # Assert
        assert response.status_code == 401


class TestOutfitById:
    def test_an_outfit_opens_by_its_id(self, client, user):
        # Arrange
        outfit = feed(client, user).json()["items"][0]

        # Act
        response = client.get(f"/outfits/{outfit['id']}", headers=user)

        # Assert
        assert response.status_code == 200 and response.json()["id"] == outfit["id"]

    def test_an_unknown_outfit_gets_404(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        response = client.get("/outfits/c.no-such-product", headers=user)

        # Assert
        assert response.status_code == 404

    def test_an_outfit_with_the_users_item_gets_an_absolute_photo_url(self, client, user):
        # Arrange
        item = upload(client, user, category="top").json()

        # Act
        outfit = client.get(f"/outfits/w.{item['id']}~c.chinos~c.sneakers-white", headers=user).json()

        # Assert
        own = next(p for p in outfit["pieces"] if p["origin"] == "wardrobe")
        assert own["image_url"].startswith("http://testserver/media/") and own["product"] is None

    def test_someone_elses_item_cannot_be_opened(self, client, sender):
        # Arrange
        owner, stranger = login(client, sender), login(client, sender)
        item = upload(client, owner).json()

        # Act
        response = client.get(f"/outfits/w.{item['id']}~c.chinos~c.sneakers-white", headers=stranger)

        # Assert
        assert response.status_code == 404
