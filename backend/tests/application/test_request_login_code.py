import re

import pytest

from app.application.errors import DeliveryFailed, TooManyRequests
from app.application.policies import AuthPolicy
from app.application.use_cases.auth import RequestLoginCode
from app.domain.errors import InvalidValue

PHONE = "+79991234567"


@pytest.fixture()
def make_use_case(uow, sender, clock, security):
    def factory(policy: AuthPolicy | None = None) -> RequestLoginCode:
        return RequestLoginCode(uow, sender, clock, security, policy or AuthPolicy())

    return factory


def test_the_code_is_sent_to_the_normalised_phone(make_use_case, sender):
    # Arrange
    use_case = make_use_case()

    # Act
    issued = use_case.execute("8 (999) 123-45-67")

    # Assert
    assert issued.kind == "phone" and issued.identifier == PHONE
    assert [(kind, ident) for kind, ident, _ in sender.sent] == [("phone", PHONE)]
    assert re.fullmatch(r"\d{6}", sender.last_code(PHONE))


def test_the_code_is_sent_to_a_lowercased_email(make_use_case, sender):
    # Arrange
    use_case = make_use_case()

    # Act
    issued = use_case.execute("  Alice@Example.COM ")

    # Assert
    assert (issued.kind, issued.identifier) == ("email", "alice@example.com")
    assert sender.sent[0][:2] == ("email", "alice@example.com")


def test_the_caller_learns_when_a_new_code_can_be_requested(make_use_case):
    # Arrange
    use_case = make_use_case()

    # Act
    issued = use_case.execute(PHONE)

    # Assert
    assert issued.resend_after == 60


def test_the_code_itself_is_not_returned_by_default(make_use_case):
    # Arrange
    use_case = make_use_case()

    # Act
    issued = use_case.execute(PHONE)

    # Assert
    assert issued.dev_code is None


def test_the_code_is_returned_in_dev_mode(make_use_case, sender):
    # Arrange
    use_case = make_use_case(AuthPolicy(return_dev_code=True))

    # Act
    issued = use_case.execute(PHONE)

    # Assert
    assert issued.dev_code == sender.last_code(PHONE)


def test_only_a_hash_of_the_code_is_stored(make_use_case, sender, database):
    # Arrange
    use_case = make_use_case()

    # Act
    use_case.execute(PHONE)

    # Assert
    stored = next(iter(database.tables.otp_codes.values()))
    code = sender.last_code(PHONE)
    assert stored.code_hash != code and code not in stored.code_hash
    assert len(stored.code_hash) == 64


def test_the_code_lives_for_five_minutes(make_use_case, database, clock):
    # Arrange
    use_case = make_use_case()

    # Act
    use_case.execute(PHONE)

    # Assert
    stored = next(iter(database.tables.otp_codes.values()))
    assert (stored.expires_at - clock.now()).total_seconds() == 300


def test_a_second_request_during_the_cooldown_is_refused_with_the_time_left(make_use_case, clock):
    # Arrange
    use_case = make_use_case()
    use_case.execute(PHONE)
    clock.advance(seconds=20)

    # Act / Assert
    with pytest.raises(TooManyRequests) as refusal:
        use_case.execute(PHONE)
    assert refusal.value.retry_after == 40


def test_phone_formats_share_one_cooldown(make_use_case):
    # Arrange
    use_case = make_use_case()
    use_case.execute("+7 999 123-45-67")

    # Act / Assert
    with pytest.raises(TooManyRequests):
        use_case.execute("89991234567")


def test_a_new_code_can_be_requested_after_the_cooldown(make_use_case, sender, clock):
    # Arrange
    use_case = make_use_case()
    use_case.execute(PHONE)
    clock.advance(seconds=61)

    # Act
    use_case.execute(PHONE)

    # Assert
    assert len(sender.sent) == 2


def test_different_identifiers_do_not_share_a_cooldown(make_use_case, sender):
    # Arrange
    use_case = make_use_case()
    use_case.execute(PHONE)

    # Act
    use_case.execute("+79990000000")
    use_case.execute("a@example.com")

    # Assert
    assert len(sender.sent) == 3


def test_the_hourly_cap_stops_a_flood_of_requests(make_use_case, clock):
    # Arrange: пауза между кодами отключена, чтобы упереться именно в часовой лимит
    use_case = make_use_case(AuthPolicy(code_resend_seconds=0, code_max_per_hour=3))
    for _ in range(3):
        use_case.execute(PHONE)

    # Act / Assert
    with pytest.raises(TooManyRequests) as refusal:
        use_case.execute(PHONE)
    assert refusal.value.retry_after == 3600


def test_the_hourly_cap_resets_after_an_hour(make_use_case, sender, clock):
    # Arrange
    use_case = make_use_case(AuthPolicy(code_resend_seconds=0, code_max_per_hour=2))
    use_case.execute(PHONE)
    use_case.execute(PHONE)
    clock.advance(hours=1, seconds=1)

    # Act
    use_case.execute(PHONE)

    # Assert
    assert len(sender.sent) == 3


def test_a_failed_delivery_is_reported(make_use_case, sender):
    # Arrange
    sender.fail = True
    use_case = make_use_case()

    # Act / Assert
    with pytest.raises(DeliveryFailed):
        use_case.execute(PHONE)


def test_an_undelivered_code_is_not_kept_and_does_not_start_a_cooldown(make_use_case, sender, database):
    # Arrange
    sender.fail = True
    use_case = make_use_case()
    with pytest.raises(DeliveryFailed):
        use_case.execute(PHONE)
    sender.fail = False

    # Act
    use_case.execute(PHONE)  # сразу же, без ожидания

    # Assert
    assert len(database.tables.otp_codes) == 1 and len(sender.sent) == 1


@pytest.mark.parametrize("raw", ["", "abc", "12345", "name@"])
def test_garbage_is_rejected_before_anything_is_sent(make_use_case, sender, database, raw):
    # Arrange
    use_case = make_use_case()

    # Act / Assert
    with pytest.raises(InvalidValue):
        use_case.execute(raw)
    assert sender.sent == [] and database.tables.otp_codes == {}
