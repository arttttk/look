from fastapi import APIRouter

from app.api.deps import AuthDep, UseCasesDep
from app.api.schemas import CodeRequest, CodeSent, TokenOut, VerifyIn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/code", response_model=CodeSent, status_code=202)
def request_code(body: CodeRequest, use_cases: UseCasesDep) -> CodeSent:
    """Шаг 1 входа: шлём одноразовый код на телефон или почту. Нового человека это же и регистрирует."""
    issued = use_cases.request_login_code().execute(body.identifier)
    return CodeSent(
        kind=issued.kind,  # type: ignore[arg-type]
        identifier=issued.identifier,
        resend_after=issued.resend_after,
        dev_code=issued.dev_code,
    )


@router.post("/verify", response_model=TokenOut)
def verify_code(body: VerifyIn, use_cases: UseCasesDep) -> TokenOut:
    """Шаг 2: код -> токен сессии. Приложение хранит токен и шлёт его как Bearer."""
    signed_in = use_cases.verify_login_code().execute(body.identifier, body.code)
    return TokenOut(access_token=signed_in.token, user_id=signed_in.user.id, is_new=signed_in.is_new)


@router.post("/logout", status_code=204)
def logout(auth: AuthDep, use_cases: UseCasesDep) -> None:
    """Выход: токен перестаёт работать сразу, не дожидаясь срока."""
    use_cases.logout().execute(auth.session)
