import re

def phone_number_validator(phone: str):
    phone = phone.strip()
    if isinstance(phone, str) and len(phone) == 10 and phone.isdigit():
        return phone
    return None

def email_validator(email: str):
    email = email.strip().lower()
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    if re.match(pattern, email):
        return email
    return None

def slug_validator(slug: str):
    slug = slug.strip().lower()
    pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
    if re.match(pattern, slug) and 2 <= len(slug) <= 100:
        return slug
    return None

def price_validator(price):
    try:
        price = float(price)
        if price >= 0:
            return price
        return None
    except:
        return None

def sanitize_str(value: str, max_len: int = 255) -> str:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if len(value) == 0 or len(value) > max_len:
        return None
    return value

def is_valid_uuid(uid: str) -> bool:
    uid = uid.strip()
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uid, re.IGNORECASE))
