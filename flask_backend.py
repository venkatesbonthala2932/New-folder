"""
=============================================================
  AADITYAA HOSPITAL — FLASK BACKEND (Full Production Version)
  Hospital Phone : 8886799666
  Admin Email    : venkateshbonthala8055@gmail.com

  Features:
    ✅ SQLite database (hospital.db) — permanent storage
    ✅ Patient registration & login (session-based)
    ✅ Appointment booking with email confirmation
    ✅ Doctors with fees & available days
    ✅ Admin dashboard at /admin
    ✅ Phone change with password verification

  HOW TO RUN:
    pip install flask flask-cors flask-sqlalchemy flask-mail
    python flask_backend.py

  FOR EMAIL (one-time setup):
    1. Go to myaccount.google.com
    2. Security → Enable 2-Step Verification
    3. Search "App passwords" → Create → Select "Mail"
    4. Copy the 16-char password (e.g. abcd efgh ijkl mnop)
    5. Paste it (without spaces) in MAIL_APP_PASSWORD below

  FIRST RUN:
    Admin login: admin@aadityaa.com / admin123
    (Change this password after first login!)
=============================================================
"""

from flask import Flask, request, jsonify, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os

# ─────────────────────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR, template_folder=BASE_DIR)

# Secret key: used to sign session cookies — keep this private!
# Real life: This is the hospital's vault combination.
app.secret_key = 'aadityaa-hyderabad-flask-secret-2024'

# ─────────────────────────────────────────────────────────────
# Database — SQLite
#
# hospital.db is created in your project folder.
# Unlike a Python list, THIS SURVIVES server restarts!
#
# Real life: Before = whiteboard (erases on off).
#            Now    = printed register book (permanent).
# ─────────────────────────────────────────────────────────────
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"sqlite:///{os.path.join(BASE_DIR, 'hospital.db')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ─────────────────────────────────────────────────────────────
# Email — Gmail SMTP
#
# Replace 'YOUR_GMAIL_APP_PASSWORD' with the 16-char App Password
# you get from myaccount.google.com → App passwords.
#
# If not configured, emails are just printed to console.
# ─────────────────────────────────────────────────────────────
MAIL_APP_PASSWORD = 'pstueolrfrpuesvq'   # Gmail App Password

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='venkateshbonthala8055@gmail.com',
    MAIL_PASSWORD=MAIL_APP_PASSWORD,
    MAIL_DEFAULT_SENDER=('Aadityaa Hospital', 'venkateshbonthala8055@gmail.com'),
)

db   = SQLAlchemy(app)
mail = Mail(app)
CORS(app, supports_credentials=True,
     origins=['http://localhost:5000', 'http://127.0.0.1:5000'])


# ═════════════════════════════════════════════════════════════
# DATABASE MODELS  (each class = one table in hospital.db)
#
# Think of models like Excel sheets:
#   User model        → "Patients" sheet
#   Doctor model      → "Doctors Directory" sheet
#   Appointment model → "Appointment Logbook" sheet
#   ContactMessage    → "Inquiry Box" sheet
# ═════════════════════════════════════════════════════════════

