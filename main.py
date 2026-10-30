from flask import Flask, jsonify, request
from secrets import token_hex
from functools import wraps
from os import getenv
from dotenv import load_dotenv

# Explicit module imports: shop, product and settings each define their own
# EDITABLE_COLUMNS, so `import *` would silently overwrite one with another.
import profile as profiles
import shop as shops
import product as products
import order as orders
import settings as platform
from order import VALID_STATUSES
from auth import (bool_validator, date_validator, email_validator, hash_password,
                  is_valid_uuid, password_validator, phone_number_validator,
                  price_validator, sanitize_str, slug_validator, time_validator,
                  verify_password)

load_dotenv('secrets.env')
load_dotenv()

zevio = Flask('zevio')
app = zevio
zevio.config['JSON_SORT_KEYS'] = False

API_KEY = getenv('API_KEY')

ALLOWED_USER_TYPES = ['customer', 'shop', 'delivery_person']
SHOP_CATEGORIES = ['hotels', 'bakery']
SUBSCRIPTION_STATUSES = ['TRIAL', 'ACTIVE', 'EXPIRED']
PAYMENT_METHODS = ['UPI', 'COD']

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

def present(key):
    """True when the form sent this field at all (so '' can mean 'clear it')."""
    return key in request.form


# ─── ROOT ─────────────────────────────────────────────────────────────────────

@zevio.route('/', methods=['GET'])
def index():
    return response('ok', {
        'name': 'Zevio API',
        'version': '1.1.0',
        'status': 'running',
    })


# ─── USER / PROFILE ROUTES ────────────────────────────────────────────────────

@zevio.route('/api/user/<string:uid>', methods=['GET'])
@require_api_key
def get_user(uid: str):
    if not is_valid_uuid(uid):
        return response('invalid uid', code=400)
    data = profiles.get_user_info(uid)
    if data:
        return response('ok', data)
    return response('user not found', code=404)


@zevio.route('/api/users/', methods=['GET'])
@require_api_key
def _get_users():
    """All profiles of one role — the admin customers and partners lists."""
    user_type = request.args.get('user_type', '').strip() or None
    if user_type and user_type not in profiles.USER_TYPES:
        return response('invalid user_type', code=400)
    return response('ok', profiles.get_users_by_type(user_type))


@zevio.route('/api/user/by-phone/<string:phone>', methods=['GET'])
@require_api_key
def _get_user_by_phone(phone: str):
    phone = phone_number_validator(phone or '')
    if not phone:
        return response('invalid phone number', code=400)
    data = profiles.get_user_by_phone(phone)
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

    extra = {}
    if present('email'):
        email = email_validator(get_field(body, 'email') or '')
        if not email:
            return response('invalid email', code=400)
        extra['email'] = email
    # Delivery-partner details.
    if present('vehicle'):
        extra['vehicle'] = sanitize_str(get_field(body, 'vehicle'), 30)
    if present('base_place'):
        extra['base_place'] = sanitize_str(get_field(body, 'base_place'), 100)
    for flag in ('is_active', 'is_online'):
        if present(flag):
            value = bool_validator(get_field(body, flag))
            if value is None:
                return response(f'{flag} must be true or false', code=400)
            extra[flag] = value

    if profiles.add_user(uid, name, phone, user_type, extra):
        return response('ok', {'id': uid}, code=201)
    return response('failed to add user', code=500)


