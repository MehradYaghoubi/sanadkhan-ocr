"""اعتبارسنجی‌های محلی: کد ملی ایران (الگوریتم رسمی) و شماره کارت بانکی (Luhn)."""


def is_valid_national_id(code: str) -> bool:
    """اعتبارسنجی کد ملی ۱۰ رقمی با الگوریتم رقم کنترل."""
    if len(code) != 10 or not code.isdigit():
        return False
    if code == code[0] * 10:  # مثل 1111111111 معتبر نیست
        return False

    check_digit = int(code[9])
    total = sum(int(code[i]) * (10 - i) for i in range(9))
    remainder = total % 11

    if remainder < 2:
        return check_digit == remainder
    return check_digit == 11 - remainder


def is_valid_card_number(number: str) -> bool:
    """اعتبارسنجی شماره کارت ۱۶ رقمی با الگوریتم Luhn."""
    if len(number) != 16 or not number.isdigit():
        return False

    total = 0
    for index, char in enumerate(number):
        digit = int(char)
        if index % 2 == 0:  # ارقام با اندیس زوج (از چپ) دو برابر می‌شوند
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0
