from db import init_product_table
from uuid import uuid4

product_table = init_product_table()

EDITABLE_COLUMNS = ('name', 'slug', 'description', 'price', 'image_url',
                    'is_available', 'section', 'is_veg')

def get_product(product_id: str) -> dict:
    result = product_table.select('*').eq('id', product_id).execute()
    if result.data:
        return result.data[0]
    return None

def get_product_by_slug(slug: str) -> dict:
    result = product_table.select('*').eq('slug', slug).execute()
    if result.data:
        return result.data[0]
    return None

def get_products_by_shop(shop_id: str, available_only: bool = False) -> list:
    query = product_table.select('*').eq('shop_id', shop_id)
    if available_only:
        query = query.eq('is_available', True)
    result = query.execute()
    return result.data

def add_product(shop_id: str, name: str, slug: str, price: float, fields: dict) -> str:
    """Creates the product and returns its new id, or None if the insert failed."""
    try:
        product_id = str(uuid4())
        row = {
            'id': product_id,
            'shop_id': shop_id,
            'name': name,
            'slug': slug,
            'price': price,
            'is_available': True,
        }
        for key, value in (fields or {}).items():
            if key in EDITABLE_COLUMNS and value is not None:
                row[key] = value
        product_table.insert(row).execute()
        return product_id
    except Exception:
        return None

def update_product(product_id: str, data: dict) -> bool:
    clean = {k: v for k, v in (data or {}).items() if k in EDITABLE_COLUMNS}
    if not clean:
        return False
    try:
        product_table.update(clean).eq('id', product_id).execute()
        return True
    except Exception:
        return False

def toggle_product_availability(product_id: str, status: bool) -> bool:
    try:
        product_table.update({'is_available': status}).eq('id', product_id).execute()
        return True
    except Exception:
        return False

def remove_product(product_id: str) -> bool:
    try:
        product_table.delete().eq('id', product_id).execute()
        return True
    except Exception:
        return False

def remove_products_by_shop(shop_id: str) -> bool:
    try:
        product_table.delete().eq('shop_id', shop_id).execute()
        return True
    except Exception:
        return False
