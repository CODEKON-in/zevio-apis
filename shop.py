from db import init_shop_table
from secrets import token_hex

shop_table = init_shop_table()

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

def get_all_shops(city: str = None) -> list:
    query = shop_table.select('*')
    if city:
        query = query.eq('city', city)
    result = query.execute()
    return result.data

def add_shop(profile_id: str, shop_name: str, slug: str, description: str,
             logo_url: str, cover_image_url: str, contact_phone: str,
             contact_email: str, address: str, city: str) -> bool:
    try:
        shop_table.insert({
            'id': token_hex(8) + '-' + token_hex(4) + '-' + token_hex(4) + '-' + token_hex(4) + '-' + token_hex(12),
            'profile_id': profile_id,
            'shop_name': shop_name,
            'slug': slug,
            'description': description,
            'logo_url': logo_url,
            'cover_image_url': cover_image_url,
            'contact_phone': contact_phone,
            'contact_email': contact_email,
            'address': address,
            'city': city,
            'is_accepting_orders': True
        }).execute()
        return True
    except:
        return False

def update_shop(shop_id: str, data: dict) -> bool:
    try:
        shop_table.update(data).eq('id', shop_id).execute()
        return True
    except:
        return False

def toggle_accepting_orders(shop_id: str, status: bool) -> bool:
    try:
        shop_table.update({'is_accepting_orders': status}).eq('id', shop_id).execute()
        return True
    except:
        return False

def remove_shop(shop_id: str) -> bool:
    try:
        shop_table.delete().eq('id', shop_id).execute()
        return True
    except:
        return False