class User(db.Model):
    """Patient accounts — one row per registered patient."""
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    phone         = db.Column(db.String(15),  nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin      = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship('Appointment', backref='patient', lazy=True)

    def set_password(self, plain):
        """Hash password before saving — NEVER store plain text!
        Real life: Like converting your ATM PIN into an encrypted code.
        Only the bank (Flask) can verify it, but cannot read the original."""
        self.password_hash = generate_password_hash(plain)

    def check_password(self, plain):
        return check_password_hash(self.password_hash, plain)

    def to_dict(self):
        return {
            'id':           self.id,
            'name':         self.name,
            'email':        self.email,
            'phone':        self.phone,
            'is_admin':     self.is_admin,
            'member_since': self.created_at.strftime('%B %Y'),
        }


class Doctor(db.Model):
    """Doctors directory — one row per doctor."""
    __tablename__ = 'doctors'

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(100), nullable=False)
    specialty      = db.Column(db.String(100), nullable=False)
    qualification  = db.Column(db.String(200))
    experience     = db.Column(db.String(50))
    fees           = db.Column(db.Integer)          # Consultation fee in ₹
    available_days = db.Column(db.String(200))      # Comma-separated, e.g. "Mon,Tue,Wed"
    slots          = db.Column(db.String(200))      # e.g. "Morning (10AM-1PM),Evening (4PM-7PM)"

    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

    def to_dict(self):
        return {
            'id':             self.id,
            'name':           self.name,
            'specialty':      self.specialty,
            'qualification':  self.qualification,
            'experience':     self.experience,
            'fees':           self.fees,
            'fees_display':   f'₹{self.fees}',
            'available_days': self.available_days.split(',') if self.available_days else [],
            'slots':          self.slots.split(',') if self.slots else [],
        }


class Appointment(db.Model):
    """Appointment logbook — one row per booking."""
    __tablename__ = 'appointments'

    id        = db.Column(db.Integer, primary_key=True)
    apt_id    = db.Column(db.String(20), unique=True, nullable=False)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    specialty = db.Column(db.String(100))
    date      = db.Column(db.String(20))
    time_slot = db.Column(db.String(50))
    status    = db.Column(db.String(20), default='Confirmed')
    notes     = db.Column(db.Text, default='')
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        patient = User.query.get(self.user_id)
        doc     = Doctor.query.get(self.doctor_id) if self.doctor_id else None
        return {
            'appointment_id': self.apt_id,
            'patient_name':   patient.name  if patient else 'Unknown',
            'patient_phone':  patient.phone if patient else '',
            'patient_email':  patient.email if patient else '',
            'doctor':         doc.name      if doc     else 'Any Available Doctor',
            'specialty':      self.specialty,
            'date':           self.date,
            'time_slot':      self.time_slot,
            'status':         self.status,
            'notes':          self.notes,
            'booked_at':      self.booked_at.strftime('%d %b %Y, %I:%M %p'),
        }


class ContactMessage(db.Model):
    """Inquiry / contact form messages."""
    __tablename__ = 'contact_messages'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100))
    email       = db.Column(db.String(150))
    phone       = db.Column(db.String(15))
    message     = db.Column(db.Text)
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read     = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id':          self.id,
            'name':        self.name,
            'email':       self.email,
            'phone':       self.phone,
            'message':     self.message,
            'received_at': self.received_at.strftime('%d %b %Y, %I:%M %p'),
            'is_read':     self.is_read,
        }


# ═════════════════════════════════════════════════════════════
# HELPER UTILITIES
# ═════════════════════════════════════════════════════════════

def current_user():
    """Return the logged-in User object from session, or None."""
    uid = session.get('user_id')
    return User.query.get(uid) if uid else None


def login_required(f):
    """Route decorator: blocks non-logged-in users.
    Real life: Security guard checking your visitor pass at hospital gate."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            return jsonify({'success': False, 'message': 'Please log in to continue.'}), 401
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    """Route decorator: blocks non-admin users."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u or not u.is_admin:
            return jsonify({'success': False, 'message': 'Admin access required.'}), 403
        return f(*args, **kwargs)
    return wrapper


def send_email(to, subject, html_body):
    """Send email. Silently logs to console if not configured."""
    if MAIL_APP_PASSWORD == 'YOUR_GMAIL_APP_PASSWORD':
        print(f'  📧 [EMAIL SKIPPED — not configured] → {to}: {subject}')
        return
    try:
        msg      = Message(subject, recipients=[to])
        msg.html = html_body
        mail.send(msg)
        print(f'  📧 [EMAIL SENT] → {to}')
    except Exception as e:
        print(f'  📧 [EMAIL ERROR] {e}')


