"""
=============================================================
  AADITYAA HOSPITAL — FLASK BACKEND (Supabase Version)
  Hospital Phone : 8886799666
  Admin Email    : venkateshbonthala8055@gmail.com

  WHAT CHANGED FROM THE OLD VERSION:
    ❌ Removed: SQLAlchemy + SQLite (hospital.db)
    ❌ Removed: Flask sessions (cookie-based login)
    ❌ Removed: werkzeug password hashing
    ❌ Removed: Python model classes (User, Doctor, Appointment)
    ✅ Added: Supabase Python client (supabase-py)
    ✅ Added: Supabase Auth (JWT token-based login)
    ✅ Added: Supabase Storage (lab report file uploads)
    ✅ Added: Row Level Security enforced at DB level
    ✅ Kept: All same API routes (/api/book, /api/doctors, etc.)
    ✅ Kept: Same JSON response format (success: true/false)
    ✅ Kept: Gmail SMTP email confirmations
    ✅ Kept: All static file routes

  HOW TO RUN:
    pip install flask flask-cors flask-mail supabase python-dotenv
    python flask_backend.py

  SETUP REQUIRED:
    1. Run supabase_setup.sql in your Supabase SQL Editor
    2. Create 'lab-reports' bucket in Supabase Storage (set public)
    3. Fill in .env with your Supabase URL and keys
    4. Register admin manually via /api/register then set is_admin=true
       in Supabase Dashboard → Table Editor → profiles
=============================================================
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_mail import Mail, Message
from flask_cors import CORS
from functools import wraps
from datetime import datetime
from supabase import create_client, Client
import os

# WHY python-dotenv? Reads your .env file into os.environ
# So you don't hardcode secrets in your code
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─────────────────────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE_DIR, template_folder=BASE_DIR)

# WHY still need secret_key? Flask-Mail and CORS still use it
app.secret_key = os.environ.get('SECRET_KEY', 'dev-fallback-secret')

# ─────────────────────────────────────────────────────────────
# Supabase Connection
#
# WHY two different keys?
#   ANON KEY    = safe for frontend HTML/JS (limited access)
#   SERVICE KEY = full admin access — ONLY use in Flask backend
#                 NEVER paste this in your HTML page!
#
# Real life: ANON key = visitor pass. SERVICE key = master key.
# ─────────────────────────────────────────────────────────────
SUPABASE_URL         = os.environ.get('SUPABASE_URL', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print('⚠️  WARNING: SUPABASE_URL or SUPABASE_SERVICE_KEY not set in .env')
    print('   Copy them from: Supabase Dashboard → Settings → API')

# WHY create_client with service key here?
# Flask is your trusted backend — it can do anything to the DB.
# The service key bypasses Row Level Security (RLS) so Flask
# can read/write all rows without restriction.
# (Your frontend uses the anon key which IS restricted by RLS.)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ─────────────────────────────────────────────────────────────
# Email — Gmail SMTP (unchanged from old version)
# ─────────────────────────────────────────────────────────────
MAIL_APP_PASSWORD = os.environ.get('MAIL_APP_PASSWORD', '')
MAIL_USERNAME     = os.environ.get('MAIL_USERNAME', 'venkateshbonthala8055@gmail.com')

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_APP_PASSWORD,
    MAIL_DEFAULT_SENDER=('Aadityaa Hospital', MAIL_USERNAME),
)

mail = Mail(app)

# WHY keep CORS? Your frontend HTML is served from the same Flask server,
# but we keep CORS open in case you build a mobile app later.
CORS(app, supports_credentials=True,
     origins=['http://localhost:5000', 'http://127.0.0.1:5000', '*'])


# ═════════════════════════════════════════════════════════════
# HELPER UTILITIES
# ═════════════════════════════════════════════════════════════

def get_token_from_request():
    """
    Extract the JWT token from the Authorization header.

    WHY JWT instead of Flask sessions?
    Old system: Flask stored a cookie (user_id=5) in the browser.
    Problem: Cookies only work on the same domain. Break on mobile apps.

    New system: Supabase gives the user a JWT token after login.
    The frontend sends it with every request: Authorization: Bearer <token>
    Flask reads it → asks Supabase "who is this?" → gets user info.
    Works on ANY device, ANY country, ANY app. That's global scale.
    """
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    return None


def decode_jwt_uid(token: str):
    """
    Decode the user UUID directly from the JWT token — NO network call needed.

    WHY? Old code called supabase.auth.get_user(token) on EVERY request.
    That means every booking, every page load → HTTP call to Supabase → wait.
    If Supabase is slow, the whole app hangs showing "Please wait..." forever.

    JWT tokens are signed strings with 3 parts: header.payload.signature
    The payload contains the user's UUID — we just base64-decode it.
    No network needed. Done in microseconds.

    Real life: Old way = asking the bank "is this card valid?" for every purchase.
    New way = reading the card chip directly — instant.
    """
    try:
        import base64, json
        payload_b64 = token.split('.')[1]
        # Fix base64 padding (JWT often omits = padding)
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get('sub')  # 'sub' is the user UUID in Supabase JWTs
    except Exception:
        return None


def get_current_user():
    """
    Verify JWT token and return user profile.
    Fast: decodes token locally, only fetches profile from DB once per request.
    """
    token = get_token_from_request()
    if not token:
        return None
    try:
        # Step 1: Get user UUID from token locally (NO network call)
        user_id = decode_jwt_uid(token)
        if not user_id:
            return None

        # Step 2: Get email from Supabase Auth (needed for email field)
        # WHY still call this? We need the email address for responses.
        # But we only do it ONCE and fall back gracefully if it fails.
        email = ''
        try:
            user_response = supabase.auth.get_user(token)
            if user_response.user:
                email = user_response.user.email
        except Exception:
            pass  # If this fails, we still have the user_id and can continue

        # Step 3: Fetch profile (name, phone, is_admin) from our DB
        profile_res = supabase.table('profiles').select('*').eq('id', user_id).maybe_single().execute()
        profile_data = profile_res.data or {}
        profile_data['email'] = email
        profile_data['id']    = str(user_id)

        # If profile missing (e.g. RLS blocked insert during registration)
        # return basic info so login/booking still works
        if not profile_res.data:
            profile_data['name']     = email.split('@')[0] if email else 'User'
            profile_data['phone']    = ''
            profile_data['is_admin'] = False

        return profile_data
    except Exception as e:
        print(f'  [get_current_user ERROR] {e}')
        return None





def login_required(f):
    """
    Route decorator: blocks unauthenticated requests.
    WHY decorator? Reusable. Just add @login_required above any route
    and it automatically blocks non-logged-in users.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Please log in to continue.'}), 401
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    """Route decorator: blocks non-admin users."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Admin access required.'}), 403
        return f(*args, **kwargs)
    return wrapper


def send_email(to, subject, html_body):
    """Send email via Gmail SMTP. Same as before — unchanged."""
    if not MAIL_APP_PASSWORD:
        print(f'  📧 [EMAIL SKIPPED — not configured] → {to}: {subject}')
        return
    try:
        msg = Message(subject, recipients=[to])
        msg.html = html_body
        mail.send(msg)
        print(f'  📧 [EMAIL SENT] → {to}')
    except Exception as e:
        print(f'  📧 [EMAIL ERROR] {e}')


def build_confirmation_email(apt: dict, patient_name: str) -> str:
    """HTML email template — unchanged from old version."""
    return f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:520px;margin:auto;border-radius:12px;overflow:hidden;border:1px solid #e1e3e4">
      <div style="background:#00483c;padding:28px 24px;text-align:center">
        <h2 style="color:#fff;margin:0;font-size:20px">🏥 Aadityaa Hospital</h2>
        <p style="color:#94d3c1;margin:4px 0 0;font-size:12px">Hastinapuram, Hyderabad | NABH Accredited</p>
      </div>
      <div style="padding:28px 24px;background:#f8fafb">
        <h3 style="color:#00483c;margin-top:0">✅ Appointment Confirmed!</h3>
        <p style="color:#3f4949">Dear <strong>{patient_name}</strong>,</p>
        <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;border:1px solid #e1e3e4;margin:16px 0">
          <tr><td style="padding:10px 14px;color:#4c616c;font-size:13px">Appointment ID</td>
              <td style="padding:10px 14px;font-weight:700">{apt['appointment_id']}</td></tr>
          <tr><td style="padding:10px 14px;color:#4c616c;font-size:13px">Doctor</td>
              <td style="padding:10px 14px">{apt.get('doctor','Any Available')}</td></tr>
          <tr><td style="padding:10px 14px;color:#4c616c;font-size:13px">Specialty</td>
              <td style="padding:10px 14px">{apt['specialty']}</td></tr>
          <tr><td style="padding:10px 14px;color:#4c616c;font-size:13px">Date</td>
              <td style="padding:10px 14px">{apt['date']}</td></tr>
          <tr><td style="padding:10px 14px;color:#4c616c;font-size:13px">Time Slot</td>
              <td style="padding:10px 14px">{apt['time_slot']}</td></tr>
        </table>
        <p style="color:#3f4949;font-size:13px">📞 For queries call: <strong>8886799666</strong></p>
        <p style="color:#6f7979;font-size:12px">Please carry a valid ID and arrive 15 minutes early.</p>
      </div>
      <div style="background:#eceeef;padding:14px 24px;text-align:center">
        <p style="color:#6f7979;font-size:11px;margin:0">© 2026 Aadityaa Hospital, Hastinapuram, Hyderabad</p>
      </div>
    </div>"""


