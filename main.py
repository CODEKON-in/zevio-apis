from flask import Flask, jsonify, request
from profile import *
from shop import *
from product import *
from order import *
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

def get_field(source, key):
    val = source.get(key, '')
    return val.strip() if val else None


# ─── ROOT ─────────────────────────────────────────────────────────────────────

@zevio.route('/', methods=['GET'])
def index():
    return response('ok', {
        'name': 'Zevio API',
        'version': '1.0.0',
        'status': 'running',
    })


# ─── USER / PROFILE ROUTES ────────────────────────────────────────────────────

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


@zevio.route('/api/user/update/', methods=['POST'])
@require_api_key
def _update_user():
    body = request.form
    uid = get_field(body, 'uid')
    allowed_attrs = {'name', 'phone', 'user_type'}
    attr = get_field(body, 'attr')
    attr_value = get_field(body, 'attr_value')

    if not uid or not is_valid_uuid(uid):
        return response('invalid uid', code=400)
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


@zevio.route('/api/user/delete/', methods=['POST'])
@require_api_key
def _remove_user():
    body = request.form
    uid = get_field(body, 'uid')
    if not uid or not is_valid_uuid(uid):
        return response('invalid uid', code=400)
    result = remove_user(uid)
    if result:
        return response('ok')
    return response('delete failed', code=500)


# ─── SHOP ROUTES ──────────────────────────────────────────────────────────────

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


@zevio.route('/api/shop/update/', methods=['POST'])
@require_api_key
def _update_shop():
    body = request.form
    shop_id = get_field(body, 'shop_id')
    allowed_attrs = {'shop_name', 'description', 'logo_url', 'cover_image_url',
                     'contact_phone', 'contact_email', 'address', 'city'}
    attr = get_field(body, 'attr')
    attr_value = get_field(body, 'attr_value')

    if not shop_id or not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
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


@zevio.route('/api/shop/toggle-orders/', methods=['POST'])
@require_api_key
def _toggle_orders():
    body = request.form
    shop_id = get_field(body, 'shop_id')
    raw_status = get_field(body, 'status')

    if not shop_id or not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    if raw_status not in ('true', 'false'):
        return response('status must be true or false', code=400)

    result = toggle_accepting_orders(shop_id, raw_status == 'true')
    if result:
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/shop/delete/', methods=['POST'])
@require_api_key
def _remove_shop():
    body = request.form
    shop_id = get_field(body, 'shop_id')
    if not shop_id or not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    remove_products_by_shop(shop_id)
    result = remove_shop(shop_id)
    if result:
        return response('ok')
    return response('delete failed', code=500)


# ─── PRODUCT ROUTES ───────────────────────────────────────────────────────────

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


@zevio.route('/api/product/update/', methods=['POST'])
@require_api_key
def _update_product():
    body = request.form
    product_id = get_field(body, 'product_id')
    allowed_attrs = {'name', 'description', 'price', 'image_url', 'slug'}
    attr = get_field(body, 'attr')
    attr_value = get_field(body, 'attr_value')

    if not product_id or not is_valid_uuid(product_id):
        return response('invalid product_id', code=400)
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


@zevio.route('/api/product/toggle-availability/', methods=['POST'])
@require_api_key
def _toggle_availability():
    body = request.form
    product_id = get_field(body, 'product_id')
    raw_status = get_field(body, 'status')

    if not product_id or not is_valid_uuid(product_id):
        return response('invalid product_id', code=400)
    if raw_status not in ('true', 'false'):
        return response('status must be true or false', code=400)

    result = toggle_product_availability(product_id, raw_status == 'true')
    if result:
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/product/delete/', methods=['POST'])
@require_api_key
def _remove_product():
    body = request.form
    product_id = get_field(body, 'product_id')
    if not product_id or not is_valid_uuid(product_id):
        return response('invalid product_id', code=400)
    result = remove_product(product_id)
    if result:
        return response('ok')
    return response('delete failed', code=500)


# ─── ORDER ROUTES ────────────────────────────────────────────────────────────

@zevio.route('/api/order/<string:order_id>', methods=['GET'])
@require_api_key
def _get_order(order_id: str):
    if not is_valid_uuid(order_id):
        return response('invalid order_id', code=400)
    data = get_order(order_id)
    if data:
        return response('ok', data)
    return response('order not found', code=404)


@zevio.route('/api/order/number/<string:order_number>', methods=['GET'])
@require_api_key
def _get_order_by_number(order_number: str):
    order_number = order_number.strip().upper()
    if not order_number:
        return response('invalid order_number', code=400)
    data = get_order_by_number(order_number)
    if data:
        return response('ok', data)
    return response('order not found', code=404)


@zevio.route('/api/orders/by-customer/<string:customer_id>', methods=['GET'])
@require_api_key
def _get_orders_by_customer(customer_id: str):
    if not is_valid_uuid(customer_id):
        return response('invalid customer_id', code=400)
    status = request.args.get('status', '').strip() or None
    if status and status not in VALID_STATUSES:
        return response('invalid status', code=400)
    data = get_orders_by_customer(customer_id, status)
    return response('ok', data)


@zevio.route('/api/orders/by-shop/<string:shop_id>', methods=['GET'])
@require_api_key
def _get_orders_by_shop(shop_id: str):
    if not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    status = request.args.get('status', '').strip() or None
    if status and status not in VALID_STATUSES:
        return response('invalid status', code=400)
    data = get_orders_by_shop(shop_id, status)
    return response('ok', data)