def build_confirmation_email(apt: dict, patient_name: str) -> str:
    """HTML email template for appointment confirmation."""
    return f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:520px;margin:auto;border-radius:12px;overflow:hidden;border:1px solid #e1e3e4">
      <div style="background:#00483c;padding:28px 24px;text-align:center">
        <h2 style="color:#fff;margin:0;font-size:20px">🏥 Aadityaa Hospital</h2>
        <p style="color:#94d3c1;margin:4px 0 0;font-size:12px">Hastinapuram, Hyderabad | NABH Accredited</p>
      </div>
      <div style="padding:28px 24px;background:#f8fafb">
        <h3 style="color:#00483c;margin-top:0">✅ Appointment Confirmed!</h3>
        <p style="color:#3f4949">Dear <strong>{patient_name}</strong>,</p>
        <p style="color:#3f4949">Your appointment has been confirmed. Details below:</p>
        <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;border:1px solid #e1e3e4;margin:16px 0">
          <tr style="border-bottom:1px solid #f2f4f5">
            <td style="padding:10px 14px;color:#4c616c;font-size:13px;width:40%">Appointment ID</td>
            <td style="padding:10px 14px;font-weight:700;font-size:13px">{apt['appointment_id']}</td>
          </tr>
          <tr style="border-bottom:1px solid #f2f4f5">
            <td style="padding:10px 14px;color:#4c616c;font-size:13px">Doctor</td>
            <td style="padding:10px 14px;font-size:13px">{apt['doctor']}</td>
          </tr>
          <tr style="border-bottom:1px solid #f2f4f5">
            <td style="padding:10px 14px;color:#4c616c;font-size:13px">Specialty</td>
            <td style="padding:10px 14px;font-size:13px">{apt['specialty']}</td>
          </tr>
          <tr style="border-bottom:1px solid #f2f4f5">
            <td style="padding:10px 14px;color:#4c616c;font-size:13px">Date</td>
            <td style="padding:10px 14px;font-size:13px">{apt['date']}</td>
          </tr>
          <tr>
            <td style="padding:10px 14px;color:#4c616c;font-size:13px">Time Slot</td>
            <td style="padding:10px 14px;font-size:13px">{apt['time_slot']}</td>
          </tr>
        </table>
        <p style="color:#3f4949;font-size:13px">📞 For queries call: <strong>8886799666</strong></p>
        <p style="color:#6f7979;font-size:12px">Please carry a valid ID and arrive 15 minutes early.</p>
      </div>
      <div style="background:#eceeef;padding:14px 24px;text-align:center">
        <p style="color:#6f7979;font-size:11px;margin:0">© 2024 Aadityaa Hospital, Hastinapuram, Hyderabad</p>
      </div>
    </div>"""


# ═════════════════════════════════════════════════════════════
# STATIC FILE ROUTES
# ═════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Serve hospital_page.html at the root URL."""
    return send_from_directory(BASE_DIR, 'hospital_page.html')

@app.route('/styles.css')
def serve_css():
    return send_from_directory(BASE_DIR, 'styles.css')

@app.route('/admin')
def admin_page():
    """Serve the admin dashboard."""
    return send_from_directory(BASE_DIR, 'admin.html')


# ═════════════════════════════════════════════════════════════
# AUTH ROUTES
# ═════════════════════════════════════════════════════════════