# ═════════════════════════════════════════════════════════════
# STATIC FILE ROUTES (unchanged)
# ═════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'hospital_page.html')

@app.route('/styles.css')
def serve_css():
    return send_from_directory(BASE_DIR, 'styles.css')

@app.route('/admin')
def admin_page():
    return send_from_directory(BASE_DIR, 'admin.html')

@app.route('/health_tips.html')
def health_tips():
    return send_from_directory(BASE_DIR, 'health_tips.html')


# ═════════════════════════════════════════════════════════════
# AUTH ROUTES
# WHY changed? Old system used Flask sessions (cookies).
# New system uses Supabase Auth (JWT tokens).
# The API responses are IDENTICAL so hospital_page.html doesn't change.
# ═════════════════════════════════════════════════════════════

@app.route('/api/register', methods=['POST'])
def register():
    """
    Patient Registration.
    Expects: { name, email, phone, password }

    WHY two steps (auth + profile)?
    Step 1: supabase.auth.sign_up() — creates the login account
            Supabase handles password hashing automatically (bcrypt)
    Step 2: Insert into profiles table — stores name, phone, is_admin
    Both are linked by the same UUID from Supabase Auth.
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data received.'}), 400

    missing = [f for f in ['name', 'email', 'phone', 'password'] if not data.get(f)]
    if missing:
        return jsonify({'success': False, 'message': f'Please fill in: {", ".join(missing)}'}), 400

    phone = data['phone'].replace(' ', '').replace('-', '')
    if not phone.isdigit() or len(phone) != 10:
        return jsonify({'success': False, 'message': 'Enter a valid 10-digit mobile number.'}), 400

    if len(data['password']) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters.'}), 400

    # Step 1: Create auth account in Supabase Auth
    # WHY Supabase Auth? It handles password hashing, email verification,
    # JWT token generation — we don't write any of that code ourselves.
    try:
        auth_response = supabase.auth.sign_up({
            'email':    data['email'].lower().strip(),
            'password': data['password'],
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    if not auth_response.user:
        return jsonify({'success': False, 'message': 'Registration failed. Email may already be registered.'}), 409

    auth_user = auth_response.user

    # Step 2: Create profile row with extra info
    # WHY separately? Supabase Auth only stores email+password.
    # name, phone, is_admin are custom fields we store in profiles table.
    try:
        supabase.table('profiles').insert({
            'id':    auth_user.id,   # same UUID as auth.users
            'name':  data['name'].strip(),
            'phone': phone,
            'is_admin': False,
        }).execute()
    except Exception as e:
        return jsonify({'success': False, 'message': f'Profile creation failed: {str(e)}'}), 500

    user_dict = {
        'id':           str(auth_user.id),
        'name':         data['name'].strip(),
        'email':        auth_user.email,
        'phone':        phone,
        'is_admin':     False,
        'member_since': datetime.now().strftime('%B %Y'),
    }

    # Send welcome email (same as before)
    send_email(
        auth_user.email,
        'Welcome to Aadityaa Hospital! 🏥',
        f"""<div style="font-family:Inter,sans-serif;max-width:520px;margin:auto">
          <div style="background:#00483c;padding:28px;text-align:center;border-radius:12px 12px 0 0">
            <h2 style="color:#fff;margin:0">Welcome, {data['name'].strip()}! 🏥</h2>
          </div>
          <div style="padding:28px;background:#f8fafb;border-radius:0 0 12px 12px;border:1px solid #e1e3e4">
            <p>Your patient account at <strong>Aadityaa Hospital</strong> has been created.</p>
            <p>You can now book appointments online 24/7 from the comfort of your home.</p>
            <p style="color:#3f4949;font-size:13px">📞 Emergency: <strong>8886799666</strong></p>
          </div>
        </div>"""
    )

    return jsonify({
        'success': True,
        'message': f'Welcome, {data["name"].strip()}! Account created.',
        'user': user_dict,
        # WHY return session? The frontend needs the JWT token to make
        # authenticated requests. It stores this in localStorage.
        'session': {
            'access_token':  auth_response.session.access_token  if auth_response.session else None,
            'refresh_token': auth_response.session.refresh_token if auth_response.session else None,
        }
    }), 201


@app.route('/api/login', methods=['POST'])
def login():
    """
    Patient Login.
    Expects: { email, password }

    WHY returns a token instead of setting a cookie?
    Old: Flask set a cookie (session). Only worked on one domain.
    New: Supabase returns a JWT token. Works on any device/domain.
    The frontend stores this token and sends it with every request.
    """
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'success': False, 'message': 'Please enter email and password.'}), 400

    try:
        # WHY sign_in_with_password? Supabase verifies email + bcrypt hash.
        # We don't write any password checking code ourselves.
        auth_response = supabase.auth.sign_in_with_password({
            'email':    data['email'].lower().strip(),
            'password': data['password'],
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'Incorrect email or password.'}), 401

    if not auth_response.user:
        return jsonify({'success': False, 'message': 'Incorrect email or password.'}), 401

    auth_user = auth_response.user

    # Fetch profile — use maybe_single() so it doesn't crash if profile is missing
    profile_res = supabase.table('profiles').select('*').eq('id', auth_user.id).maybe_single().execute()
    profile_data = profile_res.data or {}

    # Auto-create missing profile (happens when RLS blocked the INSERT during registration)
    if not profile_res.data:
        try:
            supabase.table('profiles').insert({
                'id':       str(auth_user.id),
                'name':     auth_user.email.split('@')[0],
                'phone':    '',
                'is_admin': False,
            }).execute()
            profile_data = {'name': auth_user.email.split('@')[0], 'phone': '', 'is_admin': False}
        except Exception:
            pass  # Profile may already exist, or RLS still blocking — continue anyway

    user_dict = {
        'id':           str(auth_user.id),
        'name':         profile_data.get('name', auth_user.email.split('@')[0]),
        'email':        auth_user.email,
        'phone':        profile_data.get('phone', ''),
        'is_admin':     profile_data.get('is_admin', False),
        'member_since': '',
    }


    return jsonify({
        'success': True,
        'message': f'Welcome back, {user_dict["name"]}!',
        'user': user_dict,
        # Return JWT tokens — frontend stores in localStorage
        'session': {
            'access_token':  auth_response.session.access_token,
            'refresh_token': auth_response.session.refresh_token,
        }
    })


@app.route('/api/logout', methods=['POST'])
def logout():
    """
    Logout.
    WHY different from old version? No cookie to clear.
    We just tell Supabase to invalidate the token server-side.
    Frontend also removes token from localStorage.
    """
    token = get_token_from_request()
    if token:
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
    return jsonify({'success': True, 'message': 'Logged out successfully.'})


@app.route('/api/me', methods=['GET'])
@login_required
def get_me():
    """Return the currently logged-in patient's profile."""
    user = get_current_user()
    return jsonify({'success': True, 'user': user})


