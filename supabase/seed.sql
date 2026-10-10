-- ==============================================================================
-- DentalAI - Synthetic Demonstration Seed Data
-- Designed specifically for the IEEE Competition Demonstration Branches
-- ==============================================================================

-- Clean existing demo data if re-running
DELETE FROM clinical_feedback_logs;
DELETE FROM prescriptions;
DELETE FROM treatments;
DELETE FROM findings;
DELETE FROM scans;
DELETE FROM patients;

-- ------------------------------------------------------------------------------
-- 1. DEMO PATIENTS
-- ------------------------------------------------------------------------------

-- Patient 1: Branch A (Active Infection - Clean First-Line Amoxicillin)
-- Adult, no allergies, no hepatic/renal/cardiac contraindications.
INSERT INTO patients (
    id,
    first_name,
    last_name,
    date_of_birth,
    gender,
    phone,
    email,
    weight_kg,
    allergies,
    current_medications,
    medical_conditions,
    notes
) VALUES (
    '11111111-1111-1111-1111-111111111111',
    'Ahmed',
    'Hassan',
    '1988-04-12',
    'male',
    '+20 100 123 4567',
    'ahmed.hassan@demo.dentalai.eg',
    78.50,
    ARRAY[]::TEXT[],
    ARRAY[]::TEXT[],
    ARRAY[]::TEXT[],
    'Demo Patient 1: Clean clinical history. Used for standard first-line infection demo.'
);

-- Patient 2: Branch B (Active Infection - Penicillin Allergy Conflict)
-- Adult with documented Penicillin hypersensitivity. System MUST raise a critical
-- warning on Amoxicillin and recommend Clindamycin 300 mg qid or Azithromycin.
INSERT INTO patients (
    id,
    first_name,
    last_name,
    date_of_birth,
    gender,
    phone,
    email,
    weight_kg,
    allergies,
    current_medications,
    medical_conditions,
    notes
) VALUES (
    '22222222-2222-2222-2222-222222222222',
    'Mona',
    'El-Sayed',
    '1994-09-23',
    'female',
    '+20 101 987 6543',
    'mona.elsayed@demo.dentalai.eg',
    62.00,
    ARRAY['penicillin', 'amoxicillin']::TEXT[],
    ARRAY[]::TEXT[],
    ARRAY[]::TEXT[],
    'Demo Patient 2: Severe allergy to Penicillins. Triggers active contraindication warning.'
);

-- Patient 3: Branch C (Pre-Procedure Cardiac Prophylaxis - AHA Guideline)
-- Patient at high risk of Infective Endocarditis.
-- Must trigger single-dose Amoxicillin 2g (or Azithromycin if allergic), NOT Clindamycin (AHA 2021 update).
INSERT INTO patients (
    id,
    first_name,
    last_name,
    date_of_birth,
    gender,
    phone,
    email,
    weight_kg,
    allergies,
    current_medications,
    medical_conditions,
    notes
) VALUES (
    '33333333-3333-3333-3333-333333333333',
    'Tarek',
    'Mahmoud',
    '1965-02-18',
    'male',
    '+20 102 555 7788',
    'tarek.mahmoud@demo.dentalai.eg',
    84.00,
    ARRAY[]::TEXT[],
    ARRAY['antihypertensive']::TEXT[],
    ARRAY['prosthetic_cardiac_valve', 'infective_endocarditis_risk']::TEXT[],
    'Demo Patient 3: Cardiac risk profile requiring pre-procedure single-dose antibiotic prophylaxis.'
);

-- Patient 4: Branch D (Restorative Only - Caries with No Infection)
-- Simple carious lesions without pulpal or periapical involvement.
-- System MUST NOT recommend antibiotics or systemic drugs, only restorative filling.
INSERT INTO patients (
    id,
    first_name,
    last_name,
    date_of_birth,
    gender,
    phone,
    email,
    weight_kg,
    allergies,
    current_medications,
    medical_conditions,
    notes
) VALUES (
    '44444444-4444-4444-4444-444444444444',
    'Nour',
    'Ibrahim',
    '2001-11-05',
    'female',
    '+20 109 444 3322',
    'nour.ibrahim@demo.dentalai.eg',
    55.00,
    ARRAY[]::TEXT[],
    ARRAY[]::TEXT[],
    ARRAY[]::TEXT[],
    'Demo Patient 4: Routine examination, isolated superficial caries, restorative referral only.'
);