@zevio.route('/api/user/update/', methods=['POST'])
@require_api_key
def _update_user():
    body = request.form
    uid = get_field(body, 'uid')
    attr = get_field(body, 'attr')
    attr_value = get_field(body, 'attr_value')

    allowed_attrs = {'name', 'phone', 'user_type', 'email', 'avatar_url',
                     'is_blocked', 'vehicle', 'base_place', 'is_active', 'is_online'}

    if not uid or not is_valid_uuid(uid):
        return response('invalid uid', code=400)
    if attr not in allowed_attrs:
        return response('invalid attribute', code=400)

    if attr == 'phone':
        attr_value = phone_number_validator(attr_value or '')
        if not attr_value:
            return response('invalid phone number', code=400)
    elif attr == 'email':
        attr_value = email_validator(attr_value or '')
        if not attr_value:
            return response('invalid email', code=400)
    elif attr == 'user_type':
        if attr_value not in ALLOWED_USER_TYPES:
            return response('invalid user_type', code=400)
    elif attr == 'name':
        attr_value = sanitize_str(attr_value, 100)
        if not attr_value:
            return response('invalid name', code=400)
    elif attr in ('is_blocked', 'is_active', 'is_online'):
        attr_value = bool_validator(attr_value)
        if attr_value is None:
            return response(f'{attr} must be true or false', code=400)
    elif attr == 'vehicle':
        attr_value = sanitize_str(attr_value, 30)
    elif attr == 'base_place':
        attr_value = sanitize_str(attr_value, 100)
    elif attr == 'avatar_url':
        attr_value = sanitize_str(attr_value, 500)

    if not profiles.get_user_info(uid):
        return response('user not found', code=404)
    if profiles.update_user(uid, attr, attr_value):
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/user/delete/', methods=['POST'])
@require_api_key
def _remove_user():
    body = request.form
    uid = get_field(body, 'uid')
    if not uid or not is_valid_uuid(uid):
        return response('invalid uid', code=400)
    if not profiles.get_user_info(uid):
        return response('user not found', code=404)
    if profiles.remove_user(uid):
        return response('ok')
    return response('delete failed', code=500)


# ─── ADMIN ACCOUNTS ───────────────────────────────────────────────────────────

@zevio.route('/api/admin/add/', methods=['POST'])
@require_api_key
def _add_admin():
    """Create an admin. Guarded by the API key, so only the server owner can
    call it — use it once to make the first admin."""
    body = request.form
    name = sanitize_str(get_field(body, 'name'), 100)
    email = email_validator(get_field(body, 'email') or '')
    phone = phone_number_validator(get_field(body, 'phone') or '')
    password = password_validator(get_field(body, 'password') or '')

    if not name:
        return response('invalid name', code=400)
    if not email:
        return response('invalid email', code=400)
    if not phone:
        return response('invalid phone number', code=400)
    if not password:
        return response('password must be at least 8 characters', code=400)
    if profiles.get_user_by_email(email):
        return response('email already in use', code=409)

    uid = profiles.generate_uuid()
    if profiles.add_admin(uid, name, email, phone, hash_password(password)):
        return response('ok', {'id': uid}, code=201)
    return response('failed to add admin', code=500)


@zevio.route('/api/auth/admin', methods=['POST'])
@require_api_key
def _admin_login():
    body = request.form
    email = email_validator(get_field(body, 'email') or '')
    password = get_field(body, 'password')

    if not email or not password:
        return response('invalid credentials', code=401)

    record = profiles.get_admin_credentials(email)
    if not record or not verify_password(record.get('password_hash'), password):
        return response('invalid credentials', code=401)

    data = profiles.get_user_info(record['id'])
    if not data:
        return response('invalid credentials', code=401)
    return response('ok', data)


# ─── SHOP ROUTES ──────────────────────────────────────────────────────────────

