-- ============================================================
--  AADITYAA HOSPITAL — FINAL RLS FIX
--  Run this in: Supabase Dashboard → SQL Editor → New query → Run
--
--  This permanently fixes the infinite recursion error.
--  ALL users (not just one) will be able to register and login.
-- ============================================================

-- STEP 1: Drop ALL existing broken policies first
-- ─────────────────────────────────────────────────────────────
do $$ declare
  r record;
begin
  for r in (
    select policyname, tablename
    from pg_policies
    where tablename in ('profiles','appointments','contact_messages','lab_reports')
  ) loop
    execute format('drop policy if exists %I on %I', r.policyname, r.tablename);
  end loop;
end $$;


-- STEP 2: Disable RLS on profiles completely
-- WHY? The infinite recursion happens ONLY on profiles RLS.
-- Flask uses the service_role key which should bypass RLS,
-- but to be safe we disable it so zero recursion can happen.
-- Security is still enforced by Flask @login_required decorators.
-- ─────────────────────────────────────────────────────────────
alter table profiles disable row level security;


-- STEP 3: Keep simple RLS on appointments (no self-reference)
-- These are safe — they only reference auth.uid(), never profiles again.
-- ─────────────────────────────────────────────────────────────
alter table appointments enable row level security;

create policy "own_appointments_select"
  on appointments for select
  using (auth.uid() = patient_id);

create policy "own_appointments_insert"
  on appointments for insert
  with check (auth.uid() = patient_id);

create policy "own_appointments_update"
  on appointments for update
  using (auth.uid() = patient_id);

create policy "own_appointments_delete"
  on appointments for delete
  using (auth.uid() = patient_id);


-- STEP 4: Contact messages — anyone can submit
-- ─────────────────────────────────────────────────────────────
alter table contact_messages enable row level security;

create policy "anyone_insert_contact"
  on contact_messages for insert
  with check (true);


-- STEP 5: Lab reports — patients see their own
-- ─────────────────────────────────────────────────────────────
alter table lab_reports enable row level security;

create policy "own_reports_select"
  on lab_reports for select
  using (auth.uid() = patient_id);

create policy "own_reports_insert"
  on lab_reports for insert
  with check (auth.uid() = patient_id);


-- STEP 6: Add INSERT policy for profiles
-- This allows new users to create their own profile row after registration
-- ─────────────────────────────────────────────────────────────
alter table profiles enable row level security;

create policy "own_profile_insert"
  on profiles for insert
  with check (auth.uid() = id);

create policy "own_profile_select"
  on profiles for select
  using (auth.uid() = id);

create policy "own_profile_update"
  on profiles for update
  using (auth.uid() = id);


-- ============================================================
-- VERIFY: You should see a list of policies with no recursion
-- ============================================================
select tablename, policyname, cmd
from pg_policies
where tablename in ('profiles','appointments','contact_messages','lab_reports')
order by tablename, policyname;
