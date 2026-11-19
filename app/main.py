"""نقطه ورود برنامه: FastAPI + فایل‌های استاتیک + نگاشت خطاهای دامنه به HTTP."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.errors import (
    ImageTooLargeError,
    InvalidBoxesError,
    InvalidImageError,
    LlmUnavailableError,
    ProviderConfigurationError,
    UnknownDocumentTypeError,
)
from app.routers.documents import router as documents_router

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="سندخوان", description="استخراج خودکار اطلاعات از تصویر مدارک")
app.include_router(documents_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.exception_handler(InvalidImageError)
async def _invalid_image(_: Request, exc: InvalidImageError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(ImageTooLargeError)
async def _image_too_large(_: Request, exc: ImageTooLargeError) -> JSONResponse:
    return JSONResponse(status_code=413, content={"detail": str(exc)})


@app.exception_handler(UnknownDocumentTypeError)
async def _unknown_doc_type(_: Request, exc: UnknownDocumentTypeError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(InvalidBoxesError)
async def _invalid_boxes(_: Request, exc: InvalidBoxesError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(LlmUnavailableError)
async def _llm_unavailable(_: Request, exc: LlmUnavailableError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(ProviderConfigurationError)
async def _provider_configuration(_: Request, exc: ProviderConfigurationError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def _unhandled(_: Request, _exc: Exception) -> JSONResponse:
    """Return a generic response without internal exception details."""
    return JSONResponse(
        status_code=500,
        content={"detail": "خطای داخلی سرویس"},
    )
