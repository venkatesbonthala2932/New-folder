"""
Re-creates the admin account and a test patient account in Supabase.
Run this once to restore after a database reset.
"""
from dotenv import load_dotenv; load_dotenv()
import os, requests
from supabase import create_client

sb   = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_KEY'])
BASE = 'http://127.0.0.1:5000'

print('=== Restoring accounts ===')

# 1. Create admin account in Supabase Auth
print('\n[1] Creating admin account...')
try:
    admin = sb.auth.admin.create_user({
        'email': 'deadp3215@gmail.com',
        'password': 'Admin@1234',
        'email_confirm': True,   # Skip email verification
    })
    admin_uid = admin.user.id
    print('  Admin Auth user created:', admin.user.email)

    # Add profile row with is_admin=True
    sb.table('profiles').insert({
        'id':       str(admin_uid),
        'name':     'Admin',
        'phone':    '9963132932',
        'is_admin': True,
    }).execute()
    print('  Admin profile saved.')
except Exception as e:
    if 'already' in str(e).lower() or 'exists' in str(e).lower():
        print('  Admin already exists, updating to admin...')
        users = sb.auth.admin.list_users()
        for u in users:
            if u.email == 'deadp3215@gmail.com':
                sb.table('profiles').upsert({'id': str(u.id), 'name': 'Admin', 'phone': '9963132932', 'is_admin': True}).execute()
    else:
        print('  ERROR:', e)

# 2. Create a test patient account
print('\n[2] Creating test patient account...')
try:
    patient = sb.auth.admin.create_user({
        'email': 'testpatient@gmail.com',
        'password': 'Patient@1234',
        'email_confirm': True,
    })
    patient_uid = patient.user.id
    sb.table('profiles').insert({
        'id':       str(patient_uid),
        'name':     'Test Patient',
        'phone':    '9876543210',
        'is_admin': False,
    }).execute()
    print('  Patient created: testpatient@gmail.com / Patient@1234')
except Exception as e:
    print('  (Already exists or error):', str(e)[:80])

# 3. Verify by logging in
print('\n[3] Verifying login works...')
r = requests.post(f'{BASE}/api/login', json={'email': 'deadp3215@gmail.com', 'password': 'Admin@1234'})
d = r.json()
if d.get('success'):
    print(f'  Login SUCCESS | is_admin={d["user"]["is_admin"]} | name={d["user"]["name"]}')
else:
    print('  Login FAILED:', d.get('message'))

print('\n=== Done! ===')
print('Admin:   deadp3215@gmail.com / Admin@1234')
print('Patient: testpatient@gmail.com / Patient@1234')
print('Open http://127.0.0.1:5000 and login with the above accounts.')
print('Admin panel: http://127.0.0.1:5000/admin')