def _shop_fields(body, creating: bool):
    """Reads the shop columns from the form. Returns (fields, error_message)."""
    fields = {}

    def text(key, column, max_len):
        if creating or present(key):
            fields[column] = sanitize_str(get_field(body, key), max_len)

    text('shop_name', 'shop_name', 100)
    text('description', 'description', 1000)
    text('logo_url', 'logo_url', 500)
    text('cover_image_url', 'cover_image_url', 500)
    text('address', 'address', 500)
    text('city', 'city', 100)
    text('postal_code', 'postal_code', 10)
    text('owner_name', 'owner_name', 150)
    text('upi_id', 'upi_id', 100)
    text('delivery_time', 'delivery_time', 20)
    text('subscription_plan', 'subscription_plan', 100)

    if creating or present('contact_phone'):
        phone = phone_number_validator(get_field(body, 'contact_phone') or '')
        if not phone:
            return None, 'invalid contact_phone'
        fields['contact_phone'] = phone

    if creating or present('contact_email'):
        email = email_validator(get_field(body, 'contact_email') or '')
        if not email:
            return None, 'invalid contact_email'
        fields['contact_email'] = email

    if present('category'):
        category = get_field(body, 'category')
        if category not in SHOP_CATEGORIES:
            return None, 'invalid category'
        fields['category'] = category

    for key in ('open_time', 'close_time'):
        if present(key):
            value = time_validator(get_field(body, key) or '')
            if not value:
                return None, f'invalid {key} (use HH:MM)'
            fields[key] = value

    if present('is_active'):
        value = bool_validator(get_field(body, 'is_active'))
        if value is None:
            return None, 'is_active must be true or false'
        fields['is_active'] = value

    if present('subscription_status'):
        value = get_field(body, 'subscription_status')
        if value and value not in SUBSCRIPTION_STATUSES:
            return None, 'invalid subscription_status'
        fields['subscription_status'] = value

    for key in ('subscription_start', 'subscription_end'):
        if present(key):
            raw = get_field(body, key)
            if raw:
                value = date_validator(raw)
                if not value:
                    return None, f'invalid {key} (use YYYY-MM-DD)'
                fields[key] = value
            else:
                fields[key] = None

    return fields, None


@zevio.route('/api/shop/<string:shop_id>', methods=['GET'])
@require_api_key
def _get_shop(shop_id: str):
    if not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    data = shops.get_shop(shop_id)
    if data:
        return response('ok', data)
    return response('shop not found', code=404)


@zevio.route('/api/shop/slug/<string:slug>', methods=['GET'])
@require_api_key
def _get_shop_by_slug(slug: str):
    if not slug_validator(slug):
        return response('invalid slug', code=400)
    data = shops.get_shop_by_slug(slug)
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
    active_only = request.args.get('active', 'false').lower() == 'true'
    return response('ok', shops.get_all_shops(city, active_only))


@zevio.route('/api/shops/by-profile/<string:profile_id>', methods=['GET'])
@require_api_key
def _get_shops_by_profile(profile_id: str):
    if not is_valid_uuid(profile_id):
        return response('invalid profile_id', code=400)
    return response('ok', shops.get_shops_by_profile(profile_id))


@zevio.route('/api/shop/add/', methods=['POST'])
@require_api_key
def _add_shop():
    body = request.form
    profile_id = get_field(body, 'profile_id')
    slug = slug_validator(get_field(body, 'slug') or '')

    if not profile_id or not is_valid_uuid(profile_id):
        return response('invalid profile_id', code=400)
    if not slug:
        return response('invalid slug (use lowercase letters, numbers and hyphens)', code=400)

    fields, error = _shop_fields(body, creating=True)
    if error:
        return response(error, code=400)
    if not fields.get('shop_name'):
        return response('invalid shop_name', code=400)
    if not fields.get('address'):
        return response('invalid address', code=400)
    if not fields.get('city'):
        return response('invalid city', code=400)

    shop_name = fields.pop('shop_name')
    new_id = shops.add_shop(profile_id, shop_name, slug, fields)
    if new_id:
        return response('ok', {'id': new_id}, code=201)
    return response('failed to create shop', code=500)


