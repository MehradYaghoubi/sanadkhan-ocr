"""ساخت پرامپت‌ها، پارس JSON و اعتبارسنجی سخت‌گیرانه فیلدها.

کاهش توهم (Anti-Hallucination): عدم حدس زدن داده‌ها، ارسال پیام سیستم صریح
و اعتبارسنجی کد ملی، شماره کارت و شبا.
"""

import json
import re

from app.extraction.field_specs import FIELD_SPECS, Field, list_document_types
from app.extraction.text_utils import normalize_text
from app.extraction.validators import is_valid_card_number, is_valid_national_id
from app.readers.base import AUTO_DOC_TYPE

_NATIONAL_ID_KEYS = frozenset({"national_id"})
_CARD_NUMBER_KEYS = frozenset({"card_number"})

SYSTEM_PROMPT = (
    "تو یک سامانه فوق‌العاده دقیق و سخت‌گیر استخراج اطلاعات از تصویر مدارک ایرانی هستی.\n"
    "قوانین حیاتی و قدغن‌ها:\n"
    "۱. فقط و فقط مقادیری که کاملاً، صریحاً و با وضوح ۱۰۰٪ روی تصویر مدرک نوشته شده‌اند را استخراج کن.\n"
    "۲. هرگز، تحت هیچ شرایطی، مقداری را حدس نزن، تخمین نزن، بازسازی نکن و اختراع نکن.\n"
    "۳. اگر یک فیلد (مثلاً نام، کد ملی، یا شماره شناسنامه) در تصویر دیده نمیشود یا خوانا نیست، آن کلید را اصلاً در شیء fields قرار نده.\n"
    "۴. ارائه اطلاعات نادرست یا حدسی به اپراتور خطای بزرگ محسوب می‌شود؛ بنابراین فقط داده‌های قطعی را قرار بده."
    "\n۵. هر فیلد باید به‌صورت شیء شامل value، confidence بین 0 و 1 و evidence (عین متن قابل‌مشاهده) باشد."
    "\n۶. اگر evidence نداری یا confidence کمتر از 0.80 است، آن فیلد را اصلاً خروجی نده."
)

def build_prompt(doc_type: str) -> str:
    """پرامپت کاربر جهت استخراج فیلدهای مشخص شده."""
    sections: list[str] = [
        _doc_type_instruction(doc_type),
        _fields_instruction(doc_type),
        (
            "دستورالعمل خروجی:\n"
            "- تصویر اول نمای کامل و تصاویر بعدی cropهای تقویت‌شده از نواحی متن هستند؛ همه را با هم مقایسه کن.\n"
            "- خروجی حتماً و فقط یک شیء JSON شامل doc_type، fields و raw_text باشد.\n"
            "- fields یک شیء است؛ هر مقدار آن باید دقیقاً به‌شکل {\"value\": string, \"confidence\": number, \"evidence\": string, \"bbox\": [x1,y1,x2,y2] یا null} باشد.\n"
            "- evidence باید عین متن خوانده‌شده از تصویر باشد، نه توضیح یا حدس.\n"
            "- از حدس زدن یا ساختن داده‌های خیالی خودداری کن؛ فیلدهای غیرموجود را کلاً حذف کن.\n"
            "- همه ارقام را به‌صورت لاتین (0-9) بنویس.\n"
            "- raw_text: متن کامل قابل‌مشاهده مدرک، خط‌به‌خط."
        ),
    ]
    return "\n\n".join(sections)


def parse_outcome(content: str, requested_doc_type: str) -> tuple[str, list[Field], str]:
    """رشته JSON مدل → (doc_type نهایی، فیلدهای معتبرشده، متن خام)."""
    data = _load_json(content)

    doc_type = _resolve_doc_type(data.get("doc_type"), requested_doc_type)
    raw_fields = data.get("fields") or {}
    raw_text = str(data.get("raw_text") or "").strip()

    labels = {key: label for key, label, _ in FIELD_SPECS.get(doc_type, [])}
    fields: list[Field] = []
    for key, value in raw_fields.items() if isinstance(raw_fields, dict) else []:
        field = _finalize_field(str(key), value, labels)
        if field is not None:
            fields.append(field)

    return doc_type, fields, raw_text


