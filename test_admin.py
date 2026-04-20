from dotenv import load_dotenv; load_dotenv()
import os, requests
from supabase import create_client

BASE = 'http://127.0.0.1:5000'
sb   = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_KEY'])

# Step 1: Reset password so we know it for sure
users = sb.auth.admin.list_users()
uid = next((u.id for u in users if u.email == 'deadp3215@gmail.com'), None)
if uid:
    sb.auth.admin.update_user_by_id(uid, {'password': 'Admin@1234'})
    print('Password reset to Admin@1234')

# Step 2: Login
r    = requests.post(f'{BASE}/api/login', json={'email': 'deadp3215@gmail.com', 'password': 'Admin@1234'})
data = r.json()
print('Login success:', data.get('success'))
print('is_admin:', data.get('user', {}).get('is_admin'))

if not data.get('success'):
    print('ERROR:', data.get('message'))
    exit()

token   = data['session']['access_token']
headers = {'Authorization': 'Bearer ' + token}

# Step 3: Test each admin route
routes = ['/api/admin/stats', '/api/admin/appointments', '/api/admin/users', '/api/admin/messages']
for route in routes:
    res = requests.get(f'{BASE}{route}', headers=headers)
    body = res.json()
    print()
    print('ROUTE:', route, '| HTTP:', res.status_code)
    print('RESPONSE:', str(body)[:200])
