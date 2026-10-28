from db import init_profile_table
from secrets import token_hex

profile_table = init_profile_table()

def generate_uuid() -> str:
    parts = []
    parts.append(token_hex(4))
    parts.append(token_hex(2))
    parts.append(token_hex(2))
    parts.append(token_hex(2))
    parts.append(token_hex(6))

    return '-'.join(parts)

def get_user_info(uid:str) -> dict:
    users = profile_table.select('*').eq('id',uid).execute()
    return users.data[0]

def add_user(uid:str,name:str,phone:str,user_type:str) -> bool:
    try:
        profile_table.insert({
            'id':uid,
            'name':name,
            'phone':phone,
            'user_type':user_type
        }).execute()
        return True
    except Exception as e:
        return e

def update_user(uid:str,attr:str,attr_value:str) -> bool:
    try:
        profile_table.update({attr:attr_value}).eq('id',uid).execute()
        return True
    except: return False

def remove_user(uid:str) -> bool:
    try:
        profile_table.delete().eq('id',uid).execute()
        return True
    except: return False
