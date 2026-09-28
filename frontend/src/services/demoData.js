/**
 * Demo-mode fixtures.
 *
 * Used only when VITE_DEMO_MODE=true. Values follow the QA draft profiles in
 * docs/qa/synthetic-patient-profiles.md (P-001 ... P-006) and the draft
 * six-drug list in the same document. Everything here is synthetic.
 */

export const DEMO_IMAGE = '/demo/panorama-xray.jpg';

// Original image is 640x336, so every bbox below stays inside that box.
const PATIENTS = [
  {
    id: 'p-001',
    first_name: 'Sara',
    last_name: 'M.',
    email: 'sara.m@example.com',
    phone: '+1 555 0101',
    contact_number: '+1 555 0101',
    date_of_birth: '1998-04-12',
    gender: 'female',
    age: 28,
    allergies: [],
    current_medications: [],
    medical_conditions: [],
    medical_history: [],
    notes: 'Non-smoker, no alcohol. Recall every 6 months.',
  },
  {
    id: 'p-002',
    first_name: 'Omar',
    last_name: 'H.',
    email: 'omar.h@example.com',
    phone: '+1 555 0102',
    contact_number: '+1 555 0102',
    date_of_birth: '1991-07-30',
    gender: 'male',
    age: 35,
    allergies: [],
    current_medications: [],
    medical_conditions: [],
    medical_history: [],
    notes: 'Reports cold sensitivity on the lower left quadrant.',
  },
  {
    id: 'p-003',
    first_name: 'Nour',
    last_name: 'A.',
    email: 'nour.a@example.com',
    phone: '+1 555 0103',
    contact_number: '+1 555 0103',
    date_of_birth: '2007-02-19',
    gender: 'female',
    age: 19,
    allergies: ['penicillin'],
    current_medications: [],
    medical_conditions: ['atopic eczema'],
    medical_history: [
      { condition: 'Atopic eczema', contraindications: [] },
    ],
    notes: 'Penicillin allergy recorded as childhood rash (non-anaphylactic).',
  },
  {
    id: 'p-004',
    first_name: 'Mahmoud',
    last_name: 'S.',
    email: 'mahmoud.s@example.com',
    phone: '+1 555 0104',
    contact_number: '+1 555 0104',
    date_of_birth: '1954-11-05',
    gender: 'male',
    age: 72,
    allergies: [],
    current_medications: [
      'Warfarin 5 mg daily',
      'Amlodipine 5 mg daily',
      'Atorvastatin 20 mg nightly',
    ],
    medical_conditions: ['atrial fibrillation', 'hypertension', 'hyperlipidemia'],
    medical_history: [
      { condition: 'Atrial fibrillation (Warfarin 5 mg daily)', contraindications: ['Ibuprofen'] },
      { condition: 'Hypertension', contraindications: [] },
      { condition: 'Hyperlipidemia', contraindications: [] },
    ],
    notes: 'Ex-smoker. INR check required before any surgical procedure.',
  },
  {
    id: 'p-005',
    first_name: 'Youssef',
    last_name: 'A.',
    email: 'youssef.a@example.com',
    phone: '+1 555 0105',
    contact_number: '+1 555 0105',
    date_of_birth: '2020-06-22',
    gender: 'male',
    age: 6,
    allergies: [],
    current_medications: [],
    medical_conditions: [],
    medical_history: [],
    notes: 'Pediatric patient, 18 kg. Guardian present at every visit.',
  },
  {
    id: 'p-006',
    first_name: 'Rania',
    last_name: 'K.',
    email: 'rania.k@example.com',
    phone: '+1 555 0106',
    contact_number: '+1 555 0106',
    date_of_birth: '1981-09-08',
    gender: 'female',
    age: 45,
    allergies: ['sulfa'],
    current_medications: ['Metformin 1000 mg daily'],
    medical_conditions: ['Type 2 diabetes, well controlled (HbA1c 6.4%)'],
    medical_history: [
      { condition: 'Type 2 diabetes, well controlled', contraindications: [] },
    ],
    notes: 'Sulfa allergy (rash). Must not trigger a warning for unrelated drugs.',
  },
];