# ---------- internals ----------

def _doc_type_instruction(doc_type: str) -> str:
    if doc_type != AUTO_DOC_TYPE:
        return f'نوع مدرک ورودی: "{doc_type}". در خروجی doc_type را همین مقدار بگذار.'

    options = "، ".join(
        f'"{dt}" ({title})' for dt, title in list_document_types()
    )
    return (
        "ابتدا نوع مدرک را به‌دقت از بین این گزینه‌ها تشخیص بده. "
        f"doc_type باید یکی از این مقادیر باشد: {options}"
    )


def _fields_instruction(doc_type: str) -> str:
    if doc_type != AUTO_DOC_TYPE:
        spec_lines = "\n".join(
            f'  - "{key}": {label} ({hint})' for key, label, hint in FIELD_SPECS[doc_type]
        )
        return f'کلیدهای مجاز fields برای مدرک "{doc_type}":\n{spec_lines}'

    parts = []
    for dt, title in list_document_types():
        spec_lines = "\n".join(
            f'  - "{key}": {label}' for key, label, hint in FIELD_SPECS[dt]
        )
        parts.append(f'اگر doc_type="{dt}" ({title}) بود، فقط از این کلیدها استفاده کن:\n{spec_lines}')
    return "\n\n".join(parts)


def _load_json(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _resolve_doc_type(model_doc_type, requested: str) -> str:
    if requested != AUTO_DOC_TYPE:
        return requested
    if isinstance(model_doc_type, str) and model_doc_type in FIELD_SPECS:
        return model_doc_type
    return "generic"


def _finalize_field(key: str, value, labels: dict[str, str]) -> Field | None:
    if key not in labels or not isinstance(value, dict):
        return None

    raw_value = value.get("value")
    evidence = normalize_text(str(value.get("evidence") or "")).strip()
    try:
        confidence = float(value.get("confidence"))
    except (TypeError, ValueError):
        return None
    if not evidence or not 0.8 <= confidence <= 1.0:
        return None

    text = normalize_text(str(raw_value or "")).strip()
    if not text or text.lower() in ("null", "none", "-"):
        return None

    label = labels[key]

    if key in _NATIONAL_ID_KEYS:
        digits = re.sub(r"\D", "", text)
        if len(digits) != 10 or not is_valid_national_id(digits):
            return None
        text = digits

    elif key in _CARD_NUMBER_KEYS:
        digits = re.sub(r"\D", "", text)
        if len(digits) != 16 or not is_valid_card_number(digits):
            return None
        text = "-".join(digits[i:i + 4] for i in range(0, 16, 4))

    elif key == "iban":
        compact = re.sub(r"[\s\-.]", "", text.upper())
        if not re.fullmatch(r"IR\d{24}", compact):
            return None
        text = compact

    elif key == "certificate_serial":
        # نرمال‌سازی سری و سریال شناسنامه مانند (787680 / 20 د)
        text = re.sub(r"(\d+)\s*([آ-یa-zA-Z])", r"\1 \2", text)
        text = re.sub(r"([آ-یa-zA-Z])\s*(\d+)", r"\1 \2", text)
        text = re.sub(r"\s*/\s*", " / ", text)
        text = re.sub(r"\s+", " ", text).strip()

    bbox = value.get("bbox")
    if isinstance(bbox, list) and len(bbox) == 4 and all(isinstance(item, (int, float)) for item in bbox):
        bbox = tuple(round(float(item)) for item in bbox)
    else:
        bbox = None

    return Field(
        key=key,
        label=label,
        value=text,
        confidence=confidence,
        evidence=evidence,
        bbox=bbox,
    )
