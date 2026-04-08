"""
Load test - simulates 50 users trying to login at the same time.
Run: python load_test.py
"""
import time
import threading
import requests

BASE = 'http://127.0.0.1:5000'
RESULTS = {'success': 0, 'fail': 0, 'times': []}
LOCK = threading.Lock()

def try_login(user_num):
    start = time.time()
    try:
        r = requests.post(f'{BASE}/api/doctors', timeout=10)
        elapsed = round(time.time() - start, 2)
        with LOCK:
            if r.status_code in [200, 201]:
                RESULTS['success'] += 1
            else:
                RESULTS['fail'] += 1
            RESULTS['times'].append(elapsed)
    except Exception as e:
        with LOCK:
            RESULTS['fail'] += 1
            RESULTS['times'].append(10.0)

# Simulate 50 simultaneous users
USERS = 50
print(f'Sending {USERS} simultaneous requests to Flask...')
start_total = time.time()

threads = [threading.Thread(target=try_login, args=(i,)) for i in range(USERS)]
for t in threads: t.start()
for t in threads: t.join()

total = time.time() - start_total
avg   = sum(RESULTS['times']) / len(RESULTS['times']) if RESULTS['times'] else 0
slow  = sum(1 for t in RESULTS['times'] if t > 2.0)

print(f'\n=== RESULTS ({USERS} simultaneous users) ===')
print(f'  Succeeded  : {RESULTS["success"]}')
print(f'  Failed     : {RESULTS["fail"]}')
print(f'  Total time : {round(total, 2)}s')
print(f'  Avg per req: {round(avg, 3)}s')
print(f'  Slow (>2s) : {slow} requests')
print()
if avg < 0.5:
    print('VERDICT: FAST ✅ — Good for current usage')
elif avg < 2.0:
    print('VERDICT: ACCEPTABLE ⚠️  — Okay for small hospital, upgrade for scale')
else:
    print('VERDICT: TOO SLOW ❌ — Need Gunicorn to handle real load')