@zevio.route('/api/shop/update/', methods=['POST'])
@require_api_key
def _update_shop():
    """Accepts either one attr/attr_value pair or any number of columns at once."""
    body = request.form
    shop_id = get_field(body, 'shop_id')
    if not shop_id or not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    if not shops.get_shop(shop_id):
        return response('shop not found', code=404)

    attr = get_field(body, 'attr')
    if attr:
        if attr not in shops.EDITABLE_COLUMNS:
            return response('invalid attribute', code=400)
        attr_value = get_field(body, 'attr_value')
        if attr == 'contact_phone':
            attr_value = phone_number_validator(attr_value or '')
            if not attr_value:
                return response('invalid phone number', code=400)
        elif attr == 'contact_email':
            attr_value = email_validator(attr_value or '')
            if not attr_value:
                return response('invalid email', code=400)
        elif attr == 'category' and attr_value not in SHOP_CATEGORIES:
            return response('invalid category', code=400)
        elif attr in ('open_time', 'close_time'):
            attr_value = time_validator(attr_value or '')
            if not attr_value:
                return response(f'invalid {attr} (use HH:MM)', code=400)
        elif attr in ('subscription_start', 'subscription_end'):
            attr_value = date_validator(attr_value or '')
            if not attr_value:
                return response(f'invalid {attr} (use YYYY-MM-DD)', code=400)
        elif attr == 'subscription_status' and attr_value not in SUBSCRIPTION_STATUSES:
            return response('invalid subscription_status', code=400)
        elif attr == 'is_active':
            attr_value = bool_validator(attr_value)
            if attr_value is None:
                return response('is_active must be true or false', code=400)
        else:
            attr_value = sanitize_str(attr_value, 1000)
            if attr_value is None:
                return response(f'invalid {attr}', code=400)
        if shops.update_shop(shop_id, {attr: attr_value}):
            return response('ok')
        return response('update failed', code=500)

    fields, error = _shop_fields(body, creating=False)
    if error:
        return response(error, code=400)
    if not fields:
        return response('nothing to update', code=400)
    if shops.update_shop(shop_id, fields):
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/shop/toggle-orders/', methods=['POST'])
@require_api_key
def _toggle_orders():
    body = request.form
    shop_id = get_field(body, 'shop_id')
    status = bool_validator(get_field(body, 'status'))

    if not shop_id or not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    if status is None:
        return response('status must be true or false', code=400)
    if not shops.get_shop(shop_id):
        return response('shop not found', code=404)
    if shops.toggle_accepting_orders(shop_id, status):
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/shop/set-active/', methods=['POST'])
@require_api_key
def _set_shop_active():
    """Admin activate / deactivate — hides the shop from customers entirely."""
    body = request.form
    shop_id = get_field(body, 'shop_id')
    status = bool_validator(get_field(body, 'status'))

    if not shop_id or not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    if status is None:
        return response('status must be true or false', code=400)
    if not shops.get_shop(shop_id):
        return response('shop not found', code=404)
    if shops.set_shop_active(shop_id, status):
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/shop/delete/', methods=['POST'])
@require_api_key
def _remove_shop():
    body = request.form
    shop_id = get_field(body, 'shop_id')
    if not shop_id or not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    if not shops.get_shop(shop_id):
        return response('shop not found', code=404)
    products.remove_products_by_shop(shop_id)
    if shops.remove_shop(shop_id):
        return response('ok')
    return response('delete failed', code=500)


# ─── PRODUCT ROUTES ───────────────────────────────────────────────────────────

def _product_fields(body, creating: bool):
    fields = {}

    def text(key, column, max_len):
        if creating or present(key):
            fields[column] = sanitize_str(get_field(body, key), max_len)

    text('name', 'name', 200)
    text('description', 'description', 1000)
    text('image_url', 'image_url', 500)
    text('section', 'section', 100)

    if present('price'):
        price = price_validator(get_field(body, 'price'))
        if price is None:
            return None, 'invalid price'
        fields['price'] = price

    if present('is_available'):
        value = bool_validator(get_field(body, 'is_available'))
        if value is None:
            return None, 'is_available must be true or false'
        fields['is_available'] = value

    if present('is_veg'):
        raw = get_field(body, 'is_veg')
        if raw:
            value = bool_validator(raw)
            if value is None:
                return None, 'is_veg must be true or false'
            fields['is_veg'] = value
        else:
            fields['is_veg'] = None

    return fields, None


@zevio.route('/api/product/<string:product_id>', methods=['GET'])
@require_api_key
def _get_product(product_id: str):
    if not is_valid_uuid(product_id):
        return response('invalid product_id', code=400)
    data = products.get_product(product_id)
    if data:
        return response('ok', data)
    return response('product not found', code=404)


@zevio.route('/api/product/slug/<string:slug>', methods=['GET'])
@require_api_key
def _get_product_by_slug(slug: str):
    if not slug_validator(slug):
        return response('invalid slug', code=400)
    data = products.get_product_by_slug(slug)
    if data:
        return response('ok', data)
    return response('product not found', code=404)


