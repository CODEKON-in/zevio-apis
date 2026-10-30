from supabase import create_client
from dotenv import load_dotenv
from os import getenv

# load_dotenv picks up secrets.env locally; on Vercel env vars are injected directly
load_dotenv('secrets.env')
load_dotenv()

conn = None

def get_conn():
    global conn
    if conn is None:
        url = getenv('SUPABASE_URL')
        key = getenv('SUPABASE_SECRET_KEY')
        if not url or not key:
            raise ValueError(
                "Missing SUPABASE_URL or SUPABASE_SECRET_KEY environment variable. "
                "Please configure them in your Vercel Project Settings."
            )
        conn = create_client(url, key)
    return conn

class LazyTable:
    def __init__(self, table_name: str):
        self._table_name = table_name

    def __getattr__(self, name: str):
        table = get_conn().table(self._table_name)
        return getattr(table, name)

def init_profile_table():
    return LazyTable('profiles')

def init_shop_table():
    return LazyTable('shops')

def init_product_table():
    return LazyTable('products')

def init_order_table():
    return LazyTable('orders')

def init_order_item_table():
    return LazyTable('order_items')

def init_settings_table():
    return LazyTable('platform_settings')

def init_place_table():
    return LazyTable('service_places')
