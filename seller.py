"""Seller (shop owner) API — the backend for the Mynt seller panel.

Every route lives under /api/seller/ and is scoped to ONE shop: the one that
belongs to the signed-in seller. The shop is never taken from the request, so a
seller cannot read or change another shop's orders, menu or settings by
guessing an id.

Authentication, per request:
  1. X-API-Key          — same server key as every other /api route.
  2. Authorization      — `Bearer <Google ID token>`. The token is verified
                          against Google's keys (signature, issuer, audience,
                          expiry), exactly as /api/auth/google does.
A seller is a profile with user_type = 'shop' that owns a shop
(shops.profile_id). Blocked or deactivated profiles are refused.

Everything is built on the existing profile / shop / product / order modules.
"""
from functools import wraps
from os import getenv

from flask import Blueprint, g, request

import profile as profiles
import shop as shops
import product as products
import order as orders
from auth import (bool_validator, date_validator, email_validator, is_valid_uuid,
                  phone_number_validator, price_validator, sanitize_str,
                  time_validator)

bp = Blueprint('seller', __name__, url_prefix='/api/seller')

# The panel's shop-category labels, mapped onto the API's two stored categories.
# Values the API already stores ('hotels', 'bakery') pass through unchanged.
STORED_CATEGORIES = ('hotels', 'bakery')
PANEL_CATEGORY_MAP = {
    'bakery & sweets': 'bakery',
    'restaurant & cafe': 'hotels',
    'south indian tiffin & meals': 'hotels',
    'tea, coffee & beverages': 'hotels',
    'fast food & snacks': 'hotels',
}

# What the seller's three order buttons do, in the API's own lifecycle
# (pending → confirmed → preparing → out_for_delivery → delivered | cancelled).
# There is no separate 'ready' state in the database; "ready" hands the order
# to the delivery step.
ACCEPTABLE_FROM = ('pending', 'confirmed')
READY_FROM = ('preparing', 'confirmed')
REJECTABLE_FROM = ('pending', 'confirmed', 'preparing')

# The panel uploads photos as base64 data URLs, which are far longer than a
# normal URL. Capped so one request stays well under the host's body limit.
MAX_IMAGE_CHARS = 1_500_000

_deps = {}


def _response(status, data=None, code=200):
    return _deps['response'](status, data, code)


def _google_client_id():
    return _deps['google_client_id']() or getenv('GOOGLE_CLIENT_ID') or getenv('VITE_GOOGLE_CLIENT_ID')


# ─── authentication ───────────────────────────────────────────────────────────

def _verify_google_token(token: str):
    """Returns (claims, error_response). Mirrors /api/auth/google's checks."""
    client_id = _google_client_id()
    if not client_id:
        return None, _response('server not configured: GOOGLE_CLIENT_ID is not set', code=500)
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        claims = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
    except ValueError:
        return None, _response('invalid google token', code=401)
    except Exception:
        return None, _response('could not verify google token', code=503)

    if claims.get('iss') not in ('accounts.google.com', 'https://accounts.google.com'):
        return None, _response('invalid google token', code=401)
    if not claims.get('email_verified') or not claims.get('email'):
        return None, _response('this google account has no verified email', code=403)
    return claims, None


def _resolve_seller(email: str):
    """Maps a verified email to (profile, shop, error_response)."""
    email = email_validator(email or '')
    profile = profiles.get_user_by_email(email) if email else None
    denied = _response("you don't have access yet. contact mynt to get set up", code=403)
    if not profile or profile.get('user_type') != 'shop':
        return None, None, denied
    if profile.get('is_blocked') or profile.get('is_active') is False:
        return None, None, denied
    owned = shops.get_shops_by_profile(profile['id'])
    if not owned:
        return None, None, denied
    return profile, owned[0], None


def require_seller(f):
    """API key + Google token → g.profile and g.shop."""
    @wraps(f)
    def decorated(*args, **kwargs):
        def authenticated():
            header = request.headers.get('Authorization', '')
            if not header.lower().startswith('bearer ') or not header[7:].strip():
                return _response('unauthorized', code=401)
            claims, error = _verify_google_token(header[7:].strip())
            if error:
                return error
            profile, shop, error = _resolve_seller(claims['email'])
            if error:
                return error
            g.google = claims
            g.profile = profile
            g.shop = shop
            return f(*args, **kwargs)
        # The API-key check is looked up per request: it is supplied by
        # register(), which runs after this module's routes are defined.
        return _deps['require_api_key'](authenticated)()
    return decorated


def _field(key):
    value = request.form.get(key, '')
    return value.strip() if value else None


def _present(key):
    return key in request.form