@zevio.route('/api/products/by-shop/<string:shop_id>', methods=['GET'])
@require_api_key
def _get_products_by_shop(shop_id: str):
    if not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    available_only = request.args.get('available', 'false').lower() == 'true'
    return response('ok', products.get_products_by_shop(shop_id, available_only))


@zevio.route('/api/product/add/', methods=['POST'])
@require_api_key
def _add_product():
    body = request.form
    shop_id = get_field(body, 'shop_id')
    slug = slug_validator(get_field(body, 'slug') or '')
    price = price_validator(get_field(body, 'price'))

    if not shop_id or not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    if not slug:
        return response('invalid slug', code=400)
    if price is None:
        return response('invalid price', code=400)

    fields, error = _product_fields(body, creating=True)
    if error:
        return response(error, code=400)
    if not fields.get('name'):
        return response('invalid name', code=400)

    name = fields.pop('name')
    fields.pop('price', None)
    new_id = products.add_product(shop_id, name, slug, price, fields)
    if new_id:
        return response('ok', {'id': new_id}, code=201)
    return response('failed to add product', code=500)


@zevio.route('/api/product/update/', methods=['POST'])
@require_api_key
def _update_product():
    body = request.form
    product_id = get_field(body, 'product_id')
    if not product_id or not is_valid_uuid(product_id):
        return response('invalid product_id', code=400)
    if not products.get_product(product_id):
        return response('product not found', code=404)

    attr = get_field(body, 'attr')
    if attr:
        if attr not in products.EDITABLE_COLUMNS:
            return response('invalid attribute', code=400)
        attr_value = get_field(body, 'attr_value')
        if attr == 'price':
            attr_value = price_validator(attr_value)
            if attr_value is None:
                return response('invalid price', code=400)
        elif attr == 'slug':
            attr_value = slug_validator(attr_value or '')
            if not attr_value:
                return response('invalid slug', code=400)
        elif attr in ('is_available', 'is_veg'):
            attr_value = bool_validator(attr_value)
            if attr_value is None:
                return response(f'{attr} must be true or false', code=400)
        else:
            attr_value = sanitize_str(attr_value, 1000)
            if attr_value is None:
                return response(f'invalid {attr}', code=400)
        if products.update_product(product_id, {attr: attr_value}):
            return response('ok')
        return response('update failed', code=500)

    fields, error = _product_fields(body, creating=False)
    if error:
        return response(error, code=400)
    if not fields:
        return response('nothing to update', code=400)
    if products.update_product(product_id, fields):
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/product/toggle-availability/', methods=['POST'])
@require_api_key
def _toggle_availability():
    body = request.form
    product_id = get_field(body, 'product_id')
    status = bool_validator(get_field(body, 'status'))

    if not product_id or not is_valid_uuid(product_id):
        return response('invalid product_id', code=400)
    if status is None:
        return response('status must be true or false', code=400)
    if not products.get_product(product_id):
        return response('product not found', code=404)
    if products.toggle_product_availability(product_id, status):
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/product/delete/', methods=['POST'])
@require_api_key
def _remove_product():
    body = request.form
    product_id = get_field(body, 'product_id')
    if not product_id or not is_valid_uuid(product_id):
        return response('invalid product_id', code=400)
    if not products.get_product(product_id):
        return response('product not found', code=404)
    if products.remove_product(product_id):
        return response('ok')
    return response('delete failed', code=500)


# ─── ORDER ROUTES ────────────────────────────────────────────────────────────

@zevio.route('/api/order/<string:order_id>', methods=['GET'])
@require_api_key
def _get_order(order_id: str):
    if not is_valid_uuid(order_id):
        return response('invalid order_id', code=400)
    data = orders.get_order(order_id)
    if data:
        return response('ok', data)
    return response('order not found', code=404)


@zevio.route('/api/order/number/<string:order_number>', methods=['GET'])
@require_api_key
def _get_order_by_number(order_number: str):
    order_number = order_number.strip().upper()
    if not order_number:
        return response('invalid order_number', code=400)
    data = orders.get_order_by_number(order_number)
    if data:
        return response('ok', data)
    return response('order not found', code=404)


@zevio.route('/api/orders/', methods=['GET'])
@require_api_key
def _get_all_orders():
    """Every order — the admin orders list and dashboard, in one call."""
    status = request.args.get('status', '').strip() or None
    date = request.args.get('date', '').strip() or None
    if status and status not in VALID_STATUSES:
        return response('invalid status', code=400)
    if date and not date_validator(date):
        return response('invalid date (use YYYY-MM-DD)', code=400)
    return response('ok', orders.get_all_orders(status, date))


@zevio.route('/api/orders/by-customer/<string:customer_id>', methods=['GET'])
@require_api_key
def _get_orders_by_customer(customer_id: str):
    if not is_valid_uuid(customer_id):
        return response('invalid customer_id', code=400)
    status = request.args.get('status', '').strip() or None
    if status and status not in VALID_STATUSES:
        return response('invalid status', code=400)
    return response('ok', orders.get_orders_by_customer(customer_id, status))


@zevio.route('/api/orders/by-shop/<string:shop_id>', methods=['GET'])
@require_api_key
def _get_orders_by_shop(shop_id: str):
    if not is_valid_uuid(shop_id):
        return response('invalid shop_id', code=400)
    status = request.args.get('status', '').strip() or None
    if status and status not in VALID_STATUSES:
        return response('invalid status', code=400)
    return response('ok', orders.get_orders_by_shop(shop_id, status))


@zevio.route('/api/orders/by-partner/<string:partner_id>', methods=['GET'])
@require_api_key
def _get_orders_by_partner(partner_id: str):
    if not is_valid_uuid(partner_id):
        return response('invalid partner_id', code=400)
    status = request.args.get('status', '').strip() or None
    if status and status not in VALID_STATUSES:
        return response('invalid status', code=400)
    return response('ok', orders.get_orders_by_partner(partner_id, status))


@zevio.route('/api/order/<string:order_id>/items/', methods=['GET'])
@require_api_key
def _get_order_items(order_id: str):
    if not is_valid_uuid(order_id):
        return response('invalid order_id', code=400)
    return response('ok', orders.get_order_items(order_id))


@zevio.route('/api/order/items/', methods=['GET'])
@require_api_key
def _get_items_for_orders():
    """Line items for many orders at once: ?order_ids=<uuid>,<uuid>,…"""
    raw = request.args.get('order_ids', '').strip()
    if not raw:
        return response('order_ids are required', code=400)
    order_ids = [x.strip() for x in raw.split(',') if x.strip()]
    if not order_ids or len(order_ids) > 200:
        return response('send between 1 and 200 order_ids', code=400)
    for oid in order_ids:
        if not is_valid_uuid(oid):
            return response('invalid order_id in order_ids', code=400)
    return response('ok', orders.get_items_for_orders(order_ids))


@zevio.route('/api/order/place/', methods=['POST'])
@require_api_key
def _place_order():
    import json
    body = request.form

    customer_id = get_field(body, 'customer_id')
    shop_id = get_field(body, 'shop_id')
    recipient_name = sanitize_str(get_field(body, 'recipient_name'), 100)
    recipient_phone = phone_number_validator(get_field(body, 'recipient_phone') or '')
    delivery_address = sanitize_str(get_field(body, 'delivery_address'), 500)
    delivery_city = sanitize_str(get_field(body, 'delivery_city'), 100)
    delivery_postal_code = sanitize_str(get_field(body, 'delivery_postal_code'), 20)
    subtotal = price_validator(get_field(body, 'subtotal'))
    delivery_fee = price_validator(get_field(body, 'delivery_fee') or '0')
    discount_amount = price_validator(get_field(body, 'discount_amount') or '0')
    total_amount = price_validator(get_field(body, 'total_amount'))
    items_raw = get_field(body, 'items')

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

    payment_method = get_field(body, 'payment_method') or 'COD'
    if payment_method not in PAYMENT_METHODS:
        return response('invalid payment_method', code=400)

    extra = {
        'payment_method': payment_method,
        # UPI is collected before the order is placed; cash is collected on delivery.
        'payment_status': 'PAID' if payment_method == 'UPI' else 'PENDING',
        'landmark': sanitize_str(get_field(body, 'landmark'), 200),
        'directions': sanitize_str(get_field(body, 'directions'), 200),
        'instructions': sanitize_str(get_field(body, 'instructions'), 200),
    }

    try:
        items = json.loads(items_raw)
    except (ValueError, TypeError):
        return response('items must be a valid JSON array', code=400)
    if not isinstance(items, list) or len(items) == 0:
        return response('items must be a non-empty JSON array', code=400)
    for item in items:
        if not isinstance(item, dict):
            return response('each item must be an object', code=400)
        if not item.get('product_name'):
            return response('each item must have product_name', code=400)
        if price_validator(item.get('unit_price')) is None:
            return response('each item must have valid unit_price', code=400)
        quantity = item.get('quantity')
        # bool is an int in Python: quantity=true must not pass as 1.
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            return response('each item must have valid quantity (integer >= 1)', code=400)
        if item.get('product_id') and not is_valid_uuid(str(item['product_id'])):
            return response('invalid product_id in items', code=400)

    result = orders.place_order(
        customer_id, shop_id, subtotal, delivery_fee, discount_amount,
        total_amount, recipient_name, recipient_phone,
        delivery_address, delivery_city, delivery_postal_code, items, extra,
    )
    if result:
        return response('ok', result, code=201)
    return response('failed to place order', code=500)


