import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

print("Fetching non-existent user profile...")
try:
    res = supabase.table('profiles').select('*').eq('id', '00000000-0000-0000-0000-000000000000').maybe_single().execute()
    print("Type of res:", type(res))
    print("res:", res)
    if res:
        print("res.data:", getattr(res, 'data', 'NO DATA ATTR'))
except Exception as e:
    print("Error:", e)
 