def _owned_product(product_id):
    """The product, only if it belongs to the seller's shop. (data, error)."""
    if not product_id or not is_valid_uuid(product_id):
        return None, _response('invalid product_id', code=400)
    row = products.get_product(product_id)
    if not row or row.get('shop_id') != g.shop['id']:
        return None, _response('product not found', code=404)
    return row, None


def _owned_order(order_id):
    """The order, only if it belongs to the seller's shop. (data, error)."""
    if not order_id or not is_valid_uuid(order_id):
        return None, _response('invalid order_id', code=400)
    row = orders.get_order(order_id)
    if not row or row.get('shop_id') != g.shop['id']:
        return None, _response('order not found', code=404)
    return row, None


# ─── session ──────────────────────────────────────────────────────────────────

@bp.route('/me', methods=['GET'])
@require_seller
def seller_me():
    """Sign-in check: who the seller is and which shop is theirs."""
    return _response('ok', {
        'email': g.profile.get('email'),
        'name': g.profile.get('name') or g.google.get('name'),
        'photo': g.google.get('picture'),
        'profile': g.profile,
        'shop': g.shop,
    })


# ─── shop ─────────────────────────────────────────────────────────────────────

@bp.route('/shop', methods=['GET'])
@require_seller
def seller_get_shop():
    return _response('ok', g.shop)


@bp.route('/shop/update/', methods=['POST'])
@require_seller
def seller_update_shop():
    """Shop profile: name, category, phone, area, UPI id, hours, photo."""
    fields = {}

    def text(key, column, max_len):
        if _present(key):
            value = sanitize_str(_field(key), max_len)
            if value is None:
                return f'invalid {key}'
            fields[column] = value
        return None

    for key, column, max_len in (('shop_name', 'shop_name', 100),
                                 ('city', 'city', 100),
                                 ('upi_id', 'upi_id', 100),
                                 ('logo_url', 'logo_url', MAX_IMAGE_CHARS)):
        error = text(key, column, max_len)
        if error:
            return _response(error, code=400)

    if _present('contact_phone'):
        phone = phone_number_validator(_field('contact_phone') or '')
        if not phone:
            return _response('invalid contact_phone', code=400)
        fields['contact_phone'] = phone

    if _present('category'):
        raw = (_field('category') or '').lower()
        category = raw if raw in STORED_CATEGORIES else PANEL_CATEGORY_MAP.get(raw)
        if not category:
            return _response('invalid category', code=400)
        fields['category'] = category

    for key in ('open_time', 'close_time'):
        if _present(key):
            value = time_validator(_field(key) or '')
            if not value:
                return _response(f'invalid {key} (use HH:MM)', code=400)
            fields[key] = value

    if 'upi_id' in fields and '@' not in fields['upi_id']:
        return _response('invalid upi_id', code=400)
    if not fields:
        return _response('nothing to update', code=400)
    if shops.update_shop(g.shop['id'], fields):
        return _response('ok', shops.get_shop(g.shop['id']))
    return _response('update failed', code=500)


@bp.route('/shop/toggle-open/', methods=['POST'])
@require_seller
def seller_toggle_open():
    """The open / closed switch (is_accepting_orders)."""
    status = bool_validator(_field('status'))
    if status is None:
        return _response('status must be true or false', code=400)
    if shops.toggle_accepting_orders(g.shop['id'], status):
        return _response('ok', {'is_accepting_orders': status})
    return _response('update failed', code=500)


# ─── products (menu) ──────────────────────────────────────────────────────────

def _product_fields(creating: bool):
    fields = {}

    if creating or _present('name'):
        name = sanitize_str(_field('name'), 200)
        if not name:
            return None, 'invalid name'
        fields['name'] = name
    if creating or _present('price'):
        price = price_validator(_field('price'))
        if price is None:
            return None, 'invalid price'
        fields['price'] = price
    if _present('description'):
        fields['description'] = (_field('description') or '')[:1000]
    if _present('image_url'):
        image = _field('image_url') or ''
        if len(image) > MAX_IMAGE_CHARS:
            return None, 'image is too large'
        fields['image_url'] = image or None
    if _present('section'):
        fields['section'] = sanitize_str(_field('section'), 100)
    if _present('is_available'):
        value = bool_validator(_field('is_available'))
        if value is None:
            return None, 'is_available must be true or false'
        fields['is_available'] = value
    if _present('is_veg'):
        raw = _field('is_veg')
        if raw:
            value = bool_validator(raw)
            if value is None:
                return None, 'is_veg must be true or false'
            fields['is_veg'] = value
        else:
            fields['is_veg'] = None
    return fields, None


def _slugify(name: str) -> str:
    import re
    base = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:60] or 'item'
    return base


@bp.route('/products', methods=['GET'])
@require_seller
def seller_products():
    rows = products.get_products_by_shop(g.shop['id'])
    rows.sort(key=lambda r: (r.get('name') or '').lower())
    return _response('ok', rows)


