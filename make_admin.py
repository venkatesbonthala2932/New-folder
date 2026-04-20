from dotenv import load_dotenv; load_dotenv()
import os
from supabase import create_client

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_KEY'])

# The account we previously reset
target_email = 'deadp3215@gmail.com'
print(f"Finding user {target_email}...")

users = sb.auth.admin.list_users()
target_uid = None
for u in users:
    if u.email == target_email:
        target_uid = u.id
        break

if target_uid:
    # Upgrade to admin in the profiles table
    res = sb.table('profiles').update({'is_admin': True}).eq('id', target_uid).execute()
    print(f"SUCCESS: Upgraded {target_email} to ADMIN!")
else:
    print(f"Could not find {target_email}")
