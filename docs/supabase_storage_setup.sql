-- ============================================================
-- Supabase Storage Configuration for xray-scans Bucket
-- ============================================================
-- Run this in your Supabase SQL Editor to fix storage RLS issues
-- ============================================================

-- STEP 1: Ensure the storage bucket exists and is PUBLIC
-- ============================================================
-- This should be done in the Supabase Dashboard:
-- 1. Go to Storage
-- 2. Select xray-scans bucket (or create it if it doesn't exist)
-- 3. Click "Make bucket public" (allows public READ access via URLs)
-- 
-- Or create the bucket via SQL:
-- INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
-- VALUES (
--   'xray-scans',
--   'xray-scans',
--   true,  -- Public bucket allows public read access
--   52428800,  -- 50MB file size limit
--   ARRAY['image/jpeg', 'image/jpg', 'image/png', 'application/dicom', 'application/octet-stream']
-- )
-- ON CONFLICT (id) DO UPDATE SET public = true;


-- STEP 2: Create Storage RLS Policies
-- ============================================================
-- These policies control who can upload, view, and delete files

-- OPTION A: Service Role Only (Recommended - Current Backend Implementation)
-- ============================================================
-- With this option, only the backend service role can upload/modify files
-- The bucket must be PUBLIC for images to be viewable via public URLs
-- No additional policies are needed since service_role bypasses RLS

-- The backend already uses the service role client, so this approach
-- requires NO policy changes - just ensure the bucket is PUBLIC


-- OPTION B: Allow Authenticated Users to Upload (Alternative)
-- ============================================================
-- Use this if you want users to upload directly from the frontend

-- Allow authenticated users to upload files
CREATE POLICY IF NOT EXISTS "Authenticated users can upload scans"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'xray-scans' AND
  (storage.foldername(name))[1] = 'scans'
);

-- Allow authenticated users to view all scans
-- (You might want to restrict this to only their own scans)
CREATE POLICY IF NOT EXISTS "Authenticated users can view scans"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'xray-scans');

-- Allow users to delete their own scans
CREATE POLICY IF NOT EXISTS "Dentists can delete their scans"
ON storage.objects FOR DELETE
TO authenticated
USING (
  bucket_id = 'xray-scans' AND
  EXISTS (
    SELECT 1 FROM public.scans
    WHERE scans.image_url LIKE '%' || storage.objects.name || '%'
    AND scans.dentist_id = auth.uid()
  )
);


-- OPTION C: Granular Access Control (Most Secure)
-- ============================================================
-- Users can only access scans that belong to them

-- Allow users to upload to scans folder
CREATE POLICY IF NOT EXISTS "Users upload to scans folder"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'xray-scans' AND
  (storage.foldername(name))[1] = 'scans'
);

-- Allow users to read only their own scans
CREATE POLICY IF NOT EXISTS "Users read own scans only"
ON storage.objects FOR SELECT
TO authenticated
USING (
  bucket_id = 'xray-scans' AND
  (
    -- Check if this scan belongs to the user
    EXISTS (
      SELECT 1 FROM public.scans
      WHERE scans.image_url LIKE '%' || storage.objects.name || '%'
      AND scans.dentist_id = auth.uid()
    )
    -- Or allow service role
    OR auth.role() = 'service_role'
  )
);

-- Allow users to update metadata on their own scans
CREATE POLICY IF NOT EXISTS "Users update own scans metadata"
ON storage.objects FOR UPDATE
TO authenticated
USING (
  bucket_id = 'xray-scans' AND
  EXISTS (
    SELECT 1 FROM public.scans
    WHERE scans.image_url LIKE '%' || storage.objects.name || '%'
    AND scans.dentist_id = auth.uid()
  )
);

-- Allow users to delete their own scans
CREATE POLICY IF NOT EXISTS "Users delete own scans"
ON storage.objects FOR DELETE
TO authenticated
USING (
  bucket_id = 'xray-scans' AND
  EXISTS (
    SELECT 1 FROM public.scans
    WHERE scans.image_url LIKE '%' || storage.objects.name || '%'
    AND scans.dentist_id = auth.uid()
  )
);


-- ============================================================
-- RECOMMENDED CONFIGURATION
-- ============================================================
-- For the current backend implementation (service role uploads):
-- 
-- 1. Make the bucket PUBLIC (via Dashboard)
-- 2. DO NOT add any storage policies (service role bypasses them)
-- 3. Keep the existing database RLS policies
--
-- This is the simplest and most secure approach because:
-- - Frontend cannot directly upload to storage
-- - All uploads go through authenticated backend API
-- - Backend uses service role key (bypasses RLS)
-- - Images are publicly viewable via URLs (but only if you know the URL)
-- - Database RLS prevents unauthorized access to scan records
-- ============================================================


-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================

-- Check if bucket exists and is public
SELECT id, name, public, file_size_limit, allowed_mime_types
FROM storage.buckets
WHERE id = 'xray-scans';

-- Check existing storage policies
SELECT *
FROM pg_policies
WHERE schemaname = 'storage'
AND tablename = 'objects';

-- Check if RLS is enabled on storage.objects
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'storage'
AND tablename = 'objects';

-- Count files in the bucket
SELECT bucket_id, COUNT(*) as file_count
FROM storage.objects
WHERE bucket_id = 'xray-scans'
GROUP BY bucket_id;


-- ============================================================
-- CLEANUP (if needed)
-- ============================================================

-- Drop all existing storage policies for xray-scans
-- (Run this if you want to start fresh)
/*
DROP POLICY IF EXISTS "Authenticated users can upload scans" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can view scans" ON storage.objects;
DROP POLICY IF EXISTS "Dentists can delete their scans" ON storage.objects;
DROP POLICY IF EXISTS "Users upload to scans folder" ON storage.objects;
DROP POLICY IF EXISTS "Users read own scans only" ON storage.objects;
DROP POLICY IF EXISTS "Users update own scans metadata" ON storage.objects;
DROP POLICY IF EXISTS "Users delete own scans" ON storage.objects;
DROP POLICY IF EXISTS "Public can view scans" ON storage.objects;
*/


-- ============================================================
-- NOTES
-- ============================================================
-- 1. Service role key bypasses ALL RLS policies (both database and storage)
-- 2. Anon key respects RLS policies
-- 3. Authenticated users (JWT) respect RLS policies
-- 4. Public bucket = anyone can READ files if they have the URL
-- 5. Private bucket = files are only accessible via signed URLs or if RLS allows
-- 6. The backend service role client is used in:
--    - app/core/supabase.py: get_supabase_service()
--    - app/api/scans.py: upload_scan() endpoint
-- ============================================================