const SCANS = [
  {
    id: 's-001',
    patient_id: 'p-002',
    patient_name: 'Omar H.',
    scan_type: 'panoramic',
    image_url: DEMO_IMAGE,
    status: 'completed',
    notes: 'Lower left quadrant pain, cold sensitive.',
    created_at: '2026-09-18T09:24:00.000Z',
    updated_at: '2026-09-18T09:31:00.000Z',
  },
  {
    id: 's-002',
    patient_id: 'p-004',
    patient_name: 'Mahmoud S.',
    scan_type: 'panoramic',
    image_url: DEMO_IMAGE,
    status: 'pending',
    notes: 'Pre-extraction assessment, tooth 26.',
    created_at: '2026-09-24T14:02:00.000Z',
    updated_at: '2026-09-24T14:02:00.000Z',
  },
  {
    id: 's-003',
    patient_id: 'p-003',
    patient_name: 'Nour A.',
    scan_type: 'panoramic',
    image_url: DEMO_IMAGE,
    status: 'reviewed',
    notes: 'Pericoronitis around 38, penicillin allergy on file.',
    created_at: '2026-09-26T11:47:00.000Z',
    updated_at: '2026-09-26T12:10:00.000Z',
  },
];

const PREDICTIONS = {
  's-001': [
    {
      id: 'f-101',
      finding_type: 'caries',
      confidence: 0.87,
      severity: 'medium',
      tooth_number: '36',
      notes: 'Radiolucency at the occlusal surface extending toward the pulp chamber.',
      bbox_x: 288,
      bbox_y: 158,
      bbox_width: 58,
      bbox_height: 50,
      confirmed: true,
    },
    {
      id: 'f-102',
      finding_type: 'periapical',
      confidence: 0.74,
      severity: 'high',
      tooth_number: '36',
      notes: 'Periapical radiolucency at the apex — possible chronic apical periodontitis.',
      bbox_x: 300,
      bbox_y: 224,
      bbox_width: 52,
      bbox_height: 44,
      confirmed: true,
    },
    {
      id: 'f-103',
      finding_type: 'pericoronal',
      confidence: 0.61,
      severity: 'low',
      tooth_number: '38',
      notes: 'Soft tissue shadow around the distal of the lower left third molar.',
      bbox_x: 150,
      bbox_y: 196,
      bbox_width: 56,
      bbox_height: 48,
      confirmed: false,
    },
  ],
  's-002': [
    {
      id: 'f-201',
      finding_type: 'caries',
      confidence: 0.79,
      severity: 'high',
      tooth_number: '26',
      notes: 'Extensive caries with gross destruction of the crown.',
      bbox_x: 430,
      bbox_y: 120,
      bbox_width: 62,
      bbox_height: 54,
      confirmed: false,
    },
    {
      id: 'f-202',
      finding_type: 'periapical',
      confidence: 0.68,
      severity: 'medium',
      tooth_number: '26',
      notes: 'Widened periodontal ligament space at the apex.',
      bbox_x: 444,
      bbox_y: 76,
      bbox_width: 50,
      bbox_height: 42,
      confirmed: false,
    },
  ],
  's-003': [
    {
      id: 'f-301',
      finding_type: 'pericoronal',
      confidence: 0.83,
      severity: 'medium',
      tooth_number: '38',
      notes: 'Operculum over the partially erupted 38, consistent with pericoronitis.',
      bbox_x: 158,
      bbox_y: 200,
      bbox_width: 56,
      bbox_height: 48,
      confirmed: true,
    },
    {
      id: 'f-302',
      finding_type: 'inter_radicular',
      confidence: 0.52,
      severity: 'low',
      tooth_number: '46',
      notes: 'Possible early inter-radicular bone loss — low confidence, review clinically.',
      bbox_x: 386,
      bbox_y: 214,
      bbox_width: 54,
      bbox_height: 44,
      confirmed: false,
    },
  ],
};

