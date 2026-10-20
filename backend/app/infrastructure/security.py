import hashlib
import hmac
import secrets


class HmacSecurity:
    """Коды и токены. Сам код короткий (10^6 вариантов), поэтому его хэш привязан к секрету сервера
    и к идентификатору, а число попыток ограничено в use case. Токен длинный и случайный —
    для него достаточно SHA-256 (медленный хэш нужен для паролей)."""

    def __init__(self, secret_key: str):
        self._secret = secret_key.encode()

    def new_code(self) -> str:
        return f"{secrets.randbelow(10**6):06d}"

    def hash_code(self, identifier: str, code: str) -> str:
        return hmac.new(self._secret, f"{identifier}:{code}".encode(), hashlib.sha256).hexdigest()

    def code_matches(self, identifier: str, code: str, code_hash: str) -> bool:
        return hmac.compare_digest(self.hash_code(identifier, code), code_hash)

    def new_token(self) -> str:
        return "lk_" + secrets.token_urlsafe(32)

    def hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