@zevio.route('/api/order/update-status/', methods=['POST'])
@require_api_key
def _update_order_status():
    body = request.form
    order_id = get_field(body, 'order_id')
    status = get_field(body, 'status')
    reject_reason = sanitize_str(get_field(body, 'reject_reason'), 200)

    if not order_id or not is_valid_uuid(order_id):
        return response('invalid order_id', code=400)
    if status not in VALID_STATUSES:
        return response(f'invalid status. allowed: {", ".join(VALID_STATUSES)}', code=400)
    if not orders.get_order(order_id):
        return response('order not found', code=404)
    if orders.update_order_status(order_id, status, reject_reason):
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/order/cancel/', methods=['POST'])
@require_api_key
def _cancel_order():
    body = request.form
    order_id = get_field(body, 'order_id')
    reject_reason = sanitize_str(get_field(body, 'reject_reason'), 200)
    if not order_id or not is_valid_uuid(order_id):
        return response('invalid order_id', code=400)
    if not orders.get_order(order_id):
        return response('order not found', code=404)
    if orders.cancel_order(order_id, reject_reason):
        return response('ok')
    return response('cancel failed', code=500)


@zevio.route('/api/order/assign-partner/', methods=['POST'])
@require_api_key
def _assign_partner():
    """Assign a delivery partner, or send an empty partner_id to unassign."""
    body = request.form
    order_id = get_field(body, 'order_id')
    partner_id = get_field(body, 'partner_id')

    if not order_id or not is_valid_uuid(order_id):
        return response('invalid order_id', code=400)
    if not orders.get_order(order_id):
        return response('order not found', code=404)
    if partner_id:
        if not is_valid_uuid(partner_id):
            return response('invalid partner_id', code=400)
        partner = profiles.get_user_info(partner_id)
        if not partner:
            return response('partner not found', code=404)
        if partner.get('user_type') != 'delivery_person':
            return response('partner_id is not a delivery partner', code=400)
    if orders.assign_partner(order_id, partner_id or None):
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/order/mark-paid/', methods=['POST'])
@require_api_key
def _mark_order_paid():
    body = request.form
    order_id = get_field(body, 'order_id')
    if not order_id or not is_valid_uuid(order_id):
        return response('invalid order_id', code=400)
    if not orders.get_order(order_id):
        return response('order not found', code=404)
    if orders.mark_order_paid(order_id):
        return response('ok')
    return response('update failed', code=500)


@zevio.route('/api/order/delete/', methods=['POST'])
@require_api_key
def _delete_order():
    body = request.form
    order_id = get_field(body, 'order_id')
    if not order_id or not is_valid_uuid(order_id):
        return response('invalid order_id', code=400)
    if not orders.get_order(order_id):
        return response('order not found', code=404)
    if orders.delete_order(order_id):
        return response('ok')
    return response('delete failed', code=500)


