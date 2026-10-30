"""Platform settings and the service area.

Both used to live in the browser, so every device had its own delivery fee and
its own list of places. They are now rows in the database, shared by everyone.
"""
from db import init_settings_table, init_place_table

settings_table = init_settings_table()
place_table = init_place_table()

SETTINGS_ROW_ID = 1

EDITABLE_COLUMNS = ('delivery_fee', 'partner_incentive', 'support_phone',
                    'support_whatsapp', 'platform_upi_id', 'platform_upi_name')

DEFAULTS = {
    'id': SETTINGS_ROW_ID,
    'delivery_fee': 20,
    'partner_incentive': 10,
    'support_phone': None,
    'support_whatsapp': None,
    'platform_upi_id': None,
    'platform_upi_name': None,
}

def get_settings() -> dict:
    """The single settings row. Creates it with the defaults if it is missing."""
    result = settings_table.select('*').eq('id', SETTINGS_ROW_ID).execute()
    if result.data:
        return result.data[0]
    try:
        settings_table.insert(dict(DEFAULTS)).execute()
    except Exception:
        pass
    result = settings_table.select('*').eq('id', SETTINGS_ROW_ID).execute()
    if result.data:
        return result.data[0]
    return dict(DEFAULTS)

def update_settings(data: dict) -> bool:
    clean = {k: v for k, v in (data or {}).items() if k in EDITABLE_COLUMNS}
    if not clean:
        return False
    try:
        get_settings()  # make sure the row exists before updating it
        settings_table.update(clean).eq('id', SETTINGS_ROW_ID).execute()
        return True
    except Exception:
        return False


# ─── service places ───────────────────────────────────────────────────────────

def get_places() -> list:
    return place_table.select('id,name').order('name').execute().data

def get_place(place_id: str) -> dict:
    result = place_table.select('id,name').eq('id', place_id).execute()
    if result.data:
        return result.data[0]
    return None

def add_place(place_id: str, name: str) -> bool:
    try:
        place_table.upsert({'id': place_id, 'name': name}).execute()
        return True
    except Exception:
        return False

def rename_place(place_id: str, name: str) -> bool:
    try:
        place_table.update({'name': name}).eq('id', place_id).execute()
        return True
    except Exception:
        return False

def remove_place(place_id: str) -> bool:
    try:
        place_table.delete().eq('id', place_id).execute()
        return True
    except Exception:
        return False
