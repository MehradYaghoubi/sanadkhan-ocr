"""لایه Response — شکل‌دهی خروجی API با Pydantic؛ مدل‌های داخلی مستقیم بیرون نمی‌روند."""

from pydantic import BaseModel

from app.services.extraction_service import ExtractionResult


class FieldResponse(BaseModel):
    key: str
    label: str
    value: str
    confidence: float | None = None
    evidence: str | None = None
    bbox: tuple[int, int, int, int] | None = None


class UsageResponse(BaseModel):
    input_tokens: int
    output_tokens: int
    cost_toman: int | None


class ExtractionResponse(BaseModel):
    doc_type: str
    title: str
    fields: list[FieldResponse]
    raw_text: str
    usage: UsageResponse | None = None

    @classmethod
    def from_domain(cls, result: ExtractionResult) -> "ExtractionResponse":
        return cls(
            doc_type=result.doc_type,
            title=result.title,
            fields=[
                FieldResponse(
                    key=f.key,
                    label=f.label,
                    value=f.value,
                    confidence=f.confidence,
                    evidence=f.evidence,
                    bbox=f.bbox,
                )
                for f in result.fields
            ],
            raw_text=result.raw_text,
            usage=UsageResponse(
                input_tokens=result.usage.input_tokens,
                output_tokens=result.usage.output_tokens,
                cost_toman=result.usage.cost_toman,
            )
            if result.usage is not None
            else None,
        )


class DocumentTypeResponse(BaseModel):
    doc_type: str
    title: str


class ComposeResponse(BaseModel):
    image_b64: str
    width: int
    height: int
    regions_count: int
