"""مستطیل‌های نرمال‌شده برای crop کلی و قطعات تصویر."""

import json
import math
from dataclasses import dataclass

from app.errors import InvalidBoxesError


@dataclass(frozen=True)
class NormalizedRegion:
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        values = (self.x, self.y, self.width, self.height)
        if not all(math.isfinite(value) for value in values):
            raise InvalidBoxesError("مختصات ناحیه باید عددی و معتبر باشند.")
        if self.x < 0 or self.y < 0 or self.width <= 0 or self.height <= 0:
            raise InvalidBoxesError("ابعاد ناحیه باید مثبت و مختصات آن غیرمنفی باشند.")
        if self.x + self.width > 1 or self.y + self.height > 1:
            raise InvalidBoxesError("ناحیه باید داخل تصویر قرار داشته باشد.")


def parse_region(payload: str | dict) -> NormalizedRegion:
    try:
        raw = json.loads(payload) if isinstance(payload, str) else payload
        return NormalizedRegion(
            x=float(raw["x"]),
            y=float(raw["y"]),
            width=float(raw["width"]),
            height=float(raw["height"]),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise InvalidBoxesError("ساختار ناحیه نامعتبر است.") from exc


def parse_regions(payload: str | None, max_regions: int = 24) -> list[NormalizedRegion]:
    if not payload or payload == "[]":
        return []
    try:
        raw_regions = json.loads(payload)
    except (TypeError, json.JSONDecodeError) as exc:
        raise InvalidBoxesError("فهرست نواحی JSON معتبر نیست.") from exc
    if not isinstance(raw_regions, list) or len(raw_regions) > max_regions:
        raise InvalidBoxesError("تعداد نواحی نامعتبر است.")
    return [parse_region(raw) for raw in raw_regions]
