import pytest

from app.infrastructure.storage import LocalFileStorage


@pytest.fixture()
def storage(tmp_path) -> LocalFileStorage:
    return LocalFileStorage(tmp_path / "media")


def test_the_root_directory_is_created(tmp_path):
    # Arrange
    root = tmp_path / "deep" / "media"

    # Act
    LocalFileStorage(root)

    # Assert
    assert root.is_dir()


def test_a_saved_file_lands_under_the_users_folder(storage):
    # Arrange: состояние задают фикстуры (storage)
    # Act
    path = storage.save("user1", b"data", ".png")

    # Assert
    assert path.startswith("user1/") and path.endswith(".png")
    assert (storage.root / path).read_bytes() == b"data"


def test_every_save_gets_a_new_name(storage):
    # Arrange
    first = storage.save("user1", b"a", ".png")
    # Act
    second = storage.save("user1", b"a", ".png")

    # Assert
    assert first != second


def test_the_public_path_is_relative_to_the_site_root(storage):
    # Arrange: состояние задают фикстуры (storage)
    # Act
    url = storage.public_path("user1/photo.png")

    # Assert
    assert url == "/media/user1/photo.png"


def test_delete_removes_the_file(storage):
    # Arrange
    path = storage.save("user1", b"data", ".png")

    # Act
    storage.delete(path)

    # Assert
    assert not (storage.root / path).exists()


def test_deleting_a_missing_file_is_harmless(storage):
    # Arrange: состояние задают фикстуры (storage)
    # Act
    storage.delete("user1/never-existed.png")

    # Assert
    assert list(storage.root.iterdir()) == []


@pytest.mark.parametrize("path", ["../outside.txt", "../../etc/passwd", "user1/../../outside.txt"])
def test_a_path_that_escapes_the_storage_is_ignored(tmp_path, storage, path):
    # Arrange
    outside = tmp_path / "outside.txt"
    outside.write_text("keep me")

    # Act
    storage.delete(path)

    # Assert
    assert outside.read_text() == "keep me"


def test_deleting_one_file_keeps_the_others(storage):
    # Arrange
    keep = storage.save("user1", b"keep", ".png")
    drop = storage.save("user1", b"drop", ".png")

    # Act
    storage.delete(drop)

    # Assert
    assert (storage.root / keep).exists() and not (storage.root / drop).exists()