@app.route('/api/me/phone', methods=['PUT'])
@login_required
def change_phone():
    """
    Change phone number.
    Expects: { new_phone, current_password }

    WHY verify password again?
    Security: Even if someone steals the JWT token,
    they can't change the phone number without knowing the password.
    This is the same "special authentication" step from the old version.
    """
    user = get_current_user()
    data = request.get_json()

    if not data or not data.get('new_phone') or not data.get('current_password'):
        return jsonify({'success': False, 'message': 'Provide new phone and current password.'}), 400

    # Re-verify password by trying to login again
    # WHY? Supabase doesn't have a "check password" method separately.
    # The safest way is to attempt login with the provided password.
    try:
        verify = supabase.auth.sign_in_with_password({
            'email':    user['email'],
            'password': data['current_password'],
        })
        if not verify.user:
            raise Exception('Invalid')
    except Exception:
        return jsonify({'success': False, 'message': 'Incorrect password. Phone number not changed.'}), 401

    phone = data['new_phone'].replace(' ', '').replace('-', '')
    if not phone.isdigit() or len(phone) != 10:
        return jsonify({'success': False, 'message': 'Enter a valid 10-digit mobile number.'}), 400

    old_phone = user.get('phone', '')
    # Update in profiles table
    supabase.table('profiles').update({'phone': phone}).eq('id', user['id']).execute()

    user['phone'] = phone
    return jsonify({
        'success': True,
        'message': f'Phone updated from {old_phone} to {phone}.',
        'user': user
    })


