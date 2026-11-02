from supabase import create_client
from dotenv import load_dotenv
from os import getenv

# load_dotenv picks up secrets.env locally; on Vercel env vars are injected directly
load_dotenv('secrets.env')
load_dotenv()

conn = None

# Supabase hands the same two values out under several names depending on where
# they were copied from, and a key pasted into a hosting dashboard often carries
# a trailing newline or the quotes it was copied inside. Accepting the common
# spellings means one misnamed variable does not take the whole API down with a
# bare 500, which is what happened in production.
URL_NAMES = ('SUPABASE_URL', 'SUPABASE_PROJECT_URL', 'NEXT_PUBLIC_SUPABASE_URL',
             'VITE_SUPABASE_URL')
KEY_NAMES = ('SUPABASE_SECRET_KEY', 'SUPABASE_SERVICE_ROLE_KEY',
             'SUPABASE_SERVICE_KEY', 'SUPABASE_KEY', 'SUPABASE_ANON_KEY',
             'NEXT_PUBLIC_SUPABASE_ANON_KEY')


class DatabaseNotConfigured(ValueError):
    """The environment provides no usable Supabase URL and key.

    Its own type, so the 500 handler can report this one cause instead of
    replacing it with 'internal server error' — which is what made the
    production failure impossible to act on.
    """


def _first(preferred, names):
    """The first of `names` the environment actually provides, cleaned up."""
    for name in (preferred,) + tuple(n for n in names if n != preferred):
        value = getenv(name)
        if value:
            value = value.strip().strip('\'"').strip()
            if value:
                return value
    return None

def get_conn():
    global conn
    if conn is None:
        url = _first('SUPABASE_URL', URL_NAMES)
        key = _first('SUPABASE_SECRET_KEY', KEY_NAMES)
        if not url or not key:
            # Name every variable that was looked for, so a misnamed one can be
            # spotted without guessing. Values are never included.
            missing = []
            if not url:
                missing.append('project URL (tried: %s)' % ', '.join(URL_NAMES))
            if not key:
                missing.append('service key (tried: %s)' % ', '.join(KEY_NAMES))
            raise DatabaseNotConfigured(
                'Database not configured: the environment provides no ' +
                ' and no '.join(missing) +
                '. Set SUPABASE_URL and SUPABASE_SECRET_KEY in the hosting '
                'project settings.'
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
