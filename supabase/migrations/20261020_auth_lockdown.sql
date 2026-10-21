-- ==============================================================================
-- DentalAI - Auth lockdown (Phase 6)
-- Run once in the Supabase SQL editor of an existing project. Idempotent.
--
-- Why: the original development policies granted the `anon` and `authenticated` roles full
-- read/write on every clinical table, and the X-ray bucket was public. The frontend now ships
-- the publishable (anon) key for sign-in, so those policies would let anyone with the key read
-- and change all patient data directly through the REST API, bypassing the backend.
--
-- After this migration:
--   * Clinical tables: RLS stays ON with NO policies for anon/authenticated -> clients cannot
--     touch them. Only the backend (service-role key, which bypasses RLS) reads and writes, and it
--     enforces per-dentist ownership (backend/app/services/access.py).
--   * Storage bucket `xray-scans` is private; the backend hands out short-lived signed URLs.
-- ==============================================================================

-- 1. Drop the permissive development policies --------------------------------------------
DROP POLICY IF EXISTS "Allow authenticated read patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated insert patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated update patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated delete patients" ON patients;

DROP POLICY IF EXISTS "Allow read scans" ON scans;
DROP POLICY IF EXISTS "Allow insert scans" ON scans;
DROP POLICY IF EXISTS "Allow update scans" ON scans;
DROP POLICY IF EXISTS "Allow delete scans" ON scans;

DROP POLICY IF EXISTS "Allow read findings" ON findings;
DROP POLICY IF EXISTS "Allow insert findings" ON findings;
DROP POLICY IF EXISTS "Allow update findings" ON findings;
DROP POLICY IF EXISTS "Allow delete findings" ON findings;

DROP POLICY IF EXISTS "Allow read treatments" ON treatments;
DROP POLICY IF EXISTS "Allow insert treatments" ON treatments;
DROP POLICY IF EXISTS "Allow update treatments" ON treatments;
DROP POLICY IF EXISTS "Allow delete treatments" ON treatments;

DROP POLICY IF EXISTS "Allow read prescriptions" ON prescriptions;
DROP POLICY IF EXISTS "Allow insert prescriptions" ON prescriptions;
DROP POLICY IF EXISTS "Allow update prescriptions" ON prescriptions;
DROP POLICY IF EXISTS "Allow delete prescriptions" ON prescriptions;

DROP POLICY IF EXISTS "Allow read feedback" ON clinical_feedback_logs;
DROP POLICY IF EXISTS "Allow insert feedback" ON clinical_feedback_logs;

-- Keep RLS enabled (deny-by-default for client roles).
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE treatments ENABLE ROW LEVEL SECURITY;
ALTER TABLE prescriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical_feedback_logs ENABLE ROW LEVEL SECURITY;

-- 2. Make the X-ray bucket private ---------------------------------------------------------
UPDATE storage.buckets SET public = false WHERE id = 'xray-scans';

DROP POLICY IF EXISTS "Allow public read xray-scans" ON storage.objects;
DROP POLICY IF EXISTS "Allow upload xray-scans" ON storage.objects;
DROP POLICY IF EXISTS "Allow update xray-scans" ON storage.objects;
DROP POLICY IF EXISTS "Allow delete xray-scans" ON storage.objects;

-- 3. Audit trail: reviewer should not block deleting a user account -------------------------
ALTER TABLE findings DROP CONSTRAINT IF EXISTS findings_reviewed_by_fkey;
ALTER TABLE findings ADD CONSTRAINT findings_reviewed_by_fkey
    FOREIGN KEY (reviewed_by) REFERENCES auth.users(id) ON DELETE SET NULL;

-- Verify (should return 0 rows):
--   SELECT tablename, policyname FROM pg_policies WHERE schemaname = 'public';
-- and: SELECT public FROM storage.buckets WHERE id = 'xray-scans';  -- false
