from flask import Flask, jsonify, request
from profile import *
from shop import *
from product import *
from auth import *
from secrets import token_hex
from functools import wraps
from os import getenv
from dotenv import load_dotenv

load_dotenv('secrets.env')

zevio = Flask('zevio')
zevio.config['JSON_SORT_KEYS'] = False

API_KEY = getenv('API_KEY')

ALLOWED_USER_TYPES = ['customer', 'shop', 'delivery_person']

def response(status, data=None, code=200):
    body = {'status': status, 'csrf': token_hex(16)}
    if data is not None:
        body['data'] = data
    return jsonify(body), code

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if not key or key != API_KEY:
            return response('unauthorized', code=401)
        return f(*args, **kwargs)
    return decorated

def require_json_or_form(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated

def get_field(source, key):
    return source.get(key, '').strip() if source.get(key) else None


@zevio.route('/api/user/<string:uid>', methods=['GET'])
@require_api_key
def get_user(uid: str):
    if not is_valid_uuid(uid):
        return response('invalid uid', code=400)
    data = get_user_info(uid)
    if data:
        return response('ok', data)
    return response('user not found', code=404)


@zevio.route('/api/user/add/', methods=['POST'])
@require_api_key
def _add_user():
    body = request.form
    uid = get_field(body, 'uid')
    name = sanitize_str(get_field(body, 'name'), 100)
    phone = phone_number_validator(get_field(body, 'phone') or '')
    user_type = get_field(body, 'user_type')

    if not uid or not is_valid_uuid(uid):
        return response('invalid uid', code=400)
    if not name:
        return response('invalid name', code=400)
    if not phone:
        return response('invalid phone number', code=400)
    if user_type not in ALLOWED_USER_TYPES:
        return response('invalid user_type', code=400)

    result = add_user(uid, name, phone, user_type)
    if result is True:
        return response('ok', code=201)
    return response('failed to add user', code=500)


@zevio.route('/api/user/<string:uid>/update/', methods=['PATCH'])
@require_api_key
def _update_user(uid: str):
    if not is_valid_uuid(uid):
        return response('invalid uid', code=400)

    body = request.form
    allowed_attrs = {'name', 'phone', 'user_type'}
    attr = get_field(body, 'attr')
    attr_value = get_field(body, 'attr_value')

    if attr not in allowed_attrs:
        return response('invalid attribute', code=400)
    if attr == 'phone' and not phone_number_validator(attr_value or ''):
        return response('invalid phone number', code=400)
    if attr == 'user_type' and attr_value not in ALLOWED_USER_TYPES:
        return response('invalid user_type', code=400)
    if attr == 'name' and not sanitize_str(attr_value, 100):
        return response('invalid name', code=400)

    result = update_user(uid, attr, attr_value)
    if result:
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/user/<string:uid>/delete/', methods=['DELETE'])
@require_api_key
def _remove_user(uid: str):
    if not is_valid_uuid(uid):
        return response('invalid uid', code=400)
    result = remove_user(uid)
    if result:
        return response('ok')
    return response('delete failed', code=500)


@zevio.route('/api/shop/<string:shop_id>', methods=['GET'])
@require_api_key
def _get_shop(shop_id: str):
    if not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    data = get_shop(shop_id)
    if data:
        return response('ok', data)
    return response('shop not found', code=404)


@zevio.route('/api/shop/slug/<string:slug>', methods=['GET'])
@require_api_key
def _get_shop_by_slug(slug: str):
    if not slug_validator(slug):
        return response('invalid slug', code=400)
    data = get_shop_by_slug(slug)
    if data:
        return response('ok', data)
    return response('shop not found', code=404)


@zevio.route('/api/shops/', methods=['GET'])
@require_api_key
def _get_all_shops():
    city = request.args.get('city', '').strip() or None
    if city:
        city = sanitize_str(city, 100)
        if not city:
            return response('invalid city', code=400)
    data = get_all_shops(city)
    return response('ok', data)


@zevio.route('/api/shops/by-profile/<string:profile_id>', methods=['GET'])
@require_api_key
def _get_shops_by_profile(profile_id: str):
    if not is_valid_uuid(profile_id):
        return response('invalid profile_id', code=400)
    data = get_shops_by_profile(profile_id)
    return response('ok', data)


@zevio.route('/api/shop/add/', methods=['POST'])
@require_api_key
def _add_shop():
    body = request.form
    profile_id = get_field(body, 'profile_id')
    shop_name = sanitize_str(get_field(body, 'shop_name'), 100)
    slug = slug_validator(get_field(body, 'slug') or '')
    description = sanitize_str(get_field(body, 'description'), 1000)
    logo_url = sanitize_str(get_field(body, 'logo_url'), 500)
    cover_image_url = sanitize_str(get_field(body, 'cover_image_url'), 500)
    contact_phone = phone_number_validator(get_field(body, 'contact_phone') or '')
    contact_email = email_validator(get_field(body, 'contact_email') or '')
    address = sanitize_str(get_field(body, 'address'), 500)
    city = sanitize_str(get_field(body, 'city'), 100)

    if not profile_id or not is_valid_uuid(profile_id):
        return response('invalid profile_id', code=400)
    if not shop_name:
        return response('invalid shop_name', code=400)
    if not slug:
        return response('invalid slug (use lowercase letters, numbers and hyphens)', code=400)
    if not contact_phone:
        return response('invalid contact_phone', code=400)
    if not contact_email:
        return response('invalid contact_email', code=400)
    if not city:
        return response('invalid city', code=400)

    result = add_shop(profile_id, shop_name, slug, description,
                      logo_url, cover_image_url, contact_phone,
                      contact_email, address, city)
    if result:
        return response('ok', code=201)
    return response('failed to create shop', code=500)


@zevio.route('/api/shop/<string:shop_id>/update/', methods=['PATCH'])
@require_api_key
def _update_shop(shop_id: str):
    if not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)

    body = request.form
    allowed_attrs = {'shop_name', 'description', 'logo_url', 'cover_image_url',
                     'contact_phone', 'contact_email', 'address', 'city'}
    attr = get_field(body, 'attr')
    attr_value = get_field(body, 'attr_value')

    if attr not in allowed_attrs:
        return response('invalid attribute', code=400)
    if attr == 'contact_phone' and not phone_number_validator(attr_value or ''):
        return response('invalid phone number', code=400)
    if attr == 'contact_email' and not email_validator(attr_value or ''):
        return response('invalid email', code=400)

    result = update_shop(shop_id, {attr: attr_value})
    if result:
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/shop/<string:shop_id>/toggle-orders/', methods=['PATCH'])
@require_api_key
def _toggle_orders(shop_id: str):
    if not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    body = request.form
    raw_status = get_field(body, 'status')
    if raw_status not in ('true', 'false'):
        return response('status must be true or false', code=400)
    status = raw_status == 'true'
    result = toggle_accepting_orders(shop_id, status)
    if result:
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/shop/<string:shop_id>/delete/', methods=['DELETE'])
@require_api_key
def _remove_shop(shop_id: str):
    if not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    remove_products_by_shop(shop_id)
    result = remove_shop(shop_id)
    if result:
        return response('ok')
    return response('delete failed', code=500)