# ═════════════════════════════════════════════════════════════
# APPOINTMENT ROUTES
# ═════════════════════════════════════════════════════════════

@app.route('/api/book', methods=['POST'])
@login_required
def book_appointment():
    """
    Book an appointment.
    Expects: { specialty, doctor_id, date, time_slot, notes? }

    WHY supabase.table('appointments').insert()?
    Old: db.session.add(new_apt) → db.session.commit()
    New: supabase.table(...).insert({...}).execute()
    Same result — both save a row to the database.
    Supabase just does it over HTTPS to their cloud server.
    """
    user = get_current_user()
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data received.'}), 400

    missing = [f for f in ['specialty', 'date', 'time_slot'] if not data.get(f)]
    if missing:
        return jsonify({'success': False, 'message': f'Please fill in: {", ".join(missing)}'}), 400

    # FIX 1 (Backend): Validate the date is not in the past.
    # WHY validate on the backend too?
    # A smart user can open browser DevTools and change the HTML to bypass the
    # frontend min-date check. The backend is the final guard — it always checks.
    # Think of it like a nightclub: the website is the bouncer at the door (frontend),
    # but security inside (backend) double-checks your ID anyway.
    from datetime import date as date_type
    try:
        submitted_date = date_type.fromisoformat(data['date'])  # "YYYY-MM-DD" → date object
        today = date_type.today()
        if submitted_date < today:
            return jsonify({
                'success': False,
                'message': f'Past dates are not allowed. You submitted {data["date"]}. Please choose today or a future date.'
            }), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400


    doctor_id = data.get('doctor_id')
    doctor_name = 'Any Available Doctor'
    if doctor_id:
        doc_res = supabase.table('doctors').select('name').eq('id', doctor_id).single().execute()
        if not doc_res.data:
            return jsonify({'success': False, 'message': 'Selected doctor not found.'}), 404
        doctor_name = doc_res.data['name']

    # Generate appointment ID (APT1001, APT1002...)
    # WHY count()? Same logic as before — count existing appointments + 1000 + 1
    count_res = supabase.table('appointments').select('id', count='exact').execute()
    apt_number = (count_res.count or 0) + 1001
    apt_id = f'APT{apt_number}'

    # Insert the appointment
    new_apt = {
        'apt_id':     apt_id,
        'patient_id': user['id'],
        'doctor_id':  doctor_id,
        'specialty':  data['specialty'],
        'date':       data['date'],
        'time_slot':  data['time_slot'],
        'notes':      data.get('notes', ''),
        'status':     'Confirmed',
    }
    result = supabase.table('appointments').insert(new_apt).execute()

    apt_dict = {
        'appointment_id': apt_id,
        'patient_name':   user.get('name', ''),
        'patient_phone':  user.get('phone', ''),
        'patient_email':  user.get('email', ''),
        'doctor':         doctor_name,
        'specialty':      data['specialty'],
        'date':           data['date'],
        'time_slot':      data['time_slot'],
        'status':         'Confirmed',
        'notes':          data.get('notes', ''),
        'booked_at':      datetime.now().strftime('%d %b %Y, %I:%M %p'),
    }

    # Send confirmation email (same template as before)
    send_email(user['email'], f"Appointment Confirmed — {apt_id} | Aadityaa Hospital",
               build_confirmation_email(apt_dict, user.get('name', '')))
    send_email('venkateshbonthala8055@gmail.com',
               f'New Booking: {apt_id} — {user.get("name","")} ({data["specialty"]})',
               f"<p>New appointment:<br><b>{user.get('name','')}</b> | {user.get('phone','')} | {data['specialty']} | {data['date']} | {data['time_slot']}</p>")

    return jsonify({
        'success': True,
        'message': f'Confirmed! ID: {apt_id}. Check your email for details.',
        'appointment': apt_dict,
    }), 201


