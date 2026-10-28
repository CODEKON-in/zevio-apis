from supabase import create_client
from dotenv import load_dotenv
from os import getenv

load_dotenv('secrets.env')

conn = create_client(getenv('SUPABASE_URL'),getenv('SUPABASE_SECRET_KEY'))

def init_profile_table():
    return conn.table('profiles')
