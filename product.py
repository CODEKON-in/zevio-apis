from db import init_product_table
from secrets import token_hex

product_table = init_product_table()

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

def add_product(shop_id: str, name: str, slug: str, description: str,
                price: float, image_url: str, is_available: bool = True) -> bool:
    try:
        product_table.insert({
            'id': token_hex(8) + '-' + token_hex(4) + '-' + token_hex(4) + '-' + token_hex(4) + '-' + token_hex(12),
            'shop_id': shop_id,
            'name': name,
            'slug': slug,
            'description': description,
            'price': price,
            'image_url': image_url,
            'is_available': is_available
        }).execute()
        return True
    except:
        return False

def update_product(product_id: str, data: dict) -> bool:
    try:
        product_table.update(data).eq('id', product_id).execute()
        return True
    except:
        return False

def toggle_product_availability(product_id: str, status: bool) -> bool:
    try:
        product_table.update({'is_available': status}).eq('id', product_id).execute()
        return True
    except:
        return False

def remove_product(product_id: str) -> bool:
    try:
        product_table.delete().eq('id', product_id).execute()
        return True
    except:
        return False

def remove_products_by_shop(shop_id: str) -> bool:
    try:
        product_table.delete().eq('shop_id', shop_id).execute()
        return True
    except:
        return False
