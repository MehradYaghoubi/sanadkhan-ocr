"""تعریف فیلدهای موردانتظار هر نوع مدرک — ورودی پرامپت موتور VLM.

(key, label, hint) — hint به مدل کمک می‌کند فیلد را درست پیدا کند.
"""

from dataclasses import dataclass

from app.errors import UnknownDocumentTypeError

FIELD_SPECS: dict[str, list[tuple[str, str, str]]] = {
    "national_card": [
        ("national_id", "کد ملی", "شماره ملی ۱۰ رقمی"),
        ("first_name", "نام", "نام کوچک"),
        ("last_name", "نام خانوادگی", "نام خانوادگی"),
        ("father_name", "نام پدر", "نام پدر"),
        ("birth_date", "تاریخ تولد", "تاریخ تولد شمسی yyyy/mm/dd"),
        ("birth_place", "محل تولد", "شهر محل تولد"),
        ("serial_number", "شماره سریال", "شماره سریال پشت کارت"),
        ("expiry_date", "تاریخ انقضا", "پایان اعتبار کارت yyyy/mm/dd"),
    ],
    "birth_certificate": [
        ("national_id", "کد ملی", "شماره ملی ۱۰ رقمی (کد ملی/شماره ملی)"),
        ("certificate_number", "شماره شناسنامه", "شماره شناسنامه یا ش.ش"),
        ("certificate_serial", "سری و سریال", "سری و سریال شناسنامه (مانند 787680 / 20 د یا الف/12 345678)"),
        ("first_name", "نام", "نام کوچک"),
        ("last_name", "نام خانوادگی", "نام خانوادگی"),
        ("father_name", "نام پدر", "نام پدر"),
        ("mother_name", "نام مادر", "نام مادر، در صورت درج در سند"),
        ("birth_date", "تاریخ تولد", "تاریخ تولد شمسی yyyy/mm/dd"),
        ("birth_place", "محل تولد", "شهر محل تولد"),
        ("issue_place", "محل صدور", "شهر محل صدور"),
    ],
    "bank_card": [
        ("card_number", "شماره کارت", "شماره ۱۶ رقمی روی کارت"),
        ("iban", "شماره شبا", "شماره شبا که با IR شروع می‌شود"),
        ("expiry", "تاریخ انقضا", "تاریخ انقضا به شکل ماه/سال"),
        ("bank_name", "نام بانک", "نام بانک صادرکننده"),
        ("holder_name", "نام دارنده", "نام دارنده کارت"),
    ],
    "vehicle_document": [
        ("plate", "شماره پلاک", "پلاک ایرانی به شکل: دو رقم، یک حرف فارسی، سه رقم، ایران و دو رقم"),
        ("vin", "شناسه خودرو (VIN)", "شناسه ۱۷ کاراکتری VIN"),
        ("chassis_number", "شماره شاسی", "شماره شاسی"),
        ("engine_number", "شماره موتور", "شماره موتور"),
        ("owner_name", "نام مالک", "نام و نام خانوادگی مالک"),
        ("national_id", "کد ملی مالک", "شماره ملی ۱۰ رقمی مالک"),
        ("model", "سیستم و تیپ", "سیستم و تیپ خودرو"),
        ("model_year", "مدل (سال)", "سال مدل خودرو"),
        ("color", "رنگ", "رنگ خودرو"),
        ("fuel_type", "نوع سوخت", "بنزین/گازوئیل/دوگانه"),
    ],
    "insurance_policy": [
        ("policy_number", "شماره بیمه‌نامه", "شماره یکتای بیمه‌نامه"),
        ("insurer", "شرکت بیمه", "نام شرکت بیمه"),
        ("plate", "شماره پلاک", "پلاک خودروی بیمه‌شده"),
        ("vin", "شناسه خودرو (VIN)", "شناسه ۱۷ کاراکتری"),
        ("national_id", "کد ملی بیمه‌گذار", "شماره ملی ۱۰ رقمی بیمه‌گذار"),
        ("owner_name", "نام بیمه‌گذار", "نام و نام خانوادگی"),
        ("start_date", "تاریخ شروع", "تاریخ شروع پوشش، شمسی"),
        ("end_date", "تاریخ انقضا", "تاریخ پایان پوشش، شمسی"),
    ],
    "generic": [
        ("national_id", "کد ملی", "هر شماره ملی ۱۰ رقمی"),
        ("card_number", "شماره کارت", "هر شماره کارت ۱۶ رقمی"),
        ("iban", "شماره شبا", "شماره‌ای که با IR شروع می‌شود"),
        ("mobile", "شماره موبایل", "شماره‌ای که با 09 شروع می‌شود"),
        ("plate", "شماره پلاک", "پلاک خودروی ایرانی"),
        ("full_name", "نام و نام خانوادگی", "نام شخص"),
        ("date", "تاریخ", "مهم‌ترین تاریخ شمسی موجود"),
    ],
}


TITLES: dict[str, str] = {
    "national_card": "کارت ملی",
    "birth_certificate": "شناسنامه",
    "bank_card": "کارت بانکی",
    "vehicle_document": "سند / برگ سبز خودرو",
    "insurance_policy": "بیمه‌نامه خودرو",
    "generic": "سایر مدارک (تشخیص عمومی)",
}


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    value: str
    confidence: float | None = None
    evidence: str | None = None
    bbox: tuple[int, int, int, int] | None = None


def list_document_types() -> list[tuple[str, str]]:
    return [(doc_type, TITLES[doc_type]) for doc_type in FIELD_SPECS]


def get_title(doc_type: str) -> str:
    try:
        return TITLES[doc_type]
    except KeyError:
        raise UnknownDocumentTypeError(doc_type) from None
