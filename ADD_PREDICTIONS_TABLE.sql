-- Run this in Supabase SQL Editor to add the predictions table
-- This fixes the upload error and enables ML inference

-- Create predictions table
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

-- Enable RLS
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_predictions_scan_id ON predictions(scan_id);
CREATE INDEX IF NOT EXISTS idx_predictions_finding_type ON predictions(finding_type);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Predictions table created successfully! ✅';
    RAISE NOTICE 'You can now upload X-ray scans and run ML inference.';
END $$;
