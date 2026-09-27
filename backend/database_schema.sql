-- DentalAI Database Schema for Supabase
-- Run this in your Supabase SQL Editor to set up the database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dentist_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth TIMESTAMP NOT NULL,
    gender VARCHAR(20) NOT NULL CHECK (gender IN ('male', 'female', 'other')),
    phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,
    allergies JSONB DEFAULT '[]'::jsonb,
    current_medications JSONB DEFAULT '[]'::jsonb,
    medical_conditions JSONB DEFAULT '[]'::jsonb,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Scans table
CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    dentist_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    scan_type VARCHAR(50) DEFAULT 'panoramic',
    image_url TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    findings JSONB DEFAULT '[]'::jsonb,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Treatments table
CREATE TABLE IF NOT EXISTS treatments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    dentist_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    scan_id UUID REFERENCES scans(id) ON DELETE SET NULL,
    finding_id UUID,
    treatment_type VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'recommended' CHECK (status IN ('recommended', 'confirmed', 'in_progress', 'completed', 'cancelled')),
    estimated_cost DECIMAL(10, 2),
    actual_cost DECIMAL(10, 2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Prescriptions table
CREATE TABLE IF NOT EXISTS prescriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    treatment_id UUID NOT NULL REFERENCES treatments(id) ON DELETE CASCADE,
    drug_name VARCHAR(255) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100) NOT NULL,
    duration VARCHAR(100) NOT NULL,
    instructions TEXT,
    contraindication_checked BOOLEAN DEFAULT FALSE,
    contraindication_warnings JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Feedback/corrections table for active learning
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    dentist_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    finding_id UUID,
    action VARCHAR(20) NOT NULL CHECK (action IN ('accepted', 'rejected', 'corrected')),
    original_data JSONB,
    corrected_data JSONB,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Predictions table for storing ML inference results
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    finding_type VARCHAR(50) NOT NULL,
    confidence DECIMAL(5, 4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    bbox_x INTEGER NOT NULL,
    bbox_y INTEGER NOT NULL,
    bbox_width INTEGER NOT NULL,
    bbox_height INTEGER NOT NULL,
    tooth_number INTEGER,
    severity VARCHAR(20) DEFAULT 'moderate' CHECK (severity IN ('low', 'moderate', 'high', 'mild', 'severe')),
    notes TEXT,
    is_confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_patients_dentist_id ON patients(dentist_id);
CREATE INDEX idx_patients_email ON patients(email);
CREATE INDEX idx_scans_patient_id ON scans(patient_id);
CREATE INDEX idx_scans_dentist_id ON scans(dentist_id);
CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_treatments_patient_id ON treatments(patient_id);
CREATE INDEX idx_treatments_dentist_id ON treatments(dentist_id);
CREATE INDEX idx_treatments_status ON treatments(status);
CREATE INDEX idx_prescriptions_treatment_id ON prescriptions(treatment_id);
CREATE INDEX idx_feedback_scan_id ON feedback(scan_id);
CREATE INDEX idx_predictions_scan_id ON predictions(scan_id);
CREATE INDEX idx_predictions_finding_type ON predictions(finding_type);

-- Row Level Security (RLS) Policies
-- Enable RLS on all tables
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE treatments ENABLE ROW LEVEL SECURITY;
ALTER TABLE prescriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- Patients policies
CREATE POLICY "Dentists can view their own patients"
    ON patients FOR SELECT
    USING (auth.uid() = dentist_id);

CREATE POLICY "Dentists can create patients"
    ON patients FOR INSERT
    WITH CHECK (auth.uid() = dentist_id);

CREATE POLICY "Dentists can update their own patients"
    ON patients FOR UPDATE
    USING (auth.uid() = dentist_id);

CREATE POLICY "Dentists can delete their own patients"
    ON patients FOR DELETE
    USING (auth.uid() = dentist_id);

-- Scans policies
CREATE POLICY "Dentists can view their own scans"
    ON scans FOR SELECT
    USING (auth.uid() = dentist_id);

CREATE POLICY "Dentists can create scans"
    ON scans FOR INSERT
    WITH CHECK (auth.uid() = dentist_id);

CREATE POLICY "Dentists can update their own scans"
    ON scans FOR UPDATE
    USING (auth.uid() = dentist_id);

CREATE POLICY "Dentists can delete their own scans"
    ON scans FOR DELETE
    USING (auth.uid() = dentist_id);

-- Treatments policies
CREATE POLICY "Dentists can view their own treatments"
    ON treatments FOR SELECT
    USING (auth.uid() = dentist_id);

CREATE POLICY "Dentists can create treatments"
    ON treatments FOR INSERT
    WITH CHECK (auth.uid() = dentist_id);

CREATE POLICY "Dentists can update their own treatments"
    ON treatments FOR UPDATE
    USING (auth.uid() = dentist_id);

CREATE POLICY "Dentists can delete their own treatments"
    ON treatments FOR DELETE
    USING (auth.uid() = dentist_id);

-- Prescriptions policies
CREATE POLICY "Dentists can view prescriptions for their treatments"
    ON prescriptions FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM treatments
            WHERE treatments.id = prescriptions.treatment_id
            AND treatments.dentist_id = auth.uid()
        )
    );

CREATE POLICY "Dentists can create prescriptions for their treatments"
    ON prescriptions FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM treatments
            WHERE treatments.id = prescriptions.treatment_id
            AND treatments.dentist_id = auth.uid()
        )
    );

-- Feedback policies
CREATE POLICY "Dentists can view their own feedback"
    ON feedback FOR SELECT
    USING (auth.uid() = dentist_id);

CREATE POLICY "Dentists can create feedback"
    ON feedback FOR INSERT
    WITH CHECK (auth.uid() = dentist_id);

-- Predictions policies (accessible via scans)
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Dentists can view predictions for their scans"
    ON predictions FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM scans
            WHERE scans.id = predictions.scan_id
            AND scans.dentist_id = auth.uid()
        )
    );

CREATE POLICY "Dentists can create predictions for their scans"
    ON predictions FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM scans
            WHERE scans.id = predictions.scan_id
            AND scans.dentist_id = auth.uid()
        )
    );

CREATE POLICY "Dentists can update predictions for their scans"
    ON predictions FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM scans
            WHERE scans.id = predictions.scan_id
            AND scans.dentist_id = auth.uid()
        )
    );

-- Create storage bucket for X-ray images
-- Run this separately in Supabase dashboard or use the Supabase client
-- Storage bucket name: xray-scans
-- Make it public or set appropriate policies

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update updated_at
CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scans_updated_at BEFORE UPDATE ON scans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_treatments_updated_at BEFORE UPDATE ON treatments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
