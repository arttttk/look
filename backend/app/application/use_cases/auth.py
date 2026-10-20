import math
from dataclasses import dataclass
from datetime import timedelta

from app.application.errors import DeliveryFailed, InvalidCode, TooManyRequests, Unauthorized
from app.application.policies import AuthPolicy
from app.application.ports import Clock, CodeSender, Security, UnitOfWork
from app.domain.entities import AuthSession, OtpCode, User
from app.domain.identifiers import normalize_identifier


@dataclass(frozen=True)
class CodeIssued:
    kind: str
    identifier: str  # в нормализованном виде
    resend_after: int  # через сколько секунд можно запросить код снова
    dev_code: str | None


@dataclass(frozen=True)
class SignedIn:
    user: User
    token: str
    is_new: bool


@dataclass(frozen=True)
class Authenticated:
    user: User
    session: AuthSession


class RequestLoginCode:
    """Шаг 1 входа: отправить одноразовый код на телефон или почту. Нового человека это же и регистрирует."""

    def __init__(
        self, uow: UnitOfWork, sender: CodeSender, clock: Clock, security: Security, policy: AuthPolicy
    ):
        self._uow = uow
        self._sender = sender
        self._clock = clock
        self._security = security
        self._policy = policy

    def execute(self, raw_identifier: str) -> CodeIssued:
        kind, identifier = normalize_identifier(raw_identifier, self._policy.default_phone_region)
        now = self._clock.now()
        policy = self._policy

        with self._uow as uow:
            recent = uow.otp_codes.recent(identifier, since=now - timedelta(hours=1))
            if recent:
                wait = policy.code_resend_seconds - (now - recent[0].created_at).total_seconds()
                if wait > 0:
                    raise TooManyRequests(
                        "Код уже отправлен. Подождите немного перед повторной отправкой.", math.ceil(wait)
                    )
            if len(recent) >= policy.code_max_per_hour:
                raise TooManyRequests("Слишком много запросов кода. Попробуйте через час.", 3600)

            code = self._security.new_code()
            uow.otp_codes.add(
                OtpCode(
                    identifier=identifier,
                    kind=kind,
                    code_hash=self._security.hash_code(identifier, code),
                    created_at=now,
                    expires_at=now + timedelta(seconds=policy.code_ttl_seconds),
                )
            )
            try:
                self._sender.send(kind, identifier, code)
            except Exception as error:
                # Выход без commit откатит код: недоставленный код не считается в лимит.
                raise DeliveryFailed("Не удалось отправить код. Попробуйте ещё раз.") from error
            uow.commit()

        return CodeIssued(
            kind, identifier, policy.code_resend_seconds, code if policy.return_dev_code else None
        )


class VerifyLoginCode:
    """Шаг 2 входа: код -> сессия. Если человека ещё нет, создаёт его."""

    def __init__(self, uow: UnitOfWork, clock: Clock, security: Security, policy: AuthPolicy):
        self._uow = uow
        self._clock = clock
        self._security = security
        self._policy = policy

    def execute(self, raw_identifier: str, code: str) -> SignedIn:
        kind, identifier = normalize_identifier(raw_identifier, self._policy.default_phone_region)
        now = self._clock.now()

        with self._uow as uow:
            otp = uow.otp_codes.latest_active(identifier)
            if otp is None or otp.is_expired(now):
                raise InvalidCode("Код не найден или истёк. Запросите новый.")
            if otp.attempts >= self._policy.code_max_attempts:
                raise InvalidCode("Слишком много попыток. Запросите новый код.")

            otp.attempts += 1
            if not self._security.code_matches(identifier, code, otp.code_hash):
                uow.otp_codes.save(otp)
                uow.commit()  # попытку засчитываем, даже если код неверный
                raise InvalidCode("Неверный код")

            otp.consumed = True
            uow.otp_codes.save(otp)

            user = (
                uow.users.get_by_phone(identifier) if kind == "phone" else uow.users.get_by_email(identifier)
            )
            is_new = user is None
            if user is None:
                user = User.register(kind, identifier, now)
                uow.users.add(user)

            token = self._security.new_token()
            uow.sessions.add(
                AuthSession(
                    token_hash=self._security.hash_token(token),
                    user_id=user.id,
                    created_at=now,
                    expires_at=now + timedelta(days=self._policy.session_days),
                    last_used_at=now,
                )
            )
            uow.commit()

        return SignedIn(user=user, token=token, is_new=is_new)


class AuthenticateToken:
    """По токену из заголовка находит сессию и пользователя."""

    def __init__(self, uow: UnitOfWork, clock: Clock, security: Security):
        self._uow = uow
        self._clock = clock
        self._security = security

    def execute(self, token: str) -> Authenticated:
        now = self._clock.now()

        with self._uow as uow:
            session = uow.sessions.get(self._security.hash_token(token))
            if session is None or session.is_expired(now):
                raise Unauthorized("Нужна авторизация")

            user = uow.users.get(session.user_id)
            if user is None:
                raise Unauthorized("Нужна авторизация")

            if session.needs_touch(now):
                session.last_used_at = now
                uow.sessions.save(session)
                uow.commit()

        return Authenticated(user=user, session=session)


class Logout:
    """Выход: токен перестаёт работать сразу, не дожидаясь срока."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, session: AuthSession) -> None:
        with self._uow as uow:
            uow.sessions.delete(session.token_hash)
            uow.commit()