@app.route('/api/register', methods=['POST'])
def register():
    """
    Patient Registration.
    Expects: { name, email, phone, password }

    Real life: Like registering as a new patient at hospital reception.
    You fill a form → they create your patient file → give you a Patient ID.

    What Flask does:
      1. Check email not already used
      2. Hash the password (NEVER save plain text!)
      3. Save to database
      4. Auto-login after registration
      5. Send welcome email
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data received.'}), 400

    missing = [f for f in ['name', 'email', 'phone', 'password'] if not data.get(f)]
    if missing:
        return jsonify({'success': False, 'message': f'Please fill in: {", ".join(missing)}'}), 400

    # Check if email already exists
    if User.query.filter_by(email=data['email'].lower().strip()).first():
        return jsonify({'success': False, 'message': 'An account with this email already exists. Please log in.'}), 409

    # Validate 10-digit phone
    phone = data['phone'].replace(' ', '').replace('-', '')
    if not phone.isdigit() or len(phone) != 10:
        return jsonify({'success': False, 'message': 'Enter a valid 10-digit mobile number.'}), 400

    if len(data['password']) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters.'}), 400

    # Create user
    user = User(name=data['name'].strip(), email=data['email'].lower().strip(), phone=phone)
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    # Auto-login
    session['user_id'] = user.id

    # Welcome email
    send_email(
        user.email,
        'Welcome to Aadityaa Hospital! 🏥',
        f"""<div style="font-family:Inter,sans-serif;max-width:520px;margin:auto">
          <div style="background:#00483c;padding:28px;text-align:center;border-radius:12px 12px 0 0">
            <h2 style="color:#fff;margin:0">Welcome, {user.name}! 🏥</h2>
          </div>
          <div style="padding:28px;background:#f8fafb;border-radius:0 0 12px 12px;border:1px solid #e1e3e4">
            <p>Your patient account at <strong>Aadityaa Hospital</strong> has been created.</p>
            <p>You can now book appointments online 24/7 from the comfort of your home.</p>
            <p style="color:#3f4949;font-size:13px">📞 Emergency: <strong>8886799666</strong></p>
          </div>
        </div>"""
    )

    return jsonify({'success': True, 'message': f'Welcome, {user.name}! Account created.', 'user': user.to_dict()}), 201


@app.route('/api/login', methods=['POST'])
def login():
    """
    Patient Login.
    Expects: { email, password }

    Real life: Showing your hospital card at reception.
    Flask creates a SESSION — like a wristband that says "this person is verified".
    The browser keeps this wristband (cookie) until logout.
    """
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'success': False, 'message': 'Please enter email and password.'}), 400

    user = User.query.filter_by(email=data['email'].lower().strip()).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'success': False, 'message': 'Incorrect email or password.'}), 401

    session['user_id'] = user.id
    return jsonify({'success': True, 'message': f'Welcome back, {user.name}!', 'user': user.to_dict()})


@app.route('/api/logout', methods=['POST'])
def logout():
    """Remove session. Like taking off the visitor wristband."""
    session.pop('user_id', None)
    return jsonify({'success': True, 'message': 'Logged out successfully.'})


@app.route('/api/me', methods=['GET'])
@login_required
def get_me():
    """Return the currently logged-in patient's profile."""
    return jsonify({'success': True, 'user': current_user().to_dict()})


@app.route('/api/me/phone', methods=['PUT'])
@login_required
def change_phone():
    """
    Change phone number — requires current password verification.
    Expects: { new_phone, current_password }

    This is the "special authentication" you asked for.

    Real life:
      Banks in India ask for OTP + password to change your mobile number.
      We do the same — you must provide current password before changing phone.

    Why?
      So even if someone steals your session, they can't change
      your phone number without knowing your password!
    """
    user = current_user()
    data = request.get_json()

    if not data or not data.get('new_phone') or not data.get('current_password'):
        return jsonify({'success': False, 'message': 'Provide new phone and current password.'}), 400

    # SPECIAL AUTHENTICATION STEP
    if not user.check_password(data['current_password']):
        return jsonify({'success': False, 'message': 'Incorrect password. Phone number not changed.'}), 401

    phone = data['new_phone'].replace(' ', '').replace('-', '')
    if not phone.isdigit() or len(phone) != 10:
        return jsonify({'success': False, 'message': 'Enter a valid 10-digit mobile number.'}), 400

    old_phone = user.phone
    user.phone = phone
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Phone updated from {old_phone} to {phone}.',
        'user': user.to_dict()
    })


# ═════════════════════════════════════════════════════════════
# APPOINTMENT ROUTES
# ═════════════════════════════════════════════════════════════

@app.route('/api/book', methods=['POST'])
@login_required
def book_appointment():
    """
    Book an appointment (login required).
    Expects: { specialty, doctor_id, date, time_slot, notes? }

    What happens:
      1. Validate inputs
      2. Generate appointment ID (APT1001, APT1002, ...)
      3. Save to database
      4. Send confirmation email to patient
      5. Return confirmation to browser
    """
    user = current_user()
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data received.'}), 400

    missing = [f for f in ['specialty', 'date', 'time_slot'] if not data.get(f)]
    if missing:
        return jsonify({'success': False, 'message': f'Please fill in: {", ".join(missing)}'}), 400

    doctor_id = data.get('doctor_id')
    if doctor_id and not Doctor.query.get(doctor_id):
        return jsonify({'success': False, 'message': 'Selected doctor not found.'}), 404

    apt_id  = f"APT{1000 + Appointment.query.count() + 1}"
    new_apt = Appointment(
        apt_id    = apt_id,
        user_id   = user.id,
        doctor_id = doctor_id,
        specialty = data['specialty'],
        date      = data['date'],
        time_slot = data['time_slot'],
        notes     = data.get('notes', ''),
        status    = 'Confirmed',
    )
    db.session.add(new_apt)
    db.session.commit()

    apt_dict = new_apt.to_dict()

    # Confirmation email to patient
    send_email(
        user.email,
        f"Appointment Confirmed — {apt_id} | Aadityaa Hospital",
        build_confirmation_email(apt_dict, user.name)
    )

    # Notify admin too
    send_email(
        'venkateshbonthala8055@gmail.com',
        f'New Booking: {apt_id} — {user.name} ({data["specialty"]})',
        f"<p>New appointment booked:<br><b>{user.name}</b> | {user.phone} | {data['specialty']} | {data['date']} | {data['time_slot']}</p>"
    )

    return jsonify({
        'success': True,
        'message': f'Confirmed! ID: {apt_id}. Check your email {user.email} for details.',
        'appointment': apt_dict,
    }), 201


@app.route('/api/my-appointments', methods=['GET'])
@login_required
def my_appointments():
    """All appointments of the currently logged-in patient."""
    user = current_user()
    apts = (Appointment.query
            .filter_by(user_id=user.id)
            .order_by(Appointment.booked_at.desc())
            .all())
    return jsonify({'success': True, 'appointments': [a.to_dict() for a in apts]})


@app.route('/api/appointments/<apt_id>', methods=['DELETE'])
@login_required
def cancel_appointment(apt_id):
    """Patient cancels their own appointment."""
    user = current_user()
    apt  = Appointment.query.filter_by(apt_id=apt_id.upper(), user_id=user.id).first()
    if not apt:
        return jsonify({'success': False, 'message': 'Appointment not found.'}), 404
    if apt.status == 'Cancelled':
        return jsonify({'success': False, 'message': 'Already cancelled.'}), 400
    apt.status = 'Cancelled'
    db.session.commit()
    return jsonify({'success': True, 'message': f'Appointment {apt_id} cancelled successfully.'})


# ═════════════════════════════════════════════════════════════
# DOCTORS & SPECIALTIES
# ═════════════════════════════════════════════════════════════

SPECIALTIES = ['Cardiology', 'Orthopaedics', 'Neurology', 'Paediatrics', 'Gynaecology']

@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    """Get all doctors. Optional ?specialty=Cardiology to filter."""
    sp    = request.args.get('specialty')
    query = Doctor.query
    if sp:
        query = query.filter(Doctor.specialty.ilike(f'%{sp}%'))
    docs = query.all()
    return jsonify({'success': True, 'count': len(docs), 'doctors': [d.to_dict() for d in docs]})


@app.route('/api/specialties', methods=['GET'])
def get_specialties():
    return jsonify({'success': True, 'specialties': SPECIALTIES})


