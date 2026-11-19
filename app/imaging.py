"""آماده‌سازی قاب سند و variantهای کیفیتی cropهای تأییدشده."""

import io

from PIL import Image, ImageOps

from app.errors import InvalidImageError


def to_jpeg(
    image_bytes: bytes,
    max_dimension: int | None = 2048,
    quality: int = 90,
    autocontrast: bool = True,
) -> bytes:
    """تبدیل تصویر به JPEG با حفظ جزئیات بیشتر برای متن ریز."""
    try:
        _register_heif_support()
        with Image.open(io.BytesIO(image_bytes)) as raw_img:
            # جهت‌دهی بر اساس EXIF
            image = ImageOps.exif_transpose(raw_img).convert("RGB")

            # سقف ابعاد برای کنترل هزینه، بدون کوچک‌کردن شدید متن‌های ریز.
            if max_dimension is not None and max(image.size) > max_dimension:
                image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

            # کنتراست ملایم جهت خوانایی وضوح ارقام
            if autocontrast:
                image = ImageOps.autocontrast(image, cutoff=0.5)

            buffer = io.BytesIO()
            image.save(buffer, "JPEG", quality=quality)
            return buffer.getvalue()
    except InvalidImageError:
        raise
    except Exception as exc:
        raise InvalidImageError() from exc


def _register_heif_support() -> None:
    try:
        import pillow_heif

        pillow_heif.register_heif_opener()
    except ImportError:
        pass