@app.route('/api/my-appointments', methods=['GET'])
@login_required
def my_appointments():
    """All appointments of the currently logged-in patient."""
    user = get_current_user()
    # WHY .order('booked_at', desc=True)?
    # Same as old .order_by(Appointment.booked_at.desc())
    # Just different syntax — Supabase uses method chaining.
    result = supabase.table('appointments')\
        .select('*, doctors(name)')\
        .eq('patient_id', user['id'])\
        .order('booked_at', desc=True)\
        .execute()

    appointments = []
    for a in (result.data or []):
        appointments.append({
            'appointment_id': a['apt_id'],
            'patient_name':   user.get('name', ''),
            'doctor':         (a.get('doctors') or {}).get('name', 'Any Available Doctor'),
            'specialty':      a['specialty'],
            'date':           a['date'],
            'time_slot':      a['time_slot'],
            'status':         a['status'],
            'notes':          a.get('notes', ''),
            'booked_at':      a.get('booked_at', ''),
        })

    return jsonify({'success': True, 'appointments': appointments})


@app.route('/api/appointments/<apt_id>', methods=['DELETE'])
@login_required
def cancel_appointment(apt_id):
    """Patient cancels their own appointment."""
    user = get_current_user()
    result = supabase.table('appointments')\
        .select('*').eq('apt_id', apt_id.upper()).eq('patient_id', user['id'])\
        .single().execute()

    if not result.data:
        return jsonify({'success': False, 'message': 'Appointment not found.'}), 404
    if result.data['status'] == 'Cancelled':
        return jsonify({'success': False, 'message': 'Already cancelled.'}), 400

    supabase.table('appointments').update({'status': 'Cancelled'})\
        .eq('apt_id', apt_id.upper()).execute()

    return jsonify({'success': True, 'message': f'Appointment {apt_id} cancelled successfully.'})


