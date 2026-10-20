from dataclasses import dataclass
from enum import Enum

from app.application.errors import NotFound
from app.application.ports import Clock, UnitOfWork
from app.domain.entities import User
from app.domain.errors import InvalidValue
from app.domain.profile_rules import make_location, normalize_name, validate_birth_year
from app.domain.taxonomy import BUDGET_CAPS, DEPARTMENTS, STYLES


class Unset(Enum):
    """«Поле не присылали» — отличается от None, который значит «очистить поле»."""

    UNSET = "unset"


UNSET = Unset.UNSET


@dataclass(frozen=True)
class LocationInput:
    city: str
    country_code: str
    lat: float
    lon: float
    timezone: str | None = None


@dataclass(frozen=True)
class ProfileChanges:
    """Частичное обновление профиля: меняются только присланные поля. None очищает необязательные
    (name, birth_year, budget, location); обязательные (department, styles, onboarded) очистить нельзя."""

    name: str | None | Unset = UNSET
    birth_year: int | None | Unset = UNSET
    onboarded: bool | None | Unset = UNSET
    department: str | None | Unset = UNSET
    styles: list[str] | None | Unset = UNSET
    budget: str | None | Unset = UNSET
    location: LocationInput | None | Unset = UNSET


_STYLE_IDS = {s["id"] for s in STYLES}
_DEPARTMENT_IDS = {d["id"] for d in DEPARTMENTS}


class UpdateProfile:
    def __init__(self, uow: UnitOfWork, clock: Clock):
        self._uow = uow
        self._clock = clock

    def execute(self, user_id: str, changes: ProfileChanges) -> User:
        self._reject_cleared_required(changes)

        with self._uow as uow:
            user = uow.users.get(user_id)
            if user is None:
                raise NotFound("Пользователь не найден")

            self._apply(user, changes)
            uow.users.save(user)
            uow.commit()
        return user

    @staticmethod
    def _reject_cleared_required(changes: ProfileChanges) -> None:
        for field in ("onboarded", "department", "styles"):
            if getattr(changes, field) is None:
                raise InvalidValue(f"Поле {field} нельзя очистить")

    def _apply(self, user: User, changes: ProfileChanges) -> None:
        if changes.name is not UNSET:
            user.name = normalize_name(changes.name)
        if changes.birth_year is not UNSET:
            user.birth_year = validate_birth_year(changes.birth_year, self._clock.now().year)
        if changes.onboarded is not UNSET:
            user.onboarded = bool(changes.onboarded)
        if changes.department is not UNSET:
            if changes.department not in _DEPARTMENT_IDS:
                raise InvalidValue("Неизвестное значение «для кого подбираем»")
            user.department = str(changes.department)
        if changes.styles is not UNSET:
            styles = list(dict.fromkeys(changes.styles or []))  # без дублей, порядок выбора сохраняем
            if not set(styles) <= _STYLE_IDS:
                raise InvalidValue("Неизвестный стиль")
            user.styles = styles
        if changes.budget is not UNSET:
            if changes.budget is not None and changes.budget not in BUDGET_CAPS:
                raise InvalidValue("Неизвестный бюджет")
            user.budget = changes.budget
        if changes.location is not UNSET:
            loc = changes.location
            user.location = (
                make_location(loc.city, loc.country_code, loc.lat, loc.lon, loc.timezone) if loc else None
            )
