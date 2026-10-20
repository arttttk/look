from fastapi import APIRouter

from app.api.deps import PresenterDep, UseCasesDep, UserDep
from app.api.schemas import ProfileOut, ProfilePatch
from app.application.use_cases.profile import UNSET, LocationInput, ProfileChanges
from app.domain.taxonomy import BUDGETS, CATEGORIES, COLORS, DEPARTMENTS, STYLES

router = APIRouter(tags=["profile"])


@router.get("/me", response_model=ProfileOut)
def get_profile(user: UserDep, presenter: PresenterDep) -> ProfileOut:
    return presenter.profile(user)


@router.patch("/me", response_model=ProfileOut)
def update_profile(
    body: ProfilePatch, user: UserDep, use_cases: UseCasesDep, presenter: PresenterDep
) -> ProfileOut:
    sent = body.model_fields_set

    def pick(field: str):
        return getattr(body, field) if field in sent else UNSET

    location = pick("location")
    changes = ProfileChanges(
        name=pick("name"),
        birth_year=pick("birth_year"),
        onboarded=pick("onboarded"),
        department=pick("department"),
        styles=pick("styles"),
        budget=pick("budget"),
        location=LocationInput(**location.model_dump()) if location not in (UNSET, None) else location,
    )
    return presenter.profile(use_cases.update_profile().execute(user.id, changes))


@router.get("/meta")
def get_meta() -> dict:
    """Справочники для интерфейса: стили, категории, цвета, «для кого», бюджеты."""
    return {
        "styles": STYLES,
        "categories": CATEGORIES,
        "colors": [
            {"id": c.id, "title": c.title, "hex": c.hex, "neutral": c.neutral} for c in COLORS.values()
        ],
        "departments": DEPARTMENTS,
        "budgets": BUDGETS,
    }
