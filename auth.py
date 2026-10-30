import re
from datetime import date
from werkzeug.security import check_password_hash, generate_password_hash

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

def time_validator(value: str):
    """'HH:MM' or 'HH:MM:SS' → 'HH:MM:SS' for a Postgres time column."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not re.match(r'^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$', value):
        return None
    return value if len(value) == 8 else value + ':00'

def date_validator(value: str):
    """'YYYY-MM-DD', checked against the calendar."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
        return None
    try:
        date.fromisoformat(value)
        return value
    except ValueError:
        return None

def bool_validator(value):
    """Form fields arrive as text: 'true'/'false' → True/False, anything else None."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in ('true', 'false'):
        return value.strip().lower() == 'true'
    return None

def password_validator(password: str):
    """At least 8 characters. Returned unchanged — only ever stored hashed."""
    if not isinstance(password, str) or not 8 <= len(password) <= 200:
        return None
    return password

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    if not password_hash or not password:
        return False
    try:
        return check_password_hash(password_hash, password)
    except (ValueError, TypeError):
        return False
