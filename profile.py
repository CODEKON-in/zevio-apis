from db import init_profile_table
from uuid import uuid4

profile_table = init_profile_table()

# Columns the admin panel reads. password_hash is never selected.
PUBLIC_COLUMNS = ('id,name,phone,email,avatar_url,user_type,is_blocked,'
                  'vehicle,base_place,is_active,is_online,created_at,updated_at')

USER_TYPES = ('customer', 'shop', 'delivery_person', 'admin')

def generate_uuid() -> str:
    return str(uuid4())

def _public(row: dict) -> dict:
    """Defence in depth: the password hash must never leave the API, even if a
    caller selects '*' one day."""
    if row and 'password_hash' in row:
        return {k: v for k, v in row.items() if k != 'password_hash'}
    return row

def get_user_info(uid: str) -> dict:
    users = profile_table.select(PUBLIC_COLUMNS).eq('id', uid).execute()
    if users.data:
        return _public(users.data[0])
    return None

def get_users_by_type(user_type: str) -> list:
    """Every profile of one role, newest first — the admin customers / partners lists."""
    query = profile_table.select(PUBLIC_COLUMNS)
    if user_type:
        query = query.eq('user_type', user_type)
    return [_public(row) for row in query.order('created_at', desc=True).execute().data]

def get_user_by_email(email: str) -> dict:
    users = profile_table.select(PUBLIC_COLUMNS).ilike('email', email).execute()
    if users.data:
        return _public(users.data[0])
    return None

def get_user_by_phone(phone: str) -> dict:
    users = profile_table.select(PUBLIC_COLUMNS).eq('phone', phone).execute()
    if users.data:
        return _public(users.data[0])
    return None

def add_user(uid: str, name: str, phone: str, user_type: str, extra: dict = None) -> bool:
    try:
        row = {
            'id': uid,
            'name': name,
            'phone': phone,
            'user_type': user_type,
        }
        for key, value in (extra or {}).items():
            if value is not None:
                row[key] = value
        profile_table.insert(row).execute()
        return True
    except Exception:
        return False

def update_user(uid: str, attr: str, attr_value) -> bool:
    return update_user_fields(uid, {attr: attr_value})

def update_user_fields(uid: str, data: dict) -> bool:
    if not data:
        return False
    try:
        profile_table.update(data).eq('id', uid).execute()
        return True
    except Exception:
        return False

def remove_user(uid: str) -> bool:
    try:
        profile_table.delete().eq('id', uid).execute()
        return True
    except Exception:
        return False


# ─── admin accounts ───────────────────────────────────────────────────────────
# An admin is a profile with user_type = 'admin'. The password is stored only as
# a Werkzeug hash, and password_hash is never returned by any endpoint.

def add_admin(uid: str, name: str, email: str, phone: str, password_hash: str) -> bool:
    return add_user(uid, name, phone, 'admin',
                    {'email': email, 'password_hash': password_hash})

def get_admin_credentials(email: str) -> dict:
    """The one row the login check needs: id and the stored hash."""
    users = (profile_table
             .select('id,password_hash')
             .ilike('email', email)
             .eq('user_type', 'admin')
             .execute())
    if users.data:
        return users.data[0]
    return None

def count_admins() -> int:
    return len(profile_table.select('id').eq('user_type', 'admin').execute().data or [])