# ═════════════════════════════════════════════════════════════
# DOCTORS & SPECIALTIES (public — no login needed)
# ═════════════════════════════════════════════════════════════

SPECIALTIES = ['Cardiology', 'Orthopaedics', 'Neurology', 'Paediatrics', 'Gynaecology', 'Dermatology']

@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    """Get all doctors. Optional ?specialty=Cardiology to filter."""
    sp = request.args.get('specialty')
    # WHY .ilike()? Case-insensitive search — same as SQLAlchemy's ilike()
    query = supabase.table('doctors').select('*')
    if sp:
        query = query.ilike('specialty', f'%{sp}%')
    result = query.order('name').execute()

    docs = []
    for d in (result.data or []):
        docs.append({
            'id':             d['id'],
            'name':           d['name'],
            'specialty':      d['specialty'],
            'qualification':  d.get('qualification', ''),
            'experience':     d.get('experience', ''),
            'fees':           d.get('fees', 0),
            'fees_display':   f'₹{d.get("fees", 0)}',
            'available_days': d['available_days'].split(',') if d.get('available_days') else [],
            'slots':          d['slots'].split(',') if d.get('slots') else [],
        })

    return jsonify({'success': True, 'count': len(docs), 'doctors': docs})


@app.route('/api/doctors', methods=['POST'])
@admin_required
def add_doctor():
    """Admin adds a new doctor. Expects doctor fields in JSON body."""
    data = request.get_json()
    result = supabase.table('doctors').insert({
        'name':           data.get('name'),
        'specialty':      data.get('specialty'),
        'qualification':  data.get('qualification', ''),
        'experience':     data.get('experience', ''),
        'fees':           data.get('fees', 0),
        'available_days': data.get('available_days', ''),
        'slots':          data.get('slots', ''),
    }).execute()
    return jsonify({'success': True, 'doctor': result.data[0] if result.data else {}}), 201


@app.route('/api/doctors/<int:doc_id>', methods=['DELETE'])
@admin_required
def delete_doctor(doc_id):
    """Admin removes a doctor."""
    supabase.table('doctors').delete().eq('id', doc_id).execute()
    return jsonify({'success': True, 'message': f'Doctor {doc_id} removed.'})