# ═════════════════════════════════════════════════════════════
# CONTACT FORM
# ═════════════════════════════════════════════════════════════

@app.route('/api/contact', methods=['POST'])
def contact():
    """
    Handle contact / inquiry form.
    Saves to DB and notifies admin by email.
    """
    data = request.get_json()
    if not data or not data.get('name') or not data.get('message'):
        return jsonify({'success': False, 'message': 'Please provide name and message.'}), 400

    msg = ContactMessage(
        name    = data['name'],
        email   = data.get('email', ''),
        phone   = data.get('phone', ''),
        message = data['message'],
    )
    db.session.add(msg)
    db.session.commit()

    # Notify admin
    send_email(
        'venkateshbonthala8055@gmail.com',
        f'New Inquiry from {data["name"]} | Aadityaa Hospital',
        f"""<p><b>From:</b> {data['name']}</p>
            <p><b>Email:</b> {data.get('email','N/A')}</p>
            <p><b>Phone:</b> {data.get('phone','N/A')}</p>
            <p><b>Message:</b><br>{data['message']}</p>"""
    )

    return jsonify({
        'success': True,
        'message': f"Thank you {data['name']}! We'll respond within 24 hours. Call 8886799666 for urgent help.",
    }), 201


# ═════════════════════════════════════════════════════════════
# ADMIN ROUTES  (admin_required — only admin@aadityaa.com)
# ═════════════════════════════════════════════════════════════

@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def admin_stats():
    return jsonify({
        'success': True,
        'stats': {
            'total_patients':    User.query.filter_by(is_admin=False).count(),
            'total_doctors':     Doctor.query.count(),
            'total_apts':        Appointment.query.count(),
            'confirmed':         Appointment.query.filter_by(status='Confirmed').count(),
            'cancelled':         Appointment.query.filter_by(status='Cancelled').count(),
            'unread_messages':   ContactMessage.query.filter_by(is_read=False).count(),
        }
    })


@app.route('/api/admin/appointments', methods=['GET'])
@admin_required
def admin_appointments():
    apts = Appointment.query.order_by(Appointment.booked_at.desc()).all()
    return jsonify({'success': True, 'total': len(apts), 'appointments': [a.to_dict() for a in apts]})


@app.route('/api/admin/appointments/<apt_id>', methods=['PUT'])
@admin_required
def admin_update_apt(apt_id):
    """Admin can change any appointment's status."""
    data = request.get_json()
    apt  = Appointment.query.filter_by(apt_id=apt_id.upper()).first()
    if not apt:
        return jsonify({'success': False, 'message': 'Not found.'}), 404
    if data.get('status') in ['Confirmed', 'Cancelled', 'Completed', 'Pending']:
        apt.status = data['status']
        db.session.commit()
    return jsonify({'success': True, 'appointment': apt.to_dict()})


@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_users():
    users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()
    return jsonify({'success': True, 'total': len(users), 'users': [u.to_dict() for u in users]})


@app.route('/api/admin/messages', methods=['GET'])
@admin_required
def admin_messages():
    msgs = ContactMessage.query.order_by(ContactMessage.received_at.desc()).all()
    return jsonify({'success': True, 'messages': [m.to_dict() for m in msgs]})


@app.route('/api/admin/messages/<int:msg_id>/read', methods=['PUT'])
@admin_required
def mark_read(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    msg.is_read = True
    db.session.commit()
    return jsonify({'success': True})


# ═════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═════════════════════════════════════════════════════════════

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status':           '✅ Running',
        'hospital':         'Aadityaa Hospital, Hastinapuram, Hyderabad',
        'database':         'hospital.db (SQLite)',
        'email_ready':      MAIL_APP_PASSWORD != 'YOUR_GMAIL_APP_PASSWORD',
        'time':             datetime.now().strftime('%d %b %Y, %I:%M %p'),
        'total_patients':   User.query.filter_by(is_admin=False).count(),
        'total_apts':       Appointment.query.count(),
    })


