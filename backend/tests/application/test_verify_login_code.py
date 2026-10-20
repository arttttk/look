from datetime import timedelta

import pytest

from app.application.errors import InvalidCode
from app.application.policies import AuthPolicy
from app.application.use_cases.auth import RequestLoginCode, VerifyLoginCode
from app.infrastructure.security import HmacSecurity
from tests.conftest import SECRET

PHONE = "+79991234567"


class ScriptedSecurity(HmacSecurity):
    """Настоящие хэши, но коды выдаются по заранее заданному списку."""

    def __init__(self, codes):
        super().__init__(SECRET)
        self._codes = iter(codes)

    def new_code(self) -> str:
        return next(self._codes)


class Login:
    """Сценарий «запросили код -> ввели код» над общими подделками."""

    def __init__(self, uow, sender, clock, security, policy=None):
        policy = policy or AuthPolicy()
        self.request = RequestLoginCode(uow, sender, clock, security, policy)
        self.verify = VerifyLoginCode(uow, clock, security, policy)
        self.sender = sender

    def issue(self, identifier: str = PHONE) -> str:
        issued = self.request.execute(identifier)
        return self.sender.last_code(issued.identifier)


@pytest.fixture()
def login(uow, sender, clock, security) -> Login:
    return Login(uow, sender, clock, security)


def wrong_code(code: str) -> str:
    return "000000" if code != "000000" else "111111"


def test_the_right_code_registers_a_new_user(login):
    # Arrange
    code = login.issue()

    # Act
    signed_in = login.verify.execute(PHONE, code)

    # Assert
    assert signed_in.is_new is True
    assert signed_in.user.phone == PHONE and signed_in.user.email is None
    assert signed_in.user.onboarded is False and signed_in.token.startswith("lk_")


def test_the_new_user_is_actually_saved(login, database):
    # Arrange
    code = login.issue()

    # Act
    signed_in = login.verify.execute(PHONE, code)

    # Assert
    assert database.tables.users[signed_in.user.id].phone == PHONE


def test_a_known_user_is_logged_in_not_registered_again(login, clock):
    # Arrange
    first = login.verify.execute(PHONE, login.issue())
    clock.advance(minutes=2)

    # Act
    second = login.verify.execute(PHONE, login.issue())

    # Assert
    assert second.is_new is False
    assert second.user.id == first.user.id and second.token != first.token


def test_email_login_registers_by_email(login):
    # Arrange
    code = login.issue("Alice@Example.com")

    # Act
    signed_in = login.verify.execute("alice@example.com", code)

    # Assert
    assert (signed_in.user.email, signed_in.user.phone) == ("alice@example.com", None)


def test_a_different_phone_format_reaches_the_same_code(login):
    # Arrange
    code = login.issue("8 999 123-45-67")

    # Act
    signed_in = login.verify.execute("+7 (999) 123-45-67", code)

    # Assert
    assert signed_in.user.phone == PHONE


def test_the_session_is_stored_by_token_hash_and_lasts_ninety_days(login, database, clock, security):
    # Arrange
    code = login.issue()

    # Act
    signed_in = login.verify.execute(PHONE, code)

    # Assert
    stored = database.tables.sessions[security.hash_token(signed_in.token)]
    assert signed_in.token not in database.tables.sessions
    assert stored.user_id == signed_in.user.id
    assert stored.expires_at - clock.now() == timedelta(days=90)


def test_the_code_works_only_once(login):
    # Arrange
    code = login.issue()
    login.verify.execute(PHONE, code)

    # Act / Assert
    with pytest.raises(InvalidCode):
        login.verify.execute(PHONE, code)


def test_a_wrong_code_is_refused_and_creates_nobody(login, database):
    # Arrange
    code = login.issue()

    # Act / Assert
    with pytest.raises(InvalidCode, match="Неверный код"):
        login.verify.execute(PHONE, wrong_code(code))
    assert database.tables.users == {} and database.tables.sessions == {}


def test_a_wrong_attempt_is_counted_even_though_it_failed(login, database):
    # Arrange
    code = login.issue()

    # Act
    with pytest.raises(InvalidCode):
        login.verify.execute(PHONE, wrong_code(code))

    # Assert
    assert next(iter(database.tables.otp_codes.values())).attempts == 1


def test_after_five_wrong_attempts_even_the_right_code_is_refused(login):
    # Arrange
    code = login.issue()
    for _ in range(5):
        with pytest.raises(InvalidCode, match="Неверный код"):
            login.verify.execute(PHONE, wrong_code(code))

    # Act / Assert
    with pytest.raises(InvalidCode, match="попыток"):
        login.verify.execute(PHONE, code)


def test_the_attempt_limit_comes_from_the_policy(uow, sender, clock, security):
    # Arrange
    login = Login(uow, sender, clock, security, AuthPolicy(code_max_attempts=1))
    code = login.issue()
    with pytest.raises(InvalidCode, match="Неверный код"):
        login.verify.execute(PHONE, wrong_code(code))

    # Act / Assert
    with pytest.raises(InvalidCode, match="попыток"):
        login.verify.execute(PHONE, code)


def test_an_expired_code_is_refused(login, clock):
    # Arrange
    code = login.issue()
    clock.advance(minutes=5)

    # Act / Assert
    with pytest.raises(InvalidCode, match="истёк"):
        login.verify.execute(PHONE, code)


def test_a_code_is_still_valid_a_second_before_it_expires(login, clock):
    # Arrange
    code = login.issue()
    clock.advance(minutes=4, seconds=59)

    # Act
    signed_in = login.verify.execute(PHONE, code)

    # Assert
    assert signed_in.is_new is True


def test_verifying_without_a_requested_code_fails(login):
    # Arrange: код не запрашивали

    # Act / Assert
    with pytest.raises(InvalidCode, match="не найден"):
        login.verify.execute(PHONE, "123456")


def test_a_newer_code_replaces_the_older_one(uow, sender, clock):
    # Arrange: коды заданы заранее, чтобы старый и новый точно отличались
    login = Login(uow, sender, clock, ScriptedSecurity(["111111", "222222"]))
    old = login.issue()
    clock.advance(seconds=61)
    new = login.issue()

    # Act
    with pytest.raises(InvalidCode, match="Неверный код"):
        login.verify.execute(PHONE, old)
    signed_in = login.verify.execute(PHONE, new)

    # Assert
    assert (old, new) == ("111111", "222222") and signed_in.is_new is True


def test_codes_for_one_phone_do_not_work_for_another(login):
    # Arrange
    code = login.issue(PHONE)
    login.issue("+79990000000")

    # Act / Assert
    with pytest.raises(InvalidCode):
        login.verify.execute("+79990000001", code)


def test_one_user_can_have_several_sessions(login, database, clock):
    # Arrange
    first = login.verify.execute(PHONE, login.issue())
    clock.advance(minutes=2)

    # Act
    second = login.verify.execute(PHONE, login.issue())

    # Assert
    assert len(database.tables.sessions) == 2
    assert first.user.id == second.user.id
