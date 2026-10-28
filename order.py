from db import init_order_table, init_order_item_table
from secrets import token_hex
from datetime import datetime, timezone

order_table = init_order_table()
order_item_table = init_order_item_table()

VALID_STATUSES = ['pending', 'confirmed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled']

def _new_uuid():
    return (token_hex(4) + '-' + token_hex(2) + '-' +
            token_hex(2) + '-' + token_hex(2) + '-' + token_hex(6))

def _order_number():
    return 'ZV-' + token_hex(4).upper()

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

def place_order(customer_id: str, shop_id: str, subtotal: float,
                delivery_fee: float, discount_amount: float, total_amount: float,
                recipient_name: str, recipient_phone: str,
                delivery_address: str, delivery_city: str,
                delivery_postal_code: str, items: list) -> dict:
    try:
        order_id = _new_uuid()
        order_number = _order_number()

        order_table.insert({
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
        }).execute()

        for item in items:
            order_item_table.insert({
                'id': _new_uuid(),
                'order_id': order_id,
                'product_id': item.get('product_id'),
                'product_name': item['product_name'],
                'unit_price': item['unit_price'],
                'quantity': item['quantity'],
                'line_total': round(item['unit_price'] * item['quantity'], 2),
            }).execute()

        return {'order_id': order_id, 'order_number': order_number}
    except:
        return None

def update_order_status(order_id: str, status: str) -> bool:
    try:
        order_table.update({'status': status}).eq('id', order_id).execute()
        return True
    except:
        return False

def cancel_order(order_id: str) -> bool:
    return update_order_status(order_id, 'cancelled')

def delete_order(order_id: str) -> bool:
    try:
        order_item_table.delete().eq('order_id', order_id).execute()
        order_table.delete().eq('id', order_id).execute()
        return True
    except:
        return False

def get_order_items(order_id: str) -> list:
    result = order_item_table.select('*').eq('order_id', order_id).execute()
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
    except:
        return False

def delete_order_item(item_id: str) -> bool:
    try:
        order_item_table.delete().eq('id', item_id).execute()
        return True
    except:
        return False
