from dotenv import load_dotenv; load_dotenv()
import os, requests
from supabase import create_client

BASE = 'http://127.0.0.1:5000'
sb   = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_KEY'])

# Verify admin account
users = sb.auth.admin.list_users()
for u in users:
    if u.email == 'deadp3215@gmail.com':
        print(f'Found: {u.email} | id={u.id}')

# Test all key routes
print('\n--- Testing all fixes ---')

# 1. Login
r = requests.post(f'{BASE}/api/login', json={'email':'deadp3215@gmail.com','password':'Admin@1234'})
d = r.json()
print('Login:', d.get('success'), '| is_admin:', d.get('user',{}).get('is_admin'))
if not d.get('success'):
    print('ERROR:', d.get('message')); exit()

token = d['session']['access_token']
H = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}

# 2. Backend date validation
print('\n-- Date Validation --')
res = requests.post(f'{BASE}/api/book', headers=H,
    json={'specialty':'Cardiology','date':'2020-01-01','time_slot':'Morning (10AM - 1PM)'})
print('Past date rejected:', res.json().get('message',''))

# 3. Admin stats
res = requests.get(f'{BASE}/api/admin/stats', headers=H)
print('\n-- Admin Stats --')
s = res.json().get('stats',{})
print(f"  Patients: {s.get('total_patients')} | Doctors: {s.get('total_doctors')} | Appointments: {s.get('total_apts')}")

# 4. Admin appointments
res = requests.get(f'{BASE}/api/admin/appointments', headers=H)
d2 = res.json()
print(f"\n-- Appointments -- Total:{d2.get('total',0)}")
for a in (d2.get('appointments') or []):
    print(f"  {a['appointment_id']} | {a['patient_name']} | {a['date']} | {a['status']}")

# 5. Admin patients
res = requests.get(f'{BASE}/api/admin/users', headers=H)
d3 = res.json()
print(f"\n-- Patients -- Total:{d3.get('total',0)}")
for u in (d3.get('users') or []):
    print(f"  {u['name']} | {u['phone']}")

print('\n=== All checks complete ===')
