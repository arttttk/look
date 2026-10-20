import re

from app.infrastructure.security import HmacSecurity


def test_a_code_is_six_digits():
    # Arrange
    security = HmacSecurity("secret-one")

    # Act
    codes = [security.new_code() for _ in range(200)]

    # Assert
    assert all(re.fullmatch(r"\d{6}", code) for code in codes)


def test_codes_are_not_all_the_same():
    # Arrange
    security = HmacSecurity("secret-one")

    # Act
    codes = {security.new_code() for _ in range(50)}

    # Assert
    assert len(codes) > 40


def test_the_right_code_matches_its_hash():
    # Arrange
    security = HmacSecurity("secret-one")
    stored = security.hash_code("+79991234567", "123456")

    # Act
    matches = security.code_matches("+79991234567", "123456", stored)

    # Assert
    assert matches is True


def test_a_wrong_code_does_not_match():
    # Arrange
    security = HmacSecurity("secret-one")
    stored = security.hash_code("+79991234567", "123456")

    # Act
    matches = security.code_matches("+79991234567", "654321", stored)

    # Assert
    assert matches is False


def test_a_code_is_bound_to_the_identifier_it_was_issued_for():
    # Arrange
    security = HmacSecurity("secret-one")
    stored = security.hash_code("+79991234567", "123456")

    # Act
    matches = security.code_matches("+79990000000", "123456", stored)

    # Assert
    assert matches is False


def test_the_hash_depends_on_the_servers_secret():
    # Arrange
    first, second = HmacSecurity("secret-one"), HmacSecurity("secret-two")

    # Act
    a = first.hash_code("+79991234567", "123456")
    b = second.hash_code("+79991234567", "123456")

    # Assert
    assert a != b
    assert second.code_matches("+79991234567", "123456", a) is False


def test_the_code_hash_is_a_sha256_hex_digest():
    # Arrange
    security = HmacSecurity("secret-one")

    # Act
    digest = security.hash_code("x", "123456")

    # Assert
    assert re.fullmatch(r"[0-9a-f]{64}", digest)


def test_tokens_are_long_unique_and_recognisable():
    # Arrange
    security = HmacSecurity("secret-one")

    # Act
    tokens = {security.new_token() for _ in range(100)}

    # Assert
    assert len(tokens) == 100
    assert all(t.startswith("lk_") and len(t) >= 43 for t in tokens)


def test_a_token_hash_is_stable_and_does_not_reveal_the_token():
    # Arrange
    security = HmacSecurity("secret-one")
    token = security.new_token()

    # Act
    first, second = security.hash_token(token), security.hash_token(token)

    # Assert
    assert first == second and token not in first and len(first) == 64


def test_different_tokens_have_different_hashes():
    # Arrange
    security = HmacSecurity("secret-one")

    # Act
    a, b = security.hash_token("lk_a"), security.hash_token("lk_b")

    # Assert
    assert a != b
