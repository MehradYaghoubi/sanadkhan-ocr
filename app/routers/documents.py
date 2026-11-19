"""روتر مدارک — کنترلر نازک: دریافت درخواست → فراخوانی سرویس → پاسخ."""

import base64
import io

from PIL import Image

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.dependencies import get_extraction_service
from app.errors import ImageTooLargeError, InvalidImageError
from app.extraction.field_specs import list_document_types
from app.schemas import ComposeResponse, DocumentTypeResponse, ExtractionResponse
from app.extraction.regions import parse_region, parse_regions
from app.composition import compose_document
from app.services.extraction_service import ExtractionService

router = APIRouter(prefix="/api", tags=["documents"])
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_DIMENSION = 12000


@router.get("/document-types", response_model=list[DocumentTypeResponse])
def document_types() -> list[DocumentTypeResponse]:
    types = [DocumentTypeResponse(doc_type="auto", title="تشخیص خودکار نوع مدرک")]
    types += [
        DocumentTypeResponse(doc_type=doc_type, title=title)
        for doc_type, title in list_document_types()
    ]
    return types


@router.post("/compose", response_model=ComposeResponse)
async def compose(
    file: UploadFile = File(...),
    document_crop: str = Form(...),
    regions: str | None = Form(None),
    enhance: bool = Form(False),
    show_labels: bool = Form(False),
) -> ComposeResponse:
    image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    _guard_upload(image_bytes)
    document_region = parse_region(document_crop)
    selected_regions = parse_regions(regions)
    output = compose_document(
        image_bytes=image_bytes,
        document_crop=document_region,
        regions=selected_regions,
        enhance=enhance,
        show_labels=show_labels,
    )
    with Image.open(io.BytesIO(output)) as image:
        width, height = image.size
    return ComposeResponse(
        image_b64=base64.b64encode(output).decode("ascii"),
        width=width,
        height=height,
        regions_count=len(selected_regions),
    )


def _guard_upload(image_bytes: bytes) -> None:
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise ImageTooLargeError(10)
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            if max(image.size) > MAX_IMAGE_DIMENSION:
                raise ImageTooLargeError(10)
            image.verify()
    except ImageTooLargeError:
        raise
    except Exception as exc:
        raise InvalidImageError() from exc


@router.post("/extract", response_model=ExtractionResponse)
async def extract(
    file: UploadFile = File(...),
    doc_type: str = Form("auto"),
    service: ExtractionService = Depends(get_extraction_service),
) -> ExtractionResponse:
    image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    result = service.extract(image_bytes, doc_type)
    return ExtractionResponse.from_domain(result)
