from tests.api.conftest import login, upload

OUTFIT = "c.tee-white~c.chinos~c.sneakers-white"


def test_the_flow_add_list_remove(client, user):
    # Arrange
    outfit_id = client.get("/feed", headers=user).json()["items"][0]["id"]

    # Act
    added = client.put(f"/favorites/{outfit_id}", headers=user)
    ids = client.get("/favorites", headers=user).json()
    outfits = client.get("/favorites/outfits", headers=user).json()
    removed = client.delete(f"/favorites/{outfit_id}", headers=user)

    # Assert
    assert added.status_code == 204 and ids == [outfit_id]
    assert [o["id"] for o in outfits] == [outfit_id]
    assert removed.status_code == 204 and client.get("/favorites", headers=user).json() == []


def test_adding_twice_and_removing_twice_are_harmless(client, user):
    # Arrange
    client.put(f"/favorites/{OUTFIT}", headers=user)

    # Act
    again = client.put(f"/favorites/{OUTFIT}", headers=user)
    ids = client.get("/favorites", headers=user).json()
    client.delete(f"/favorites/{OUTFIT}", headers=user)
    removed_again = client.delete(f"/favorites/{OUTFIT}", headers=user)

    # Assert
    assert again.status_code == 204 and ids == [OUTFIT] and removed_again.status_code == 204


def test_an_outfit_that_does_not_exist_cannot_be_added(client, user):
    # Arrange: состояние задают фикстуры (client, user)
    # Act
    response = client.put("/favorites/c.no-such-product", headers=user)

    # Assert
    assert response.status_code == 404 and client.get("/favorites", headers=user).json() == []


def test_the_last_added_comes_first(client, user, clock):
    # Arrange
    client.put(f"/favorites/{OUTFIT}", headers=user)
    clock.advance(minutes=1)
    other = "c.hoodie~c.jeans-black~c.chunky"
    client.put(f"/favorites/{other}", headers=user)

    # Act
    ids = client.get("/favorites", headers=user).json()

    # Assert
    assert ids == [other, OUTFIT]


def test_favorites_are_private(client, sender):
    # Arrange
    alice, bob = login(client, sender), login(client, sender)
    client.put(f"/favorites/{OUTFIT}", headers=alice)

    # Act
    bobs = client.get("/favorites", headers=bob).json()

    # Assert
    assert bobs == []


def test_an_outfit_loses_its_place_when_one_of_its_items_is_deleted(client, user):
    # Arrange
    item = upload(client, user, category="top").json()
    outfit_id = f"w.{item['id']}~c.chinos~c.sneakers-white"
    client.put(f"/favorites/{outfit_id}", headers=user)
    client.put(f"/favorites/{OUTFIT}", headers=user)

    # Act
    client.delete(f"/wardrobe/items/{item['id']}", headers=user)
    outfits = client.get("/favorites/outfits", headers=user).json()

    # Assert
    assert [o["id"] for o in outfits] == [OUTFIT]


def test_favorites_need_a_token(client):
    # Arrange: состояние задают фикстуры (client)
    # Act
    responses = [
        client.get("/favorites"),
        client.get("/favorites/outfits"),
        client.put(f"/favorites/{OUTFIT}"),
        client.delete(f"/favorites/{OUTFIT}"),
    ]

    # Assert
    assert [r.status_code for r in responses] == [401, 401, 401, 401]