const DRUGS = {
  amoxicillin: { name: 'Amoxicillin', dosage: '500 mg q8h for 5-7 days' },
  azithromycin: { name: 'Azithromycin', dosage: '500 mg day 1, then 250 mg daily' },
  metronidazole: { name: 'Metronidazole', dosage: '500 mg q8h for 5-7 days' },
  paracetamol: { name: 'Paracetamol', dosage: '500 mg q6h (max 4 g/day)' },
  ibuprofen: { name: 'Ibuprofen', dosage: '400 mg q8h with food' },
  dexamethasone: { name: 'Dexamethasone', dosage: '4 mg daily for 3 days' },
};

const MEANING = {
  caries: 'Deep caries with possible pulpal involvement',
  periapical: 'Periapical radiolucency',
  pericoronal: 'Pericoronal / pericoronitis changes',
  inter_radicular: 'Inter-radicular bone loss',
  non_odontogenic: 'Non-odontogenic finding',
};

function pickAntibiotic(patient) {
  const allergies = (patient.allergies || []).map((a) => a.toLowerCase());
  if (allergies.includes('penicillin')) {
    return {
      drugs: [DRUGS.azithromycin],
      warning: 'R-01: penicillin allergy on file - amoxicillin is contraindicated. Draft alternative: azithromycin.',
    };
  }
  return { drugs: [DRUGS.amoxicillin], warning: null };
}

function pickAnalgesic(patient) {
  const meds = (patient.current_medications || []).join(' ').toLowerCase();
  const age = patient.age || 0;
  if (meds.includes('warfarin')) {
    return {
      // Draft proposal first, safe alternative second - the Treatments page
      // flags Ibuprofen against the patient's recorded contraindications.
      drugs: [DRUGS.ibuprofen, DRUGS.paracetamol],
      warning: 'R-02: NSAIDs plus warfarin raise bleeding risk and R-03 applies at age 65+. Paracetamol offered instead.',
    };
  }
  if (age < 12) {
    return {
      drugs: [DRUGS.paracetamol],
      warning: 'R-04: patient under 12 - adult 400 mg ibuprofen dose is forbidden. Weight-based dosing only.',
    };
  }
  return { drugs: [DRUGS.paracetamol], warning: null };
}

const TREATMENT_BY_FINDING = {
  caries: 'Restoration if restorable, otherwise extraction with antibiotic cover and analgesia.',
  periapical: 'Root canal treatment or extraction; antibiotic cover if infection is spreading.',
  pericoronal: 'Irrigation and operculectomy if symptomatic, plus antibiotic cover and analgesia.',
  inter_radicular: 'Periodontal assessment and scaling; monitor radiographically.',
  non_odontogenic: 'Refer for further imaging before any intervention.',
};

/**
 * Build the treatment recommendation list the Treatments page expects.
 * Mirrors the draft mapping in docs/qa/synthetic-patient-profiles.md.
 */
export function buildRecommendations(patient, predictions) {
  const recommendations = predictions.map((pred) => {
    const abi = pickAntibiotic(patient);
    const analgesic = pickAnalgesic(patient);
    const needsDrug = pred.finding_type !== 'inter_radicular' && pred.finding_type !== 'non_odontogenic';

    const medications = [];
    const recWarnings = [];

    if (needsDrug) {
      medications.push(...abi.drugs);
      if (abi.warning) recWarnings.push(abi.warning);

      medications.push(...analgesic.drugs);
      if (analgesic.warning) recWarnings.push(analgesic.warning);
    }

    if (pred.finding_type === 'pericoronal' && (patient.age || 0) >= 12) {
      medications.push(DRUGS.dexamethasone);
    }

    const notes = [
      MEANING[pred.finding_type] || 'AI-detected finding',
      ...recWarnings,
      'Draft mapping only - pending dentist validation (issue #11).',
    ];

    return {
      prediction_id: pred.id,
      finding_type: pred.finding_type,
      severity: pred.severity,
      tooth_number: pred.tooth_number,
      confidence: pred.confidence,
      treatment: TREATMENT_BY_FINDING[pred.finding_type] || 'Clinical review required.',
      medications,
      notes: notes.join(' · '),
    };
  });

  return { recommendations };
}

export function getPatients() {
  return PATIENTS.map((p) => ({ ...p }));
}

export function getScans() {
  return SCANS.map((s) => ({ ...s }));
}

export function getPredictions(scanId) {
  return (PREDICTIONS[scanId] || []).map((p) => ({ ...p }));
}
