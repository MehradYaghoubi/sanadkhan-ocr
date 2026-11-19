"""ساخت تصویر نهایی از crop کلی و قطعات انتخابی اپراتور."""

import io

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps

from app.errors import InvalidImageError
from app.extraction.regions import NormalizedRegion


PADDING = 24
REGION_MARGIN = 0.02


def compose_document(
    image_bytes: bytes,
    document_crop: NormalizedRegion,
    regions: list[NormalizedRegion],
    enhance: bool,
    show_labels: bool,
) -> bytes:
    try:
        with Image.open(io.BytesIO(image_bytes)) as raw:
            image = ImageOps.exif_transpose(raw).convert("RGB")
            document = image.crop(_pixels(document_crop, image.width, image.height))
            if not regions:
                final = document.copy()
            else:
                parts = [_crop_with_margin(document, region) for region in regions]
                width = max(part.width for part in parts) + PADDING * 2
                height = sum(part.height for part in parts) + PADDING * (len(parts) + 1)
                final = Image.new("RGB", (width, height), "white")
                draw = ImageDraw.Draw(final)
                top = PADDING
                for index, part in enumerate(parts, start=1):
                    final.paste(part, (PADDING, top))
                    if show_labels:
                        draw.rectangle((PADDING, top, PADDING + 30, top + 24), fill="white")
                        draw.text((PADDING + 8, top + 4), str(index), fill="black")
                    top += part.height + PADDING
            if enhance:
                final = _enhance_final(final)
            return _encode(final)
    except InvalidImageError:
        raise
    except Exception as exc:
        raise InvalidImageError() from exc


def _crop_with_margin(image: Image.Image, region: NormalizedRegion) -> Image.Image:
    margin_x = min(region.width * REGION_MARGIN, region.x, 1 - region.x - region.width)
    margin_y = min(region.height * REGION_MARGIN, region.y, 1 - region.y - region.height)
    expanded = NormalizedRegion(
        region.x - margin_x,
        region.y - margin_y,
        region.width + margin_x * 2,
        region.height + margin_y * 2,
    )
    return image.crop(_pixels(expanded, image.width, image.height))


def _pixels(region: NormalizedRegion, width: int, height: int) -> tuple[int, int, int, int]:
    left = max(0, min(width - 1, round(region.x * width)))
    top = max(0, min(height - 1, round(region.y * height)))
    right = max(left + 1, min(width, round((region.x + region.width) * width)))
    bottom = max(top + 1, min(height, round((region.y + region.height) * height)))
    return left, top, right, bottom


def _enhance_final(image: Image.Image) -> Image.Image:
    """بهبود قطعی و محافظه‌کارانه؛ هیچ متن یا پیکسلی را مولدانه بازسازی نمی‌کند."""
    bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    denoised = cv2.fastNlMeansDenoisingColored(bgr, None, 3, 3, 7, 21)
    lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
    light, a_channel, b_channel = cv2.split(lab)
    light = cv2.createCLAHE(clipLimit=1.35, tileGridSize=(8, 8)).apply(light)
    normalized = cv2.cvtColor(cv2.merge((light, a_channel, b_channel)), cv2.COLOR_LAB2BGR)
    sharpened = cv2.addWeighted(normalized, 1.08, cv2.GaussianBlur(normalized, (0, 0), 0.8), -0.08, 0)
    return Image.fromarray(cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB))


def _encode(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=94, optimize=True)
    return output.getvalue()
