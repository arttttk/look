from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    name: str
    region: str | None
    country: str | None
    country_code: str
    lat: float
    lon: float
    timezone: str | None
    population: int | None = None