@zevio.route('/api/order/item/add/', methods=['POST'])
@require_api_key
def _add_order_item():
    body = request.form
    order_id = get_field(body, 'order_id')
    product_id = get_field(body, 'product_id')
    product_name = sanitize_str(get_field(body, 'product_name'), 200)
    unit_price = price_validator(get_field(body, 'unit_price'))
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
    except (ValueError, TypeError):
        return response('invalid quantity (must be integer >= 1)', code=400)
    if product_id and not is_valid_uuid(product_id):
        return response('invalid product_id', code=400)
    if not orders.get_order(order_id):
        return response('order not found', code=404)

    if orders.add_order_item(order_id, product_id, product_name, unit_price, quantity):
        return response('ok', code=201)
    return response('failed to add item', code=500)


@zevio.route('/api/order/item/delete/', methods=['POST'])
@require_api_key
def _delete_order_item():
    body = request.form
    item_id = get_field(body, 'item_id')
    if not item_id or not is_valid_uuid(item_id):
        return response('invalid item_id', code=400)
    if orders.delete_order_item(item_id):
        return response('ok')
    return response('delete failed', code=500)


# ─── PLATFORM SETTINGS ───────────────────────────────────────────────────────

@zevio.route('/api/settings/', methods=['GET'])
@require_api_key
def _get_settings():
    return response('ok', platform.get_settings())


@zevio.route('/api/settings/', methods=['POST'])
@require_api_key
def _update_settings():
    body = request.form
    fields = {}

    for key in ('delivery_fee', 'partner_incentive'):
        if present(key):
            value = price_validator(get_field(body, key))
            if value is None:
                return response(f'invalid {key}', code=400)
            fields[key] = value

    for key in ('support_phone', 'support_whatsapp'):
        if present(key):
            value = phone_number_validator(get_field(body, key) or '')
            if not value:
                return response(f'invalid {key}', code=400)
            fields[key] = value

    if present('platform_upi_id'):
        fields['platform_upi_id'] = sanitize_str(get_field(body, 'platform_upi_id'), 100)
    if present('platform_upi_name'):
        fields['platform_upi_name'] = sanitize_str(get_field(body, 'platform_upi_name'), 100)

    if not fields:
        return response('nothing to update', code=400)
    if platform.update_settings(fields):
        return response('ok', platform.get_settings())
    return response('update failed', code=500)


@zevio.route('/api/places/', methods=['GET'])
@require_api_key
def _get_places():
    return response('ok', platform.get_places())


@zevio.route('/api/place/add/', methods=['POST'])
@require_api_key
def _add_place():
    body = request.form
    place_id = slug_validator(get_field(body, 'id') or '')
    name = sanitize_str(get_field(body, 'name'), 100)
    if not place_id:
        return response('invalid id (use lowercase letters, numbers and hyphens)', code=400)
    if not name:
        return response('invalid name', code=400)
    if platform.add_place(place_id, name):
        return response('ok', {'id': place_id, 'name': name}, code=201)
    return response('failed to add place', code=500)


@zevio.route('/api/place/update/', methods=['POST'])
@require_api_key
def _rename_place():
    body = request.form
    place_id = slug_validator(get_field(body, 'id') or '')
    name = sanitize_str(get_field(body, 'name'), 100)
    if not place_id:
        return response('invalid id', code=400)
    if not name:
        return response('invalid name', code=400)
    current = platform.get_place(place_id)
    if not current:
        return response('place not found', code=404)
    if not platform.rename_place(place_id, name):
        return response('update failed', code=500)
    # Shops store the place by name, so move them with it.
    if current['name'] != name:
        shops.rename_city(current['name'], name)
    return response('ok')


@zevio.route('/api/place/delete/', methods=['POST'])
@require_api_key
def _remove_place():
    body = request.form
    place_id = slug_validator(get_field(body, 'id') or '')
    if not place_id:
        return response('invalid id', code=400)
    current = platform.get_place(place_id)
    if not current:
        return response('place not found', code=404)
    # A place with shops in it must not disappear from under them.
    if shops.get_all_shops(current['name']):
        return response('place is in use by shops', code=409)
    if platform.remove_place(place_id):
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
