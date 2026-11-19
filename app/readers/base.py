"""قرارداد خواندن مدرک؛ سرویس فقط این قرارداد را می‌شناسد."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.extraction.field_specs import Field

AUTO_DOC_TYPE = "auto"


@dataclass(frozen=True)
class ReadOutcome:
    """خروجی خواندن یک مدرک — نوعِ نهایی (پس از تشخیص خودکار)، فیلدها، متن خام."""

    doc_type: str
    fields: list[Field]
    raw_text: str
    usage: object | None = None


class DocumentReader(ABC):
    @abstractmethod
    def read(self, image_bytes: bytes, doc_type: str) -> ReadOutcome:
        """doc_type می‌تواند AUTO_DOC_TYPE باشد؛ خواننده باید نوع را تشخیص دهد."""
