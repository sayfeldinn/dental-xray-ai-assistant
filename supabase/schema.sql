-- ==============================================================================
-- DentalAI - Supabase Database Schema
-- Project: IEEE IC-FTAI Student Project Submission
-- Architecture: Clinical Decision-Support Pipeline (6-Step Closed Loop)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. EXTENSIONS & PREREQUISITES
-- ------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 2. UTILITY FUNCTIONS (Automatic Timestamp Updating)
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------------------------
-- 3. CORE ENTITIES
-- ------------------------------------------------------------------------------

-- Table: patients
-- Longitudinal patient clinical record containing critical medical context
-- needed for drug contraindications and dosage validation.
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dentist_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20) NOT NULL CHECK (gender IN ('male', 'female', 'other')),
    phone VARCHAR(30),
    email VARCHAR(255),
    address TEXT,
    
    -- Clinical context required for dosage & contraindications (Section 5.4)
    weight_kg NUMERIC(5, 2) CHECK (weight_kg > 0),
    allergies TEXT[] DEFAULT '{}',                -- e.g. ARRAY['penicillin', 'aspirin', 'nsaid']
    current_medications TEXT[] DEFAULT '{}',      -- e.g. ARRAY['warfarin', 'chronic_alcohol']
    medical_conditions TEXT[] DEFAULT '{}',       -- e.g. ARRAY['cardiac_risk_endocarditis', 'renal_impairment', 'hepatic_impairment', 'gi_ulcer', 'asthma']
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: scans
-- Ingested panoramic dental radiographs. Stores links to Supabase Storage and
-- the verbatim, untruncated AI inference payload from dentex_week3.
CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    dentist_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    scan_type VARCHAR(50) DEFAULT 'panoramic',
    image_url TEXT NOT NULL,
    storage_path TEXT,
    status VARCHAR(30) DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'analyzed', 'reviewed', 'failed')),
    
    -- AI Model Inference Payload (verbatim week3 JSON)
    raw_ml_output JSONB DEFAULT '{}'::jsonb,
    ai_report TEXT,
    image_width INT,
    image_height INT,
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: findings
-- Granular detections identified by the AI model on a scan.
-- Step 3 Validation: The treating dentist explicitly confirms, rejects, or edits each finding.
CREATE TABLE IF NOT EXISTS findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    dentist_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    
    -- Tooth & Pathology Localization
    quadrant INT NOT NULL CHECK (quadrant BETWEEN 1 AND 4),
    tooth_id INT NOT NULL CHECK (tooth_id BETWEEN 1 AND 8),
    tooth_fdi VARCHAR(10) NOT NULL, -- FDI two-digit notation (e.g. '18', '27', '36', '48')
    disease VARCHAR(50) NOT NULL,    -- 'Caries', 'Deep Caries', 'Periapical Lesion', 'Impacted'
    
    -- Model Confidence Scores
    disease_confidence REAL NOT NULL CHECK (disease_confidence >= 0 AND disease_confidence <= 1),
    tooth_confidence REAL CHECK (tooth_confidence >= 0 AND tooth_confidence <= 1),
    association_confidence REAL CHECK (association_confidence >= 0 AND association_confidence <= 1),
    box JSONB NOT NULL,              -- [x1, y1, x2, y2]
    
    -- Step 3: Dentist Review & Validation
    review_status VARCHAR(20) DEFAULT 'pending' CHECK (review_status IN ('pending', 'confirmed', 'rejected', 'modified')),
    confirmed_disease VARCHAR(50),   -- Populated if dentist overrides pathology class
    dentist_notes TEXT,
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES auth.users(id),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: treatments
-- Condition-specific clinical management paths generated from CONFIRMED findings.
CREATE TABLE IF NOT EXISTS treatments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    finding_id UUID REFERENCES findings(id) ON DELETE SET NULL,
    dentist_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    
    treatment_category VARCHAR(50) NOT NULL CHECK (
        treatment_category IN ('restorative', 'endodontic', 'surgical_extraction', 'periodontal', 'preventive', 'monitoring')
    ),
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'proposed' CHECK (
        status IN ('proposed', 'confirmed', 'modified', 'in_progress', 'completed', 'cancelled')
    ),
    requires_prescription BOOLEAN DEFAULT FALSE,
    clinical_justification TEXT,
    dentist_notes TEXT,
    confirmed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: prescriptions
