import phonenumbers
from email_validator import EmailNotValidError, validate_email

from app.domain.errors import InvalidValue

MESSAGE = "Введите корректный телефон или почту"


def normalize_identifier(raw: str, default_region: str) -> tuple[str, str]:
    """Телефон или почта -> (вид, нормализованное значение). InvalidValue, если ни то ни другое.

    Телефон приводится к E.164 (+79991234567): номер без «+» трактуется по default_region,
    поэтому «8 999 123-45-67» и «+7 (999) 123-45-67» — один и тот же пользователь.
    Почта приводится к нижнему регистру."""
    value = raw.strip()
    if not value:
        raise InvalidValue(MESSAGE)

    if "@" in value:
        try:
            result = validate_email(value, check_deliverability=False)
        except EmailNotValidError as error:
            raise InvalidValue(MESSAGE) from error
        return "email", result.normalized.lower()

    try:
        number = phonenumbers.parse(value, default_region)
    except phonenumbers.NumberParseException as error:
        raise InvalidValue(MESSAGE) from error
    if not phonenumbers.is_valid_number(number):
        raise InvalidValue(MESSAGE)
    return "phone", phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
