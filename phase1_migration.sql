-- ============================================================
-- AADITYAA HOSPITAL — Phase 1 Migration: Roles & Surgeries
-- Run this in your Supabase Dashboard -> SQL Editor
-- ============================================================

-- 1. Add doctor roles to existing profiles table
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS is_doctor BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS doctor_id INTEGER REFERENCES doctors(id);

-- 2. Create the new Surgeries table
CREATE TABLE IF NOT EXISTS surgeries (
  id             SERIAL PRIMARY KEY,
  patient_id     UUID REFERENCES profiles(id) ON DELETE CASCADE,
  doctor_id      INTEGER REFERENCES doctors(id),
  surgery_type   TEXT NOT NULL,
  scheduled_date TEXT NOT NULL,
  status         TEXT DEFAULT 'Scheduled',
  notes          TEXT DEFAULT '',
  created_at     TIMESTAMPTZ DEFAULT now()
);

-- 3. Enable RLS on surgeries
ALTER TABLE surgeries ENABLE ROW LEVEL SECURITY;

-- 4. Update Policies for Profiles
-- Allow doctors to view profiles (just like admins can)
CREATE POLICY "Doctors view all profiles"
  ON profiles FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND is_doctor = true
    )
  );

-- 5. Update Policies for Appointments
-- Allow doctors to view and update only their assigned appointments
CREATE POLICY "Doctors see assigned appointments"
  ON appointments FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND is_doctor = true AND doctor_id = appointments.doctor_id
    )
  );

CREATE POLICY "Doctors update assigned appointments"
  ON appointments FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND is_doctor = true AND doctor_id = appointments.doctor_id
    )
  );

-- 6. Create Policies for Surgeries
-- Patients can view their own surgeries
CREATE POLICY "Patients see own surgeries"
  ON surgeries FOR SELECT
  USING (auth.uid() = patient_id);

-- Doctors can do everything with their assigned surgeries
CREATE POLICY "Doctors manage assigned surgeries"
  ON surgeries FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND is_doctor = true AND doctor_id = surgeries.doctor_id
    )
  );

-- Admins can do everything with all surgeries
CREATE POLICY "Admins manage all surgeries"
  ON surgeries FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND is_admin = true
    )
  );