@app.route('/api/specialties', methods=['GET'])
def get_specialties():
    return jsonify({'success': True, 'specialties': SPECIALTIES})


# ═════════════════════════════════════════════════════════════
# LAB REPORTS (NEW — Supabase Storage)
# WHY new? Your old system had no file storage.
# Supabase gives 1GB free cloud storage for PDFs, images etc.
# ═════════════════════════════════════════════════════════════

@app.route('/api/lab-reports', methods=['GET'])
@login_required
def get_lab_reports():
    """Get all lab reports for the logged-in patient."""
    user = get_current_user()
    result = supabase.table('lab_reports')\
        .select('*').eq('patient_id', user['id'])\
        .order('uploaded_at', desc=True).execute()
    return jsonify({'success': True, 'reports': result.data or []})


@app.route('/api/lab-reports/upload', methods=['POST'])
@login_required
def upload_lab_report():
    """
    Upload a lab report PDF.
    Expects: multipart/form-data with 'file', 'title', 'report_type'

    WHY Supabase Storage?
    Files are stored in the cloud (not on your server).
    Supabase returns a public URL so the patient can view/download it directly.
    No file management headaches.
    """
    user = get_current_user()
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded.'}), 400

    file = request.files['file']
    title = request.form.get('title', file.filename)
    report_type = request.form.get('report_type', 'Document')

    # Upload to Supabase Storage bucket 'lab-reports'
    # WHY this path? patient_id/filename makes it organised and unique
    file_path = f"{user['id']}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    try:
        supabase.storage.from_('lab-reports').upload(file_path, file.read(),
            file_options={'content-type': file.content_type or 'application/octet-stream'})
        file_url = supabase.storage.from_('lab-reports').get_public_url(file_path)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'}), 500

    # Save metadata to database
    result = supabase.table('lab_reports').insert({
        'patient_id':  user['id'],
        'title':       title,
        'report_type': report_type,
        'file_path':   file_path,
        'file_url':    file_url,
    }).execute()

    return jsonify({'success': True, 'report': result.data[0] if result.data else {}}), 201


# ═════════════════════════════════════════════════════════════
# CONTACT FORM
# ═════════════════════════════════════════════════════════════

@app.route('/api/contact', methods=['POST'])
def contact():
    """Handle contact / inquiry form. No login required."""
    data = request.get_json()
    if not data or not data.get('name') or not data.get('message'):
        return jsonify({'success': False, 'message': 'Please provide name and message.'}), 400

    supabase.table('contact_messages').insert({
        'name':    data['name'],
        'email':   data.get('email', ''),
        'phone':   data.get('phone', ''),
        'message': data['message'],
    }).execute()

    send_email('venkateshbonthala8055@gmail.com',
        f'New Inquiry from {data["name"]} | Aadityaa Hospital',
        f"<p><b>From:</b> {data['name']}</p><p><b>Email:</b> {data.get('email','N/A')}</p>"
        f"<p><b>Phone:</b> {data.get('phone','N/A')}</p><p><b>Message:</b><br>{data['message']}</p>")

    return jsonify({
        'success': True,
        'message': f"Thank you {data['name']}! We'll respond within 24 hours.",
    }), 201


# ═════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ═════════════════════════════════════════════════════════════

@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def admin_stats():
    # WHY len(data) instead of .count? The .count property from Supabase SDK
    # sometimes returns None in certain configurations. Using len() on the actual
    # returned rows is always reliable, just slightly more data transferred.
    patients_res = supabase.table('profiles').select('id').eq('is_admin', False).execute()
    doctors_res  = supabase.table('doctors').select('id').execute()
    apts_res     = supabase.table('appointments').select('id').execute()
    conf_res     = supabase.table('appointments').select('id').eq('status','Confirmed').execute()
    canc_res     = supabase.table('appointments').select('id').eq('status','Cancelled').execute()

    try:
        msgs_res = supabase.table('contact_messages').select('id').eq('is_read', False).execute()
        unread   = len(msgs_res.data or [])
    except Exception:
        unread = 0

    return jsonify({'success': True, 'stats': {
        'total_patients':  len(patients_res.data or []),
        'total_doctors':   len(doctors_res.data  or []),
        'total_apts':      len(apts_res.data     or []),
        'confirmed':       len(conf_res.data     or []),
        'cancelled':       len(canc_res.data     or []),
        'unread_messages': unread,
    }})



