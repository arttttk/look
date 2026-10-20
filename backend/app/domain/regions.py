"""Региональные подсказки по стилю.

ЭТО ЭВРИСТИКА, а не знание о людях: небольшая таблица «страна -> стили, которые там обычно
носят», она работает только как мягкая подсказка, пока пользователь «не определился» со стилем.
Значения — заглушка, которую стоит уточнить реальными данными (продажи, поведение пользователей).
Как только человек выбрал стили, регион на подбор не влияет.
"""

REGION_STYLES: dict[str, list[str]] = {
    "RU": ["casual", "classic"],
    "BY": ["casual", "classic"],
    "KZ": ["casual", "classic"],
    "UA": ["casual", "street"],
    "DE": ["minimal", "casual"],
    "SE": ["minimal", "casual"],
    "NO": ["minimal", "casual"],
    "DK": ["minimal", "casual"],
    "FI": ["minimal", "casual"],
    "FR": ["classic", "vintage"],
    "IT": ["classic", "vintage"],
    "ES": ["classic", "casual"],
    "GB": ["classic", "vintage"],
    "US": ["casual", "street"],
    "CA": ["casual", "street"],
    "JP": ["minimal", "street"],
    "KR": ["street", "minimal"],
    "CN": ["street", "casual"],
    "TR": ["classic", "casual"],
    "AE": ["classic", "minimal"],
}


def regional_styles(country_code: str | None) -> list[str]:
    return list(REGION_STYLES.get((country_code or "").upper(), []))