@bp.route('/product/add/', methods=['POST'])
@require_seller
def seller_add_product():
    fields, error = _product_fields(creating=True)
    if error:
        return _response(error, code=400)
    name, price = fields.pop('name'), fields.pop('price')
    # Slugs only need to be unique per shop in practice; a short suffix keeps
    # two items with the same name from colliding.
    from secrets import token_hex
    slug = f'{_slugify(name)}-{token_hex(3)}'
    product_id = products.add_product(g.shop['id'], name, slug, price, fields)
    if product_id:
        return _response('ok', products.get_product(product_id), code=201)
    return _response('failed to add product', code=500)


@bp.route('/product/update/', methods=['POST'])
@require_seller
def seller_update_product():
    _, error = _owned_product(_field('product_id'))
    if error:
        return error
    fields, error = _product_fields(creating=False)
    if error:
        return _response(error, code=400)
    if not fields:
        return _response('nothing to update', code=400)
    product_id = _field('product_id')
    if products.update_product(product_id, fields):
        return _response('ok', products.get_product(product_id))
    return _response('update failed', code=500)


@bp.route('/product/toggle-stock/', methods=['POST'])
@require_seller
def seller_toggle_stock():
    _, error = _owned_product(_field('product_id'))
    if error:
        return error
    status = bool_validator(_field('in_stock'))
    if status is None:
        return _response('in_stock must be true or false', code=400)
    if products.toggle_product_availability(_field('product_id'), status):
        return _response('ok', {'is_available': status})
    return _response('update failed', code=500)


@bp.route('/product/delete/', methods=['POST'])
@require_seller
def seller_delete_product():
    _, error = _owned_product(_field('product_id'))
    if error:
        return error
    if products.remove_product(_field('product_id')):
        return _response('ok')
    return _response('delete failed', code=500)


# ─── orders ───────────────────────────────────────────────────────────────────

def _with_items(order_rows):
    """Attaches `items` to each order using one query for the whole list."""
    items = orders.get_items_for_orders([o['id'] for o in order_rows])
    by_order = {}
    for item in items:
        by_order.setdefault(item['order_id'], []).append(item)
    return [dict(o, items=by_order.get(o['id'], [])) for o in order_rows]


@bp.route('/orders', methods=['GET'])
@require_seller
def seller_orders():
    """The shop's orders, newest first, each with its line items.
    Optional ?status= and ?date=YYYY-MM-DD (a UTC day)."""
    status = request.args.get('status', '').strip() or None
    date = request.args.get('date', '').strip() or None
    if status and status not in orders.VALID_STATUSES:
        return _response('invalid status', code=400)
    if date and not date_validator(date):
        return _response('invalid date (use YYYY-MM-DD)', code=400)
    rows = orders.get_orders_by_shop(g.shop['id'], status)
    if date:
        rows = [r for r in rows if (r.get('created_at') or '')[:10] == date]
    return _response('ok', _with_items(rows))


@bp.route('/order/<string:order_id>', methods=['GET'])
@require_seller
def seller_order(order_id: str):
    row, error = _owned_order(order_id)
    if error:
        return error
    return _response('ok', _with_items([row])[0])


def _transition(allowed_from, new_status, reject_reason=None):
    order_id = _field('order_id')
    row, error = _owned_order(order_id)
    if error:
        return error
    if row.get('status') not in allowed_from:
        return _response(f"order is {row.get('status')}; cannot move to {new_status}", code=409)
    if orders.update_order_status(order_id, new_status, reject_reason):
        return _response('ok', orders.get_order(order_id))
    return _response('update failed', code=500)


@bp.route('/order/accept/', methods=['POST'])
@require_seller
def seller_accept_order():
    return _transition(ACCEPTABLE_FROM, 'preparing')


@bp.route('/order/reject/', methods=['POST'])
@require_seller
def seller_reject_order():
    reason = sanitize_str(_field('reject_reason'), 200)
    if not reason:
        return _response('reject_reason is required', code=400)
    return _transition(REJECTABLE_FROM, 'cancelled', reason)


@bp.route('/order/ready/', methods=['POST'])
@require_seller
def seller_order_ready():
    return _transition(READY_FROM, 'out_for_delivery')


def register(app, *, response, require_api_key, google_client_id):
    """Hooks the seller routes into the app. Called once from main.py."""
    _deps['response'] = response
    _deps['require_api_key'] = require_api_key
    _deps['google_client_id'] = google_client_id
    # Werkzeug refuses form fields over 500 KB by default, which would reject
    # the photo uploads above. Still far below the host's 4.5 MB request limit.
    app.config['MAX_FORM_MEMORY_SIZE'] = max(app.config.get('MAX_FORM_MEMORY_SIZE') or 0, 2_000_000)
    app.register_blueprint(bp)
