from db import init_order_table, init_order_item_table
from uuid import uuid4
from secrets import token_hex
from datetime import datetime, timezone

order_table = init_order_table()
order_item_table = init_order_item_table()

VALID_STATUSES = ['pending', 'confirmed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled']

# Each status stamps its own column, so every phone shows the same timeline
# instead of the time this particular device happened to see the change.
STATUS_TIMESTAMP = {
    'confirmed': 'confirmed_at',
    'preparing': 'preparing_at',
    'out_for_delivery': 'out_for_delivery_at',
    'delivered': 'delivered_at',
    'cancelled': 'cancelled_at',
}

def _new_uuid():
    return str(uuid4())

def _order_number():
    return 'ZV-' + token_hex(4).upper()

def _now():
    return datetime.now(timezone.utc).isoformat()

def get_order(order_id: str) -> dict:
    result = order_table.select('*').eq('id', order_id).execute()
    if result.data:
        return result.data[0]
    return None

def get_order_by_number(order_number: str) -> dict:
    result = order_table.select('*').eq('order_number', order_number).execute()
    if result.data:
        return result.data[0]
    return None

def get_orders_by_customer(customer_id: str, status: str = None) -> list:
    query = order_table.select('*').eq('customer_id', customer_id).order('created_at', desc=True)
    if status:
        query = query.eq('status', status)
    return query.execute().data

def get_orders_by_shop(shop_id: str, status: str = None) -> list:
    query = order_table.select('*').eq('shop_id', shop_id).order('created_at', desc=True)
    if status:
        query = query.eq('status', status)
    return query.execute().data

def get_orders_by_partner(partner_id: str, status: str = None) -> list:
    query = (order_table.select('*')
             .eq('delivery_partner_id', partner_id)
             .order('created_at', desc=True))
    if status:
        query = query.eq('status', status)
    return query.execute().data

def get_all_orders(status: str = None, date: str = None, limit: int = 1000) -> list:
    """Every order, newest first — the admin orders list and dashboard.

    `date` is 'YYYY-MM-DD' and selects that whole UTC day.
    """
    query = order_table.select('*').order('created_at', desc=True).limit(limit)
    if status:
        query = query.eq('status', status)
    if date:
        query = query.gte('created_at', date + 'T00:00:00+00:00') \
                     .lte('created_at', date + 'T23:59:59.999+00:00')
    return query.execute().data

def place_order(customer_id: str, shop_id: str, subtotal: float,
                delivery_fee: float, discount_amount: float, total_amount: float,
                recipient_name: str, recipient_phone: str,
                delivery_address: str, delivery_city: str,
                delivery_postal_code: str, items: list,
                extra: dict = None) -> dict:
    """Creates the order and all its line items. Nothing is left half-saved:
    if the items fail, the order row is removed again."""
    order_id = _new_uuid()
    order_number = _order_number()

    row = {
        'id': order_id,
        'customer_id': customer_id,
        'shop_id': shop_id,
        'order_number': order_number,
        'status': 'pending',
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'discount_amount': discount_amount,
        'total_amount': total_amount,
        'recipient_name': recipient_name,
        'recipient_phone': recipient_phone,
        'delivery_address': delivery_address,
        'delivery_city': delivery_city,
        'delivery_postal_code': delivery_postal_code,
    }
    for key, value in (extra or {}).items():
        if value is not None:
            row[key] = value

    try:
        order_table.insert(row).execute()
    except Exception:
        return None

    try:
        # One insert for every line, so a bad item cannot leave a half order.
        order_item_table.insert([{
            'id': _new_uuid(),
            'order_id': order_id,
            'product_id': item.get('product_id'),
            'product_name': item['product_name'],
            'unit_price': float(item['unit_price']),
            'quantity': int(item['quantity']),
            'line_total': round(float(item['unit_price']) * int(item['quantity']), 2),
        } for item in items]).execute()
    except Exception:
        try:
            order_table.delete().eq('id', order_id).execute()
        except Exception:
            pass
        return None

    return {'order_id': order_id, 'order_number': order_number}

def update_order_status(order_id: str, status: str, reject_reason: str = None) -> bool:
    try:
        data = {'status': status}
        stamp = STATUS_TIMESTAMP.get(status)
        if stamp:
            data[stamp] = _now()
        if status == 'cancelled' and reject_reason:
            data['reject_reason'] = reject_reason
        # Cash is collected on delivery.
        if status == 'delivered':
            data['payment_status'] = 'PAID'
        order_table.update(data).eq('id', order_id).execute()
        return True
    except Exception:
        return False

def cancel_order(order_id: str, reject_reason: str = None) -> bool:
    return update_order_status(order_id, 'cancelled', reject_reason)

def assign_partner(order_id: str, partner_id: str) -> bool:
    """Admin assigns or (partner_id = None) unassigns a delivery partner."""
    try:
        order_table.update({'delivery_partner_id': partner_id}).eq('id', order_id).execute()
        return True
    except Exception:
        return False

def mark_order_paid(order_id: str) -> bool:
    try:
        order_table.update({'payment_status': 'PAID'}).eq('id', order_id).execute()
        return True
    except Exception:
        return False

def delete_order(order_id: str) -> bool:
    try:
        order_item_table.delete().eq('order_id', order_id).execute()
        order_table.delete().eq('id', order_id).execute()
        return True
    except Exception:
        return False

def get_order_items(order_id: str) -> list:
    result = order_item_table.select('*').eq('order_id', order_id).execute()
    return result.data

def get_items_for_orders(order_ids: list) -> list:
    """Line items for many orders in one call, so a long list does not need
    one request per order."""
    if not order_ids:
        return []
    result = order_item_table.select('*').in_('order_id', order_ids).execute()
    return result.data

def add_order_item(order_id: str, product_id: str, product_name: str,
                   unit_price: float, quantity: int) -> bool:
    try:
        order_item_table.insert({
            'id': _new_uuid(),
            'order_id': order_id,
            'product_id': product_id,
            'product_name': product_name,
            'unit_price': unit_price,
            'quantity': quantity,
            'line_total': round(unit_price * quantity, 2),
        }).execute()
        return True
    except Exception:
        return False

def delete_order_item(item_id: str) -> bool:
    try:
        order_item_table.delete().eq('id', item_id).execute()
        return True
    except Exception:
        return False
