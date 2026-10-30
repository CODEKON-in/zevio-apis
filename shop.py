from db import init_shop_table
from uuid import uuid4

shop_table = init_shop_table()

# Columns the admin / shop panel may set. Kept in one place so the add and
# update endpoints accept exactly the same set.
EDITABLE_COLUMNS = (
    'shop_name', 'description', 'logo_url', 'cover_image_url',
    'contact_phone', 'contact_email', 'address', 'city', 'postal_code',
    'category', 'owner_name', 'upi_id', 'open_time', 'close_time',
    'delivery_time', 'is_active',
    'subscription_plan', 'subscription_status', 'subscription_start', 'subscription_end',
)

def get_shop(shop_id: str) -> dict:
    result = shop_table.select('*').eq('id', shop_id).execute()
    if result.data:
        return result.data[0]
    return None

def get_shop_by_slug(slug: str) -> dict:
    result = shop_table.select('*').eq('slug', slug).execute()
    if result.data:
        return result.data[0]
    return None

def get_shops_by_profile(profile_id: str) -> list:
    result = shop_table.select('*').eq('profile_id', profile_id).execute()
    return result.data

def get_all_shops(city: str = None, active_only: bool = False) -> list:
    query = shop_table.select('*')
    if city:
        query = query.eq('city', city)
    if active_only:
        query = query.eq('is_active', True)
    result = query.execute()
    return result.data

def add_shop(profile_id: str, shop_name: str, slug: str, fields: dict) -> str:
    """Creates the shop and returns its new id, or None if the insert failed."""
    try:
        shop_id = str(uuid4())
        row = {
            'id': shop_id,
            'profile_id': profile_id,
            'shop_name': shop_name,
            'slug': slug,
            'is_accepting_orders': False,
        }
        for key, value in (fields or {}).items():
            if key in EDITABLE_COLUMNS and value is not None:
                row[key] = value
        shop_table.insert(row).execute()
        return shop_id
    except Exception:
        return None

def update_shop(shop_id: str, data: dict) -> bool:
    clean = {k: v for k, v in (data or {}).items() if k in EDITABLE_COLUMNS}
    if not clean:
        return False
    try:
        shop_table.update(clean).eq('id', shop_id).execute()
        return True
    except Exception:
        return False

def toggle_accepting_orders(shop_id: str, status: bool) -> bool:
    try:
        shop_table.update({'is_accepting_orders': status}).eq('id', shop_id).execute()
        return True
    except Exception:
        return False

def set_shop_active(shop_id: str, status: bool) -> bool:
    """Admin's activate / deactivate — a deactivated shop is hidden from customers."""
    try:
        shop_table.update({'is_active': status}).eq('id', shop_id).execute()
        return True
    except Exception:
        return False

def rename_city(old_name: str, new_name: str) -> bool:
    """Shops record their place by name, so renaming a service place has to
    follow through or those shops are left pointing at a place that is gone."""
    try:
        shop_table.update({'city': new_name}).eq('city', old_name).execute()
        return True
    except Exception:
        return False

def remove_shop(shop_id: str) -> bool:
    try:
        shop_table.delete().eq('id', shop_id).execute()
        return True
    except Exception:
        return False
