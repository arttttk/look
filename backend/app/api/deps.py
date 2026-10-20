from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.container import Container, UseCases
from app.api.presenter import Presenter
from app.application.errors import Unauthorized
from app.application.use_cases.auth import Authenticated
from app.domain.entities import User

bearer = HTTPBearer(auto_error=False)


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_use_cases(container: ContainerDep) -> UseCases:
    return UseCases(container)


UseCasesDep = Annotated[UseCases, Depends(get_use_cases)]


def get_presenter(request: Request, container: ContainerDep) -> Presenter:
    return Presenter(str(request.base_url), container.storage)


PresenterDep = Annotated[Presenter, Depends(get_presenter)]


def current_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    use_cases: UseCasesDep,
) -> Authenticated:
    if credentials is None:
        raise Unauthorized("Нужна авторизация")
    return use_cases.authenticate().execute(credentials.credentials)


AuthDep = Annotated[Authenticated, Depends(current_auth)]


def current_user(auth: AuthDep) -> User:
    return auth.user


UserDep = Annotated[User, Depends(current_user)]