@zevio.route('/api/product/<string:product_id>', methods=['GET'])
@require_api_key
def _get_product(product_id: str):
    if not is_valid_uuid(product_id):
        return response('invalid product_id', code=400)
    data = get_product(product_id)
    if data:
        return response('ok', data)
    return response('product not found', code=404)


@zevio.route('/api/product/slug/<string:slug>', methods=['GET'])
@require_api_key
def _get_product_by_slug(slug: str):
    if not slug_validator(slug):
        return response('invalid slug', code=400)
    data = get_product_by_slug(slug)
    if data:
        return response('ok', data)
    return response('product not found', code=404)


@zevio.route('/api/products/by-shop/<string:shop_id>', methods=['GET'])
@require_api_key
def _get_products_by_shop(shop_id: str):
    if not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    available_only = request.args.get('available', 'false').lower() == 'true'
    data = get_products_by_shop(shop_id, available_only)
    return response('ok', data)


@zevio.route('/api/product/add/', methods=['POST'])
@require_api_key
def _add_product():
    body = request.form
    shop_id = get_field(body, 'shop_id')
    name = sanitize_str(get_field(body, 'name'), 200)
    slug = slug_validator(get_field(body, 'slug') or '')
    description = sanitize_str(get_field(body, 'description'), 1000)
    price = price_validator(get_field(body, 'price'))
    image_url = sanitize_str(get_field(body, 'image_url'), 500)
    is_available = get_field(body, 'is_available')

    if not shop_id or not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    if not name:
        return response('invalid name', code=400)
    if not slug:
        return response('invalid slug', code=400)
    if price is None:
        return response('invalid price', code=400)

    availability = True if is_available in (None, 'true') else False

    result = add_product(shop_id, name, slug, description, price, image_url, availability)
    if result:
        return response('ok', code=201)
    return response('failed to add product', code=500)


@zevio.route('/api/product/<string:product_id>/update/', methods=['PATCH'])
@require_api_key
def _update_product(product_id: str):
    if not is_valid_uuid(product_id):
        return response('invalid product_id', code=400)

    body = request.form
    allowed_attrs = {'name', 'description', 'price', 'image_url', 'slug'}
    attr = get_field(body, 'attr')
    attr_value = get_field(body, 'attr_value')

    if attr not in allowed_attrs:
        return response('invalid attribute', code=400)
    if attr == 'price':
        attr_value = price_validator(attr_value)
        if attr_value is None:
            return response('invalid price', code=400)
    if attr == 'slug' and not slug_validator(attr_value or ''):
        return response('invalid slug', code=400)

    result = update_product(product_id, {attr: attr_value})
    if result:
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/product/<string:product_id>/toggle-availability/', methods=['PATCH'])
@require_api_key
def _toggle_availability(product_id: str):
    if not is_valid_uuid(product_id):
        return response('invalid product_id', code=400)
    body = request.form
    raw_status = get_field(body, 'status')
    if raw_status not in ('true', 'false'):
        return response('status must be true or false', code=400)
    status = raw_status == 'true'
    result = toggle_product_availability(product_id, status)
    if result:
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/product/<string:product_id>/delete/', methods=['DELETE'])
@require_api_key
def _remove_product(product_id: str):
    if not is_valid_uuid(product_id):
        return response('invalid product_id', code=400)
    result = remove_product(product_id)
    if result:
        return response('ok')
    return response('delete failed', code=500)


@zevio.errorhandler(404)
def not_found(e):
    return response('endpoint not found', code=404)

@zevio.errorhandler(405)
def method_not_allowed(e):
    return response('method not allowed', code=405)

@zevio.errorhandler(500)
def internal_error(e):
    return response('internal server error', code=500)


if __name__ == '__main__':
    zevio.run(host='0.0.0.0', port=2222)