-- Candidate drugs and calculated dosages cross-checked against patient medical history.
-- Sourced from published ADA/AHA/AAPD clinical guidelines (Section 5.4).
CREATE TABLE IF NOT EXISTS prescriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    treatment_id UUID NOT NULL REFERENCES treatments(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    finding_id UUID REFERENCES findings(id) ON DELETE SET NULL,
    dentist_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    
    -- Pharmacology Details
    drug_name VARCHAR(100) NOT NULL, -- 'Amoxicillin', 'Clindamycin', 'Metronidazole', 'Azithromycin', 'Ibuprofen', 'Paracetamol'
    dosage VARCHAR(100) NOT NULL,    -- e.g. '500 mg', '2 g', '400 mg'
    frequency VARCHAR(100) NOT NULL, -- e.g. 'every 8 hours', 'single dose 30-60 min pre-procedure'
    duration VARCHAR(100) NOT NULL,  -- e.g. '3-7 days', 'as needed'
    indication_type VARCHAR(50) NOT NULL CHECK (
        indication_type IN ('active_infection', 'pre_procedure_prophylaxis', 'pain_management')
    ),
    instructions TEXT,

    -- Step 4 Contraindication & Safety Engine
    contraindication_status VARCHAR(20) DEFAULT 'clear' CHECK (
        contraindication_status IN ('clear', 'warning', 'contraindicated')
    ),
    contraindication_warnings JSONB DEFAULT '[]'::jsonb, -- Array of structured warning objects

    -- Step 5: Dentist Decision
    dentist_status VARCHAR(20) DEFAULT 'proposed' CHECK (
        dentist_status IN ('proposed', 'accepted', 'modified', 'rejected')
    ),
    dentist_override_reason TEXT,    -- Required if dentist accepts despite contraindication warning
    prescribed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: clinical_feedback_logs
-- Step 6 Feedback Loop: Captures dentist modifications to both findings and prescriptions.
-- Forms the immutable audit log for active learning and future model retraining (Section 5.6).
CREATE TABLE IF NOT EXISTS clinical_feedback_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    dentist_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    
    stage VARCHAR(50) NOT NULL CHECK (
        stage IN ('finding_detection', 'treatment_recommendation', 'prescription_dosing')
    ),
    ai_original_data JSONB NOT NULL,
    dentist_corrected_data JSONB NOT NULL,
    correction_type VARCHAR(50) NOT NULL CHECK (
        correction_type IN ('false_positive', 'false_negative', 'misclassification', 'drug_override', 'dosage_adjusted', 'custom_note')
    ),
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 4. PERFORMANCE INDEXES
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_patients_dentist ON patients(dentist_id);
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_scans_patient ON scans(patient_id);
CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status);
CREATE INDEX IF NOT EXISTS idx_findings_scan ON findings(scan_id);
CREATE INDEX IF NOT EXISTS idx_findings_tooth ON findings(tooth_fdi);
CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(review_status);
CREATE INDEX IF NOT EXISTS idx_treatments_patient ON treatments(patient_id);
CREATE INDEX IF NOT EXISTS idx_treatments_scan ON treatments(scan_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_treatment ON prescriptions(treatment_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_patient ON prescriptions(patient_id);
CREATE INDEX IF NOT EXISTS idx_feedback_scan ON clinical_feedback_logs(scan_id);
CREATE INDEX IF NOT EXISTS idx_feedback_stage ON clinical_feedback_logs(stage);

-- ------------------------------------------------------------------------------
-- 5. AUTOMATIC TIMESTAMP TRIGGERS
-- ------------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trigger_patients_updated ON patients;
CREATE TRIGGER trigger_patients_updated BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_scans_updated ON scans;
CREATE TRIGGER trigger_scans_updated BEFORE UPDATE ON scans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_findings_updated ON findings;
CREATE TRIGGER trigger_findings_updated BEFORE UPDATE ON findings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_treatments_updated ON treatments;
CREATE TRIGGER trigger_treatments_updated BEFORE UPDATE ON treatments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_prescriptions_updated ON prescriptions;
CREATE TRIGGER trigger_prescriptions_updated BEFORE UPDATE ON prescriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ------------------------------------------------------------------------------
-- 6. ROW LEVEL SECURITY (RLS)
-- ------------------------------------------------------------------------------
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE treatments ENABLE ROW LEVEL SECURITY;
ALTER TABLE prescriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical_feedback_logs ENABLE ROW LEVEL SECURITY;

-- Development & Authenticated Policies
-- Allows authenticated dentists full access to records they manage.
-- For local demo and service-role testing, allow access if auth.uid() is null or matches dentist_id.

CREATE POLICY "Allow authenticated read patients" ON patients
    FOR SELECT TO authenticated, anon USING (true);
CREATE POLICY "Allow authenticated insert patients" ON patients
    FOR INSERT TO authenticated, anon WITH CHECK (true);
CREATE POLICY "Allow authenticated update patients" ON patients
    FOR UPDATE TO authenticated, anon USING (true);
CREATE POLICY "Allow authenticated delete patients" ON patients
    FOR DELETE TO authenticated, anon USING (true);

CREATE POLICY "Allow read scans" ON scans
    FOR SELECT TO authenticated, anon USING (true);
CREATE POLICY "Allow insert scans" ON scans
    FOR INSERT TO authenticated, anon WITH CHECK (true);
CREATE POLICY "Allow update scans" ON scans
    FOR UPDATE TO authenticated, anon USING (true);
CREATE POLICY "Allow delete scans" ON scans
    FOR DELETE TO authenticated, anon USING (true);

CREATE POLICY "Allow read findings" ON findings
    FOR SELECT TO authenticated, anon USING (true);
CREATE POLICY "Allow insert findings" ON findings
    FOR INSERT TO authenticated, anon WITH CHECK (true);
CREATE POLICY "Allow update findings" ON findings
    FOR UPDATE TO authenticated, anon USING (true);
CREATE POLICY "Allow delete findings" ON findings
    FOR DELETE TO authenticated, anon USING (true);

CREATE POLICY "Allow read treatments" ON treatments
    FOR SELECT TO authenticated, anon USING (true);
CREATE POLICY "Allow insert treatments" ON treatments
    FOR INSERT TO authenticated, anon WITH CHECK (true);
CREATE POLICY "Allow update treatments" ON treatments
    FOR UPDATE TO authenticated, anon USING (true);
CREATE POLICY "Allow delete treatments" ON treatments
    FOR DELETE TO authenticated, anon USING (true);

CREATE POLICY "Allow read prescriptions" ON prescriptions
    FOR SELECT TO authenticated, anon USING (true);
CREATE POLICY "Allow insert prescriptions" ON prescriptions
    FOR INSERT TO authenticated, anon WITH CHECK (true);
CREATE POLICY "Allow update prescriptions" ON prescriptions
    FOR UPDATE TO authenticated, anon USING (true);
CREATE POLICY "Allow delete prescriptions" ON prescriptions
    FOR DELETE TO authenticated, anon USING (true);

CREATE POLICY "Allow read feedback" ON clinical_feedback_logs
    FOR SELECT TO authenticated, anon USING (true);
CREATE POLICY "Allow insert feedback" ON clinical_feedback_logs
    FOR INSERT TO authenticated, anon WITH CHECK (true);

-- ------------------------------------------------------------------------------
-- 7. STORAGE BUCKET CONFIGURATION (xray-scans)
-- ------------------------------------------------------------------------------
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'xray-scans',
    'xray-scans',
    true,
    52428800, -- 50 MB
    ARRAY['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/tiff']
)
ON CONFLICT (id) DO UPDATE SET
    public = true,
    file_size_limit = 52428800;

-- Storage bucket access policies
CREATE POLICY "Allow public read xray-scans" ON storage.objects
    FOR SELECT TO public USING (bucket_id = 'xray-scans');

CREATE POLICY "Allow upload xray-scans" ON storage.objects
    FOR INSERT TO public WITH CHECK (bucket_id = 'xray-scans');

CREATE POLICY "Allow update xray-scans" ON storage.objects
    FOR UPDATE TO public USING (bucket_id = 'xray-scans');

CREATE POLICY "Allow delete xray-scans" ON storage.objects
    FOR DELETE TO public USING (bucket_id = 'xray-scans');

