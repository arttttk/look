from datetime import timedelta

import pytest

from app.application.errors import Unauthorized
from app.application.policies import AuthPolicy
from app.application.use_cases.auth import AuthenticateToken, Logout, RequestLoginCode, VerifyLoginCode

PHONE = "+79991234567"


@pytest.fixture()
def sign_in(uow, sender, clock, security):
    """Входит по телефону и возвращает результат — готовая сессия для тестов проверки токена."""

    def run(phone: str = PHONE):
        policy = AuthPolicy()
        RequestLoginCode(uow, sender, clock, security, policy).execute(phone)
        code = sender.last_code(phone)
        return VerifyLoginCode(uow, clock, security, policy).execute(phone, code)

    return run


@pytest.fixture()
def authenticate(uow, clock, security) -> AuthenticateToken:
    return AuthenticateToken(uow, clock, security)


class TestAuthenticateToken:
    def test_a_valid_token_gives_the_user_and_the_session(self, authenticate, sign_in):
        # Arrange
        signed_in = sign_in()

        # Act
        result = authenticate.execute(signed_in.token)

        # Assert
        assert result.user.id == signed_in.user.id
        assert result.session.user_id == signed_in.user.id

    @pytest.mark.parametrize("token", ["", "garbage", "lk_" + "x" * 43])
    def test_an_unknown_token_is_refused(self, authenticate, token):
        # Arrange: токен никому не выдавали

        # Act / Assert
        with pytest.raises(Unauthorized):
            authenticate.execute(token)

    def test_an_expired_session_is_refused(self, authenticate, sign_in, clock):
        # Arrange
        signed_in = sign_in()
        clock.advance(days=90)

        # Act / Assert
        with pytest.raises(Unauthorized):
            authenticate.execute(signed_in.token)

    def test_a_session_is_still_valid_a_second_before_it_expires(self, authenticate, sign_in, clock):
        # Arrange
        signed_in = sign_in()
        clock.advance(days=89, hours=23, minutes=59)

        # Act
        result = authenticate.execute(signed_in.token)

        # Assert
        assert result.user.id == signed_in.user.id

    def test_a_session_of_a_missing_user_is_refused(self, authenticate, sign_in, database):
        # Arrange
        signed_in = sign_in()
        del database.tables.users[signed_in.user.id]

        # Act / Assert
        with pytest.raises(Unauthorized):
            authenticate.execute(signed_in.token)

    def test_last_use_is_refreshed_after_an_hour(self, authenticate, sign_in, database, clock, security):
        # Arrange
        signed_in = sign_in()
        started = clock.now()
        clock.advance(hours=2)

        # Act
        authenticate.execute(signed_in.token)

        # Assert
        stored = database.tables.sessions[security.hash_token(signed_in.token)]
        assert stored.last_used_at == started + timedelta(hours=2)

    def test_last_use_is_not_rewritten_on_every_request(
        self, authenticate, sign_in, database, clock, security
    ):
        # Arrange
        signed_in = sign_in()
        started = clock.now()
        clock.advance(minutes=30)

        # Act
        authenticate.execute(signed_in.token)

        # Assert
        assert database.tables.sessions[security.hash_token(signed_in.token)].last_used_at == started


class TestLogout:
    def test_the_token_stops_working(self, uow, authenticate, sign_in):
        # Arrange
        signed_in = sign_in()
        session = authenticate.execute(signed_in.token).session

        # Act
        Logout(uow).execute(session)

        # Assert
        with pytest.raises(Unauthorized):
            authenticate.execute(signed_in.token)

    def test_other_sessions_of_the_same_user_survive(self, uow, authenticate, sign_in, clock):
        # Arrange
        first = sign_in()
        clock.advance(minutes=2)
        second = sign_in()
        session = authenticate.execute(first.token).session

        # Act
        Logout(uow).execute(session)

        # Assert
        assert authenticate.execute(second.token).user.id == first.user.id

    def test_sessions_of_other_users_survive(self, uow, authenticate, sign_in):
        # Arrange
        alice, bob = sign_in("+79990000001"), sign_in("+79990000002")
        session = authenticate.execute(alice.token).session

        # Act
        Logout(uow).execute(session)

        # Assert
        assert authenticate.execute(bob.token).user.id == bob.user.id

    def test_logging_out_twice_is_harmless(self, uow, authenticate, sign_in):
        # Arrange
        signed_in = sign_in()
        session = authenticate.execute(signed_in.token).session
        Logout(uow).execute(session)

        # Act
        Logout(uow).execute(session)

        # Assert
        with pytest.raises(Unauthorized):
            authenticate.execute(signed_in.token)

    def test_the_user_is_not_deleted_by_logging_out(self, uow, authenticate, sign_in, database):
        # Arrange
        signed_in = sign_in()
        session = authenticate.execute(signed_in.token).session

        # Act
        Logout(uow).execute(session)

        # Assert
        assert signed_in.user.id in database.tables.users
