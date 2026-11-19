"""خطاهای دامنه — سرویس‌ها هیچ اطلاعی از HTTP ندارند؛ نگاشت به کد وضعیت در main.py انجام می‌شود."""


class DomainError(Exception):
    """پایه‌ی همه‌ی خطاهای دامنه."""


class InvalidImageError(DomainError):
    """فایل ارسالی یک تصویر قابل‌خواندن نیست."""

    def __init__(self) -> None:
        super().__init__("فایل ارسالی یک تصویر معتبر نیست یا خوانده نشد.")


class ImageTooLargeError(DomainError):
    """حجم تصویر از سقف مجاز بیشتر است."""

    def __init__(self, max_mb: int) -> None:
        super().__init__(f"حجم فایل از سقف مجاز ({max_mb} مگابایت) بیشتر است.")


class UnknownDocumentTypeError(DomainError):
    """نوع مدرک درخواستی در سامانه تعریف نشده است."""

    def __init__(self, doc_type: str) -> None:
        super().__init__(f"نوع مدرک «{doc_type}» تعریف نشده است.")


class InvalidBoxesError(DomainError, ValueError):
    """باکس‌های ارسالی برای استخراج نامعتبر یا تأییدنشده‌اند."""

    def __init__(self, detail: str = "باکس‌های فیلدها نامعتبر یا تأییدنشده‌اند.") -> None:
        super().__init__(detail)


class LlmUnavailableError(DomainError):
    """سرویس Ollama در دسترس نیست یا پاسخ نامعتبر داد."""

    def __init__(self, detail: str = "") -> None:
        message = (
            "موتور هوش مصنوعی در دسترس نیست. "
            "تنظیمات اتصال به مدل را بررسی کنید (Ollama محلی یا API خارجی)."
        )
        if detail:
            message += f" جزئیات: {detail}"
        super().__init__(message)


class ProviderConfigurationError(DomainError):
    """تنظیمات provider بینایی ناقص است."""
