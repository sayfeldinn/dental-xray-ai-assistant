-- Align the live Supabase database with backend/database_schema.sql.
--
-- (Filename predates PART 4/5, which widened this beyond `predictions`.)
--
-- Every table was deployed from an older revision of the schema, so the live
-- database lags the checked-in one. On `predictions` that broke writes three
-- times over, each fault masking the next:
--
--   PART 1  PGRST204: Could not find the 'confirmed' column of 'predictions'
--           (the live table used `is_confirmed`)
--   PART 2  22P02: invalid input syntax for type integer: "56.81388854980469"
--           (bbox_* were INTEGER, but the detector emits floats)
--   PART 3  23514: violates check constraint "predictions_severity_check"
--           (the live check did not allow 'medium')
--
-- While those failed, save_predictions could not persist and
-- GET /scans/{id}/predictions silently fell back to `scans.findings`.
--
-- Safe to run more than once. Run in the Supabase SQL editor.

-- ---------------------------------------------------------------------------
-- PART 1 -- missing columns (already applied)
-- ---------------------------------------------------------------------------

ALTER TABLE predictions
    ADD COLUMN IF NOT EXISTS dentist_id   UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS confirmed    BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS confirmed_by UUID,
    ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP;

-- Carry across confirmations recorded under the old column name.
UPDATE predictions
   SET confirmed = is_confirmed
 WHERE is_confirmed IS NOT NULL
   AND confirmed IS DISTINCT FROM is_confirmed;

-- ---------------------------------------------------------------------------
-- PART 2 -- column types
-- ---------------------------------------------------------------------------

-- Bounding boxes are emitted in original-image pixel space and are not
-- whole numbers (e.g. 136.6339111328125). INTEGER rounds or rejects them.
ALTER TABLE predictions
    ALTER COLUMN bbox_x      TYPE REAL USING bbox_x::real,
    ALTER COLUMN bbox_y      TYPE REAL USING bbox_y::real,
    ALTER COLUMN bbox_width  TYPE REAL USING bbox_width::real,
    ALTER COLUMN bbox_height TYPE REAL USING bbox_height::real;

-- The detector reports an FDI tooth number as a string ("48"), and the API
-- type for it is Optional[str]; database_schema.sql declares VARCHAR(10).
ALTER TABLE predictions
    ALTER COLUMN tooth_number TYPE VARCHAR(10) USING tooth_number::text;

-- ---------------------------------------------------------------------------
-- PART 3 -- check constraints
-- ---------------------------------------------------------------------------

-- The deployed table carries an older severity check that rejects 'medium',
-- which is what the code assigns to every caries / pericoronal / cavity /
-- inter-radicular finding:
--
--   23514: new row for relation "predictions" violates check constraint
--          "predictions_severity_check"
--
-- The check names in the live table are unknown, so drop every CHECK on this
-- table and re-add the set database_schema.sql declares. NOT NULL (contype
-- 'n') and unique (contype 'u') constraints are untouched. Re-runnable: the
-- loop drops the constraints this script adds, then they are added again.

DO $$
DECLARE c record;
BEGIN
  FOR c IN
    SELECT conname
      FROM pg_constraint
     WHERE conrelid = 'predictions'::regclass
       AND contype = 'c'
  LOOP
    EXECUTE format('ALTER TABLE predictions DROP CONSTRAINT %I', c.conname);
  END LOOP;
END $$;

ALTER TABLE predictions
    ADD CONSTRAINT predictions_severity_check
        CHECK (severity IN ('low', 'medium', 'high', 'critical', 'mild', 'moderate', 'severe')),
    ADD CONSTRAINT predictions_confidence_check
        CHECK (confidence >= 0 AND confidence <= 1),
    ADD CONSTRAINT predictions_bbox_x_check      CHECK (bbox_x >= 0),
    ADD CONSTRAINT predictions_bbox_y_check      CHECK (bbox_y >= 0),
    ADD CONSTRAINT predictions_bbox_width_check  CHECK (bbox_width > 0),
    ADD CONSTRAINT predictions_bbox_height_check CHECK (bbox_height > 0);

-- ---------------------------------------------------------------------------
-- PART 4 -- domain CHECK constraints on the other tables
-- ---------------------------------------------------------------------------

-- predictions was not special: every table was created from the same older
-- DDL, so their value-set CHECKs may lag database_schema.sql too. Same
-- approach -- drop every CHECK on these four tables and re-add exactly the
-- domains the schema declares. The code already matches these sets
-- (GenderEnum, map_treatment_status, _coerce_action), so this cannot reject
-- anything the API actually writes. Re-runnable.

DO $$
DECLARE c record; t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['patients', 'scans', 'treatments', 'feedback'] LOOP
    FOR c IN
      SELECT conname FROM pg_constraint
       WHERE conrelid = t::regclass AND contype = 'c'
    LOOP
      EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', t, c.conname);
    END LOOP;
  END LOOP;
END $$;

ALTER TABLE patients
    ADD CONSTRAINT patients_gender_check
        CHECK (gender IN ('male', 'female', 'other'));

ALTER TABLE scans
    ADD CONSTRAINT scans_status_check
        CHECK (status IN ('pending', 'processing', 'completed', 'failed'));

ALTER TABLE treatments
    ADD CONSTRAINT treatments_status_check
        CHECK (status IN ('recommended', 'confirmed', 'in_progress', 'completed', 'cancelled'));

ALTER TABLE feedback
    ADD CONSTRAINT feedback_action_check
        CHECK (action IN ('accepted', 'rejected', 'corrected'));

-- ---------------------------------------------------------------------------
-- PART 5 -- store the detector's clinical report and quadrant boxes
-- ---------------------------------------------------------------------------

-- dentex_week3 returns an AI-generated clinical report and the four quadrant
-- boxes alongside the detections. Both were being discarded on the floor at
-- ml_service._call_api, so the Review screen had nothing to show. Persisting
-- them here means the report survives a reload instead of only existing for
-- the lifetime of one response.
ALTER TABLE scans
    ADD COLUMN IF NOT EXISTS ai_report TEXT,
    ADD COLUMN IF NOT EXISTS quadrants JSONB DEFAULT '[]'::jsonb;

-- `is_confirmed` is now unused. Dropping it is optional -- uncomment only
-- after confirming nothing else reads it.
-- ALTER TABLE predictions DROP COLUMN is_confirmed;

-- ---------------------------------------------------------------------------
-- Verify
-- ---------------------------------------------------------------------------

-- predictions: bbox_* should be `real`, tooth_number `character varying`.
SELECT table_name, column_name, data_type
  FROM information_schema.columns
 WHERE table_name IN ('predictions', 'scans')
 ORDER BY table_name, ordinal_position;

-- Every CHECK constraint across the aligned tables -- should list exactly the
-- six predictions checks plus the four domain checks added in PART 4.
SELECT conrelid::regclass AS table_name, conname
  FROM pg_constraint
 WHERE contype = 'c'
   AND conrelid::regclass::text IN
       ('patients', 'scans', 'treatments', 'feedback', 'predictions')
 ORDER BY 1, 2;