@zevio.route('/api/order/<string:order_id>/items/', methods=['GET'])
@require_api_key
def _get_order_items(order_id: str):
    if not is_valid_uuid(order_id):
        return response('invalid order_id', code=400)
    data = get_order_items(order_id)
    return response('ok', data)


@zevio.route('/api/order/place/', methods=['POST'])
@require_api_key
def _place_order():
    import json
    body = request.form

    customer_id   = get_field(body, 'customer_id')
    shop_id       = get_field(body, 'shop_id')
    recipient_name  = sanitize_str(get_field(body, 'recipient_name'), 100)
    recipient_phone = phone_number_validator(get_field(body, 'recipient_phone') or '')
    delivery_address = sanitize_str(get_field(body, 'delivery_address'), 500)
    delivery_city    = sanitize_str(get_field(body, 'delivery_city'), 100)
    delivery_postal_code = sanitize_str(get_field(body, 'delivery_postal_code'), 20)
    subtotal         = price_validator(get_field(body, 'subtotal'))
    delivery_fee     = price_validator(get_field(body, 'delivery_fee') or '0')
    discount_amount  = price_validator(get_field(body, 'discount_amount') or '0')
    total_amount     = price_validator(get_field(body, 'total_amount'))
    items_raw        = get_field(body, 'items')

    if not customer_id or not is_valid_uuid(customer_id):
        return response('invalid customer_id', code=400)
    if not shop_id or not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    if not recipient_name:
        return response('invalid recipient_name', code=400)
    if not recipient_phone:
        return response('invalid recipient_phone', code=400)
    if not delivery_address:
        return response('invalid delivery_address', code=400)
    if not delivery_city:
        return response('invalid delivery_city', code=400)
    if subtotal is None:
        return response('invalid subtotal', code=400)
    if total_amount is None:
        return response('invalid total_amount', code=400)
    if not items_raw:
        return response('items are required', code=400)

    try:
        items = json.loads(items_raw)
        if not isinstance(items, list) or len(items) == 0:
            raise ValueError()
        for item in items:
            if not item.get('product_name'):
                return response('each item must have product_name', code=400)
            if price_validator(str(item.get('unit_price', ''))) is None:
                return response('each item must have valid unit_price', code=400)
            if not isinstance(item.get('quantity'), int) or item['quantity'] < 1:
                return response('each item must have valid quantity (integer >= 1)', code=400)
    except:
        return response('items must be a valid JSON array', code=400)

    result = place_order(
        customer_id, shop_id, subtotal, delivery_fee, discount_amount,
        total_amount, recipient_name, recipient_phone,
        delivery_address, delivery_city, delivery_postal_code, items
    )
    if result:
        return response('ok', result, code=201)
    return response('failed to place order', code=500)


@zevio.route('/api/order/update-status/', methods=['POST'])
@require_api_key
def _update_order_status():
    body = request.form
    order_id = get_field(body, 'order_id')
    status   = get_field(body, 'status')

    if not order_id or not is_valid_uuid(order_id):
        return response('invalid order_id', code=400)
    if status not in VALID_STATUSES:
        return response(f'invalid status. allowed: {", ".join(VALID_STATUSES)}', code=400)

    result = update_order_status(order_id, status)
    if result:
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/order/cancel/', methods=['POST'])
@require_api_key
def _cancel_order():
    body = request.form
    order_id = get_field(body, 'order_id')
    if not order_id or not is_valid_uuid(order_id):
        return response('invalid order_id', code=400)
    result = cancel_order(order_id)
    if result:
        return response('ok')
    return response('cancel failed', code=500)


@zevio.route('/api/order/delete/', methods=['POST'])
@require_api_key
def _delete_order():
    body = request.form
    order_id = get_field(body, 'order_id')
    if not order_id or not is_valid_uuid(order_id):
        return response('invalid order_id', code=400)
    result = delete_order(order_id)
    if result:
        return response('ok')
    return response('delete failed', code=500)


@zevio.route('/api/order/item/add/', methods=['POST'])
@require_api_key
def _add_order_item():
    body = request.form
    order_id     = get_field(body, 'order_id')
    product_id   = get_field(body, 'product_id')
    product_name = sanitize_str(get_field(body, 'product_name'), 200)
    unit_price   = price_validator(get_field(body, 'unit_price'))
    quantity_raw = get_field(body, 'quantity')

    if not order_id or not is_valid_uuid(order_id):
        return response('invalid order_id', code=400)
    if not product_name:
        return response('invalid product_name', code=400)
    if unit_price is None:
        return response('invalid unit_price', code=400)
    try:
        quantity = int(quantity_raw)
        if quantity < 1:
            raise ValueError()
    except:
        return response('invalid quantity (must be integer >= 1)', code=400)
    if product_id and not is_valid_uuid(product_id):
        return response('invalid product_id', code=400)

    result = add_order_item(order_id, product_id, product_name, unit_price, quantity)
    if result:
        return response('ok', code=201)
    return response('failed to add item', code=500)


@zevio.route('/api/order/item/delete/', methods=['POST'])
@require_api_key
def _delete_order_item():
    body = request.form
    item_id = get_field(body, 'item_id')
    if not item_id or not is_valid_uuid(item_id):
        return response('invalid item_id', code=400)
    result = delete_order_item(item_id)
    if result:
        return response('ok')
    return response('delete failed', code=500)


# ─── ERROR HANDLERS ───────────────────────────────────────────────────────────

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