"""سرویس استخراج — منطق اصلی، مستقل از HTTP.

فقط خواننده بینایی (VLM) باقی مانده: تصویر → مدل → JSON.
"""

import os
from dataclasses import dataclass

from app.errors import ImageTooLargeError, UnknownDocumentTypeError
from app.extraction.field_specs import FIELD_SPECS, Field, get_title
from app.readers.base import AUTO_DOC_TYPE, DocumentReader

MB = 1_000_000


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
    cost_toman: int | None


@dataclass(frozen=True)
class ExtractionResult:
    """خروجی نهایی استخراج — DTO تغییرناپذیر."""

    doc_type: str
    title: str
    fields: list[Field]
    raw_text: str
    usage: Usage | None = None


class ExtractionService:
    MAX_IMAGE_MB = 10

    def __init__(self, reader: DocumentReader) -> None:
        self._reader = reader

    def extract(self, image_bytes: bytes, doc_type: str) -> ExtractionResult:
        self._guard_size(image_bytes)
        if doc_type != AUTO_DOC_TYPE and doc_type not in FIELD_SPECS:
            raise UnknownDocumentTypeError(doc_type)

        outcome = self._reader.read(image_bytes, doc_type)
        usage = outcome.usage
        return ExtractionResult(
            doc_type=outcome.doc_type,
            title=get_title(outcome.doc_type),
            fields=outcome.fields,
            raw_text=outcome.raw_text,
            usage=Usage(
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
                cost_toman=compute_cost(usage.prompt_tokens, usage.completion_tokens),
            )
            if usage is not None
            else None,
        )

    def _guard_size(self, image_bytes: bytes) -> None:
        if len(image_bytes) > self.MAX_IMAGE_MB * 1024 * 1024:
            raise ImageTooLargeError(self.MAX_IMAGE_MB)


def compute_cost(prompt_tokens: int, completion_tokens: int) -> int | None:
    """تخمین هزینه به تومان؛ خاموش پیش‌فرض (SANADKHAN_COST_ENABLED=1)."""
    if os.getenv("SANADKHAN_COST_ENABLED", "0") != "1":
        return None
    base = float(os.getenv("SANADKHAN_PRICE_PER_M", "0"))
    price_in = float(os.getenv("SANADKHAN_PRICE_INPUT_PER_M", base))
    price_out = float(os.getenv("SANADKHAN_PRICE_OUTPUT_PER_M", base))
    return round((prompt_tokens * price_in + completion_tokens * price_out) / MB)
