-- ============================================================
--  AADITYAA HOSPITAL — Supabase Database Setup
--  Run this ONCE in: Supabase Dashboard → SQL Editor → Run
-- ============================================================

-- WHY: We create the tables here instead of in Python because
-- Supabase manages the database directly. We just tell it the structure.

-- ── 1. PROFILES TABLE (replaces your 'users' table) ──────────
-- WHY 'profiles' and not 'users'?
-- Supabase Auth already creates a built-in 'auth.users' table for login.
-- We create a 'profiles' table linked to it to store extra info
-- like name, phone, is_admin — things auth.users doesn't have.
create table if not exists profiles (
  id         uuid primary key references auth.users(id) on delete cascade,
  -- WHY uuid? Supabase Auth gives every user a UUID (e.g. "a1b2-c3d4")
  -- We use the same UUID here so they are always linked.
  name       text not null,
  phone      text,
  is_admin   boolean default false,
  created_at timestamptz default now()
);

-- ── 2. DOCTORS TABLE ─────────────────────────────────────────
create table if not exists doctors (
  id             serial primary key,
  -- WHY serial? Auto-incrementing integer ID (1, 2, 3...) — same as before
  name           text not null,
  specialty      text not null,
  qualification  text,
  experience     text,
  fees           integer,
  available_days text,   -- stored as "Mon,Tue,Wed"
  slots          text,   -- stored as "Morning (10AM-1PM),Evening (4PM-7PM)"
  created_at     timestamptz default now()
);

-- ── 3. APPOINTMENTS TABLE ─────────────────────────────────────
create table if not exists appointments (
  id         serial primary key,
  apt_id     text unique not null,   -- e.g. "APT1001"
  patient_id uuid references profiles(id) on delete cascade,
  -- WHY on delete cascade? If a patient deletes their account,
  -- their appointments are also removed automatically.
  doctor_id  integer references doctors(id),
  specialty  text,
  date       text,
  time_slot  text,
  status     text default 'Confirmed',
  notes      text default '',
  booked_at  timestamptz default now()
);

-- ── 4. CONTACT MESSAGES TABLE ─────────────────────────────────
create table if not exists contact_messages (
  id          serial primary key,
  name        text,
  email       text,
  phone       text,
  message     text,
  is_read     boolean default false,
  received_at timestamptz default now()
);

-- ── 5. LAB REPORTS TABLE (NEW — didn't exist before) ──────────
-- WHY new? Supabase Storage lets us store actual PDF files.
-- This table tracks metadata (who uploaded, when, what file).
create table if not exists lab_reports (
  id          serial primary key,
  patient_id  uuid references profiles(id) on delete cascade,
  title       text not null,
  report_type text,       -- e.g. "Blood Test", "MRI Scan", "X-Ray"
  file_path   text,       -- path in Supabase Storage bucket
  file_url    text,       -- public URL to download/view
  uploaded_at timestamptz default now()
);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- WHY? Without RLS, anyone with your API key can read ALL data.
-- RLS makes the database enforce access rules automatically —
-- even if there's a bug in your Flask code, the DB protects itself.
-- Think of it as: security inside the bank vault, not just at the door.
-- ============================================================

-- Enable RLS on all tables
alter table profiles          enable row level security;
alter table appointments      enable row level security;
alter table lab_reports       enable row level security;
alter table contact_messages  enable row level security;
-- WHY not doctors? Doctors are public info — anyone can view them.
-- No point restricting that.

-- ── PROFILES policies ────────────────────────────────────────
-- Patients can view and edit only their OWN profile
create policy "Patients view own profile"
  on profiles for select
  using (auth.uid() = id);

create policy "Patients update own profile"
  on profiles for update
  using (auth.uid() = id);

-- Admins can view all profiles
create policy "Admins view all profiles"
  on profiles for select
  using (
    exists (
      select 1 from profiles
      where id = auth.uid() and is_admin = true
    )
  );

-- ── APPOINTMENTS policies ────────────────────────────────────
-- Patients see only their own appointments
create policy "Patients see own appointments"
  on appointments for select
  using (auth.uid() = patient_id);

-- Patients can insert their own appointments
create policy "Patients book appointments"
  on appointments for insert
  with check (auth.uid() = patient_id);

-- Patients can cancel (update) their own appointments
create policy "Patients cancel own appointments"
  on appointments for update
  using (auth.uid() = patient_id);

-- Admins see all appointments
create policy "Admins see all appointments"
  on appointments for all
  using (
    exists (
      select 1 from profiles
      where id = auth.uid() and is_admin = true
    )
  );

-- ── LAB REPORTS policies ─────────────────────────────────────
-- Patients see only their own reports
create policy "Patients see own reports"
  on lab_reports for select
  using (auth.uid() = patient_id);

-- ── CONTACT MESSAGES policies ────────────────────────────────
-- Anyone can insert (submit contact form — no login needed)
create policy "Anyone can submit contact"
  on contact_messages for insert
  with check (true);

-- Only admins can read messages
create policy "Admins read messages"
  on contact_messages for select
  using (
    exists (
      select 1 from profiles
      where id = auth.uid() and is_admin = true
    )
  );

-- ============================================================
-- SEED INITIAL DOCTORS DATA
-- WHY: Same doctors you had in hospital.db, now in Supabase.
-- ============================================================

insert into doctors (name, specialty, qualification, experience, fees, available_days, slots)
values
  ('Dr. Ananya Reddy',  'Cardiology',    'MBBS, MD Cardiology, DM Cardiology', '15+ Years', 800,  'Mon,Tue,Wed,Thu,Fri',       'Morning (10AM-1PM),Evening (4PM-7PM)'),
  ('Dr. Vikram Rao',    'Orthopaedics',  'MS Ortho, MCh (Ortho)',              '20+ Years', 1000, 'Mon,Wed,Fri',               'Morning (10AM-1PM)'),
  ('Dr. Sai Pallavi',   'Paediatrics',   'MBBS, MD Paediatrics',               '12+ Years', 600,  'Mon,Tue,Wed,Thu,Fri,Sat',  'Morning (10AM-1PM),Evening (4PM-7PM)'),
  ('Dr. Ravi Kumar',    'Neurology',     'MBBS, MD Neurology, DM Neurology',   '18+ Years', 1200, 'Tue,Wed,Thu',               'Morning (10AM-1PM)'),
  ('Dr. Lakshmi Devi',  'Gynaecology',   'MBBS, MD Obs & Gynaecology',         '14+ Years', 700,  'Mon,Tue,Thu,Fri,Sat',       'Morning (10AM-1PM),Evening (4PM-7PM)')
on conflict do nothing;

-- ── STORAGE BUCKET ───────────────────────────────────────────
-- Note: Create the storage bucket via Supabase Dashboard → Storage → New Bucket
-- Bucket name: lab-reports
-- Toggle "Public bucket" ON so patients can view their report URLs
-- ============================================================
