"""نرمال‌سازی متن خروجی OCR: ارقام فارسی/عربی → لاتین، یکسان‌سازی حروف عربی/فارسی."""

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ASCII_DIGITS = "0123456789"

_DIGIT_TABLE = str.maketrans(
    PERSIAN_DIGITS + ARABIC_DIGITS,
    ASCII_DIGITS + ASCII_DIGITS,
)

_CHAR_TABLE = str.maketrans(
    {
        "ي": "ی",
        "ك": "ک",
        "ة": "ه",
        "ۀ": "ه",
        "ؤ": "و",
        "إ": "ا",
        "أ": "ا",
        "\u0640": None,  # کشیده (tatweel)
        "\u200c": " ",   # نیم‌فاصله → فاصله (برای تطبیق برچسب‌ها)
        "\u200f": None,
        "\u200e": None,
    }
)


def normalize_digits(text: str) -> str:
    """تبدیل ارقام فارسی و عربی به ارقام لاتین."""
    return text.translate(_DIGIT_TABLE)


def normalize_text(text: str) -> str:
    """نرمال‌سازی کامل: ارقام + حروف + فشرده‌سازی فاصله‌ها."""
    normalized = normalize_digits(text).translate(_CHAR_TABLE)
    return " ".join(normalized.split())