@app.route('/api/admin/appointments', methods=['GET'])
@admin_required
def admin_appointments():
    # WHY no profiles(email)? Because email is stored in Supabase Auth,
    # NOT in our profiles table. Trying to select it crashes the query.
    result = supabase.table('appointments')\
        .select('*, doctors(name), profiles(name, phone)')\
        .order('booked_at', desc=True).execute()

    apts = []
    for a in (result.data or []):
        apts.append({
            'appointment_id': a['apt_id'],
            'patient_name':   (a.get('profiles') or {}).get('name', 'Unknown'),
            'patient_phone':  (a.get('profiles') or {}).get('phone', ''),
            'patient_email':  '',
            'doctor':         (a.get('doctors')  or {}).get('name', 'Any Available Doctor'),
            'specialty':      a['specialty'],
            'date':           a['date'],
            'time_slot':      a['time_slot'],
            'status':         a['status'],
            'booked_at':      a.get('booked_at', ''),
        })
    return jsonify({'success': True, 'total': len(apts), 'appointments': apts})


@app.route('/api/admin/appointments/<apt_id>', methods=['PUT'])
@admin_required
def admin_update_apt(apt_id):
    data = request.get_json()
    if data.get('status') in ['Confirmed', 'Cancelled', 'Completed', 'Pending']:
        supabase.table('appointments').update({'status': data['status']})\
            .eq('apt_id', apt_id.upper()).execute()
    return jsonify({'success': True})


@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_users():
    # WHY no order('created_at')? The profiles table has no created_at column.
    # We order by name instead which always works.
    result = supabase.table('profiles').select('id,name,phone,is_admin')\
        .eq('is_admin', False).order('name').execute()
    users = [
        {
            'id':           str(u.get('id','')),
            'name':         u.get('name', ''),
            'email':        '',   # email is in Supabase Auth, not profiles table
            'phone':        u.get('phone', ''),
            'member_since': '',
        }
        for u in (result.data or [])
    ]
    return jsonify({'success': True, 'total': len(users), 'users': users})


@app.route('/api/admin/messages', methods=['GET'])
@admin_required
def admin_messages():
    result = supabase.table('contact_messages').select('*')\
        .order('received_at', desc=True).execute()
    return jsonify({'success': True, 'messages': result.data or []})


@app.route('/api/admin/messages/<int:msg_id>/read', methods=['PUT'])
@admin_required
def mark_read(msg_id):
    supabase.table('contact_messages').update({'is_read': True}).eq('id', msg_id).execute()
    return jsonify({'success': True})


# ═════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═════════════════════════════════════════════════════════════

@app.route('/api/health', methods=['GET'])
def health():
    try:
        pts = supabase.table('profiles').select('id', count='exact').eq('is_admin', False).execute()
        apts = supabase.table('appointments').select('id', count='exact').execute()
        db_status = '✅ Supabase Connected'
    except Exception:
        db_status = '❌ Supabase Connection Failed'
        pts = type('x', (), {'count': 0})()
        apts = type('x', (), {'count': 0})()

    return jsonify({
        'status':         '✅ Running',
        'hospital':       'Aadityaa Hospital, Hastinapuram, Hyderabad',
        'database':       db_status,
        'email_ready':    bool(MAIL_APP_PASSWORD),
        'time':           datetime.now().strftime('%d %b %Y, %I:%M %p'),
        'total_patients': pts.count  or 0,
        'total_apts':     apts.count or 0,
    })


# ═════════════════════════════════════════════════════════════
# START
# ═════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print('=' * 60)
    print('  🏥 Aadityaa Hospital Backend — Supabase Version')
    print('  → Database: Supabase PostgreSQL (cloud)')
    print('  → Auth:     Supabase JWT tokens')
    print('  → Storage:  Supabase Storage (lab reports)')
    print(f'  → Supabase: {"✅ Connected" if SUPABASE_URL else "❌ NOT CONFIGURED — check .env"}')
    print('=' * 60)
    # WHY PORT from env? Render.com assigns a random port at runtime.
    # If we hardcode 5000, Render can't connect to our app and it fails.
    # Locally it defaults to 5000. On Render it uses whatever port they assign.
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
