from dotenv import load_dotenv; load_dotenv()
import os
from supabase import create_client

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_KEY'])

print('=== AUTH USERS IN SUPABASE ===')
users = sb.auth.admin.list_users()
for u in users:
    print('  Email:', u.email, ' | ID:', str(u.id)[:8] + '...')

print()
print('=== PROFILE ROWS ===')
p = sb.table('profiles').select('*').execute()
for row in (p.data or []):
    print('  Name:', row.get('name'), ' | Phone:', row.get('phone'), ' | ID:', str(row.get('id'))[:8] + '...')
if not p.data:
    print('  (no profiles yet - this is the problem!)')