# ═════════════════════════════════════════════════════════════
# DATABASE SEED  (runs only on first start when DB is empty)
# ═════════════════════════════════════════════════════════════

def seed_database():
    """
    Populate the database with initial doctors + admin account.
    Only runs once — when the hospital.db file is brand new.

    Real life: Like stocking the hospital with its first batch
    of doctors and creating the admin account before opening day.
    """
    if Doctor.query.count() > 0:
        return  # Already seeded — don't add duplicates!

    print('  📦 Seeding initial data (doctors + admin)...')

    doctors = [
        Doctor(
            name='Dr. Ananya Reddy', specialty='Cardiology',
            qualification='MBBS, MD Cardiology, DM Cardiology',
            experience='15+ Years', fees=800,
            available_days='Mon,Tue,Wed,Thu,Fri',
            slots='Morning (10AM-1PM),Evening (4PM-7PM)',
        ),
        Doctor(
            name='Dr. Vikram Rao', specialty='Orthopaedics',
            qualification='MS Ortho, MCh (Ortho)',
            experience='20+ Years', fees=1000,
            available_days='Mon,Wed,Fri',
            slots='Morning (10AM-1PM)',
        ),
        Doctor(
            name='Dr. Sai Pallavi', specialty='Paediatrics',
            qualification='MBBS, MD Paediatrics',
            experience='12+ Years', fees=600,
            available_days='Mon,Tue,Wed,Thu,Fri,Sat',
            slots='Morning (10AM-1PM),Evening (4PM-7PM)',
        ),
        Doctor(
            name='Dr. Ravi Kumar', specialty='Neurology',
            qualification='MBBS, MD Neurology, DM Neurology',
            experience='18+ Years', fees=1200,
            available_days='Tue,Wed,Thu',
            slots='Morning (10AM-1PM)',
        ),
        Doctor(
            name='Dr. Lakshmi Devi', specialty='Gynaecology',
            qualification='MBBS, MD Obs & Gynaecology',
            experience='14+ Years', fees=700,
            available_days='Mon,Tue,Thu,Fri,Sat',
            slots='Morning (10AM-1PM),Evening (4PM-7PM)',
        ),
    ]
    db.session.add_all(doctors)

    # Default admin account
    admin = User(name='Hospital Admin', email='admin@aadityaa.com',
                 phone='8886799666', is_admin=True)
    admin.set_password('admin123')
    db.session.add(admin)

    db.session.commit()
    print('  ✅ Seeded! 5 doctors + admin account ready.')
    print('  🔑 Admin login: admin@aadityaa.com / admin123')


# ═════════════════════════════════════════════════════════════
# START
# ═════════════════════════════════════════════════════════════

if __name__ == '__main__':
    with app.app_context():
        db.create_all()    # Create tables if hospital.db doesn't exist yet
        seed_database()    # Seed doctors + admin (only on first run)

    print('\n' + '═' * 60)
    print('  🏥  Aadityaa Hospital — Flask Backend (Full Version)')
    print('═' * 60)
    print('  🌐  Website        →  http://localhost:5000')
    print('  🔧  Admin Panel    →  http://localhost:5000/admin')
    print('  📋  Doctors API    →  http://localhost:5000/api/doctors')
    print('  ❤️   Health Check   →  http://localhost:5000/api/health')
    print('─' * 60)
    print('  🔑  Admin login    →  admin@aadityaa.com / admin123')
    print('─' * 60)
    if MAIL_APP_PASSWORD == 'YOUR_GMAIL_APP_PASSWORD':
        print('  ⚠️  EMAIL NOT SET — see MAIL_APP_PASSWORD in this file')
    else:
        print('  ✅  Email configured → venkateshbonthala8055@gmail.com')
    print('═' * 60 + '\n')
    app.run(debug=True, host='0.0.0.0', port=5000)
