"""خواننده سند: VlmReader (پردازش مستقیم و سریع تصویر سند با مدل بینایی)."""

import base64

from app.imaging import to_jpeg
from app.readers.base import DocumentReader, ReadOutcome
from app.readers.structuring import (
    SYSTEM_PROMPT,
    build_prompt,
    parse_outcome,
)


class VlmReader(DocumentReader):
    """خواننده تصویر سند بر پایه Vision LLM تک‌پاس و پرسرعت."""

    def __init__(self, llm, model: str) -> None:
        self._llm = llm
        self._model = model

    def read(self, image_bytes: bytes, doc_type: str) -> ReadOutcome:
        # compose خروجی را دوباره روشن/تیره یا کوچک نمی‌کنیم؛ preview اپراتور
        # باید همان تصویری باشد که برای VLM ارسال می‌شود.
        jpeg = to_jpeg(image_bytes, max_dimension=None, autocontrast=False)
        images_b64 = [base64.b64encode(jpeg).decode("ascii")]

        prompt = build_prompt(doc_type)
        result = self._llm.chat_json(
            self._model,
            prompt,
            images_b64=images_b64,
            system_prompt=SYSTEM_PROMPT,
        )
        resolved, fields, raw_text = parse_outcome(result.content, doc_type)

        return ReadOutcome(
            doc_type=resolved, fields=fields, raw_text=raw_text, usage=result
        )
