from datetime import timedelta

from app.domain.entities import AuthSession, OtpCode, User
from tests.factories import NOW


class TestUserRegistration:
    def test_phone_registration_fills_only_the_phone(self):
        # Arrange: подготовка не требуется
        # Act
        user = User.register("phone", "+79991234567", NOW)

        # Assert
        assert (user.phone, user.email) == ("+79991234567", None)
        assert user.onboarded is False and user.styles == [] and user.department == "any"

    def test_email_registration_fills_only_the_email(self):
        # Arrange: подготовка не требуется
        # Act
        user = User.register("email", "a@example.com", NOW)

        # Assert
        assert (user.phone, user.email) == (None, "a@example.com")

    def test_every_registration_gets_a_fresh_id(self):
        # Arrange
        first = User.register("phone", "+79991234567", NOW)
        # Act
        second = User.register("phone", "+79991234568", NOW)

        # Assert
        assert first.id != second.id and len(first.id) == 32


class TestAuthSession:
    @staticmethod
    def make() -> AuthSession:
        return AuthSession(
            token_hash="hash",
            user_id="user1",
            created_at=NOW,
            expires_at=NOW + timedelta(days=90),
            last_used_at=NOW,
        )

    def test_not_expired_before_the_deadline(self):
        # Arrange
        session = self.make()

        # Act
        expired = session.is_expired(NOW + timedelta(days=89))

        # Assert
        assert expired is False

    def test_expired_exactly_at_the_deadline(self):
        # Arrange
        session = self.make()

        # Act
        expired = session.is_expired(NOW + timedelta(days=90))

        # Assert
        assert expired is True

    def test_last_use_is_refreshed_at_most_once_an_hour(self):
        # Arrange
        session = self.make()

        # Act
        soon = session.needs_touch(NOW + timedelta(minutes=59))
        later = session.needs_touch(NOW + timedelta(hours=1, seconds=1))

        # Assert
        assert (soon, later) == (False, True)


class TestOtpCode:
    def test_code_expires_at_its_deadline(self):
        # Arrange
        code = OtpCode("+79991234567", "phone", "hash", NOW, NOW + timedelta(minutes=5))

        # Act
        before = code.is_expired(NOW + timedelta(minutes=4, seconds=59))
        at = code.is_expired(NOW + timedelta(minutes=5))

        # Assert
        assert (before, at) == (False, True)
