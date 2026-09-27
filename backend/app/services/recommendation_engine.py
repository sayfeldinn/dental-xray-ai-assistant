"""
Clinical Recommendation Engine.
Maps AI findings (5 model classes) to evidence-based dental treatment protocols,
screens drug allergies and co-medication interactions, and provides contraindication warnings.
All recommendations carry mandatory '[Pending Clinical Validation]' tags.
"""
from typing import Dict, List, Optional
from app.schemas.scan import Finding, FindingTypeEnum, FindingSeverityEnum
from app.schemas.treatment import TreatmentCreate, PrescriptionCreate


class RecommendationEngine:
    """
    Recommendation Engine for dental treatments and prescriptions.
    Week 2: Supports 5 YOLO model classes, allergy substitutions, and drug interaction warnings.
    """
    
    FINDING_TO_TREATMENT_MAP: Dict[FindingTypeEnum, Dict] = {
        # 1. Caries / Cavity
        FindingTypeEnum.CARIES: {
            "mild": {
                "treatment": "Composite Dental Restoration",
                "description": "[Pending Clinical Validation] Conservative resin restoration for superficial enamel caries.",
                "estimated_cost": 350.0,
                "drugs": []
            },
            "moderate": {
                "treatment": "Direct Resin Restoration & Pulp Protection",
                "description": "[Pending Clinical Validation] Excavation of dentinal caries with therapeutic liner and restoration.",
                "estimated_cost": 650.0,
                "drugs": ["Ibuprofen"]
            },
            "severe": {
                "treatment": "Endodontic Therapy (Root Canal) & Crown",
                "description": "[Pending Clinical Validation] Deep pulpal involvement requiring complete chemo-mechanical debridement, obturation, and cuspal coverage.",
                "estimated_cost": 1800.0,
                "drugs": ["Amoxicillin", "Ibuprofen"]
            }
        },
        FindingTypeEnum.CAVITY: {
            "mild": {
                "treatment": "Composite Dental Restoration",
                "description": "[Pending Clinical Validation] Conservative resin restoration for superficial enamel caries.",
                "estimated_cost": 350.0,
                "drugs": []
            },
            "moderate": {
                "treatment": "Direct Resin Restoration & Pulp Protection",
                "description": "[Pending Clinical Validation] Excavation of dentinal caries with therapeutic liner and restoration.",
                "estimated_cost": 650.0,
                "drugs": ["Ibuprofen"]
            },
            "severe": {
                "treatment": "Endodontic Therapy (Root Canal) & Crown",
                "description": "[Pending Clinical Validation] Deep pulpal involvement requiring complete chemo-mechanical debridement, obturation, and cuspal coverage.",
                "estimated_cost": 1800.0,
                "drugs": ["Amoxicillin", "Ibuprofen"]
            }
        },
        # 2. Periapical Lesion
        FindingTypeEnum.PERIAPICAL: {
            "mild": {
                "treatment": "Endodontic Diagnostic Workup & Vitality Testing",
                "description": "[Pending Clinical Validation] Apical periodontitis assessment with selective diagnostic radiographs.",
                "estimated_cost": 450.0,
                "drugs": ["Ibuprofen"]
            },
            "moderate": {
                "treatment": "Root Canal Therapy",
                "description": "[Pending Clinical Validation] Chemo-mechanical preparation and intracanal medicament dressing.",
                "estimated_cost": 1400.0,
                "drugs": ["Amoxicillin", "Ibuprofen"]
            },
            "severe": {
                "treatment": "Surgical Apicoectomy / Drainage & Root Canal",
                "description": "[Pending Clinical Validation] Periapical abscess intervention, apical resection, and retrograde sealing.",
                "estimated_cost": 2200.0,
                "drugs": ["Amoxicillin", "Metronidazole", "Ibuprofen"]
            }
        },
        # 3. Pericoronal Lesion / Pericoronitis
        FindingTypeEnum.PERICORONAL: {
            "mild": {
                "treatment": "Subgingival Debridement & Antiseptic Irrigation",
                "description": "[Pending Clinical Validation] Mechanical debridement of pericoronal flap with chlorhexidine lavage.",
                "estimated_cost": 250.0,
                "drugs": ["Chlorhexidine"]
            },
            "moderate": {
                "treatment": "Operculectomy & Deep Irrigation",
                "description": "[Pending Clinical Validation] Surgical excision of mucosal operculum to eliminate plaque trap.",
                "estimated_cost": 600.0,
                "drugs": ["Amoxicillin", "Ibuprofen"]
            },
            "severe": {
                "treatment": "Surgical Extraction of Impacted Molar",
                "description": "[Pending Clinical Validation] Surgical extraction of symptomatic impacted third molar with primary closure.",
                "estimated_cost": 1600.0,
                "drugs": ["Amoxicillin", "Metronidazole", "Ibuprofen"]
            }
        },
        # 4. Inter-Radicular Lesion / Furcation
        FindingTypeEnum.INTER_RADICULAR: {
            "mild": {
                "treatment": "Periodontal Scaling and Root Planing",
                "description": "[Pending Clinical Validation] Ultrasonic and hand debridement of interradicular furcation areas.",
                "estimated_cost": 400.0,
                "drugs": ["Chlorhexidine"]
            },
            "moderate": {
                "treatment": "Periodontal Flap Debridement & Bone Grafting",
                "description": "[Pending Clinical Validation] Open flap curettage with guided tissue regeneration in Class II furcation defect.",
                "estimated_cost": 1200.0,
                "drugs": ["Amoxicillin", "Ibuprofen"]
            },
            "severe": {
                "treatment": "Root Resection / Hemisection or Extraction",
                "description": "[Pending Clinical Validation] Advanced bone loss spanning furcation; hemisection or extraction planned.",
                "estimated_cost": 2100.0,
                "drugs": ["Amoxicillin", "Metronidazole", "Ibuprofen"]
            }
        },
        # 5. Non-Odontogenic Lesion
        FindingTypeEnum.NON_ODONTOGENIC: {
            "mild": {
                "treatment": "Periodic Clinical Monitoring & Baseline Radiographs",
                "description": "[Pending Clinical Validation] Benign radiolucency / fibro-osseous finding requiring non-invasive periodic monitoring.",
                "estimated_cost": 150.0,
                "drugs": []  # Clean / No-drug branch
            },
            "moderate": {
                "treatment": "Cone Beam CT (CBCT) & Diagnostic Incisional Biopsy",
                "description": "[Pending Clinical Validation] 3D volumetric mapping and tissue biopsy for histopathological evaluation.",
                "estimated_cost": 850.0,
                "drugs": []
            },
            "severe": {
                "treatment": "Oral & Maxillofacial Surgical Consult & Excision",
                "description": "[Pending Clinical Validation] Comprehensive referral for definitive surgical enucleation or resection.",
                "estimated_cost": 2800.0,
                "drugs": ["Ibuprofen"]
            }
        },
        # Legacy mappings
        FindingTypeEnum.ROOT_CANAL: {
            "moderate": {
                "treatment": "Root Canal Treatment",
                "description": "[Pending Clinical Validation] Root canal therapy with crown",
                "estimated_cost": 2500.0,
                "drugs": ["Amoxicillin", "Ibuprofen"]
            },
            "severe": {
                "treatment": "Root Canal Treatment or Extraction",
                "description": "[Pending Clinical Validation] Severe infection, may require extraction",
                "estimated_cost": 3000.0,
                "drugs": ["Amoxicillin", "Metronidazole", "Ibuprofen"]
            }
        },
        FindingTypeEnum.EXTRACTION: {
            "moderate": {
                "treatment": "Tooth Extraction",
                "description": "[Pending Clinical Validation] Simple extraction",
                "estimated_cost": 1000.0,
                "drugs": ["Amoxicillin", "Ibuprofen"]
            },
            "severe": {
                "treatment": "Surgical Extraction",
                "description": "[Pending Clinical Validation] Complex surgical extraction",
                "estimated_cost": 2000.0,
                "drugs": ["Amoxicillin", "Ibuprofen", "Codeine"]
            }
        }
    }
    
    DRUGS_DATABASE: Dict[str, Dict] = {
        "Amoxicillin": {
            "category": "beta-lactam antibiotic",
            "default_dosage": "500mg",
            "default_frequency": "Every 8 hours (3 times daily)",
            "default_duration": "7 days",
            "contraindications": ["penicillin_allergy", "amoxicillin_allergy"],
            "interactions": []
        },
        "Azithromycin": {
            "category": "macrolide antibiotic",
            "default_dosage": "500mg Day 1, then 250mg daily",
            "default_frequency": "Once daily",
            "default_duration": "5 days",
            "contraindications": ["macrolide_allergy", "qt_prolongation"],
            "interactions": ["amiodarone", "pimozide"]
        },
        "Metronidazole": {
            "category": "nitroimidazole antibiotic",
            "default_dosage": "400mg",
            "default_frequency": "Every 8 hours (3 times daily)",
            "default_duration": "5 days",
            "contraindications": ["alcohol_use", "pregnancy_first_trimester"],
            "interactions": ["warfarin", "alcohol"]
        },
        "Ibuprofen": {
            "category": "nsaid",
            "default_dosage": "400mg",
            "default_frequency": "Every 6-8 hours as needed",
            "default_duration": "5 days",
            "contraindications": ["nsaid_allergy", "active_ulcer", "severe_kidney_disease"],
            "interactions": ["warfarin", "aspirin", "anticoagulants"]
        },
        "Paracetamol": {
            "category": "analgesic / antipyretic",
            "default_dosage": "500mg - 1000mg",
            "default_frequency": "Every 6 hours as needed (max 4g/day)",
            "default_duration": "5 days",
            "contraindications": ["severe_liver_disease"],
            "interactions": []
        },
        "Chlorhexidine": {
            "category": "antiseptic oral rinse",
            "default_dosage": "15ml 0.12%",
            "default_frequency": "Twice daily after meals",
            "default_duration": "10 days",
            "contraindications": [],
            "interactions": []
        },
        "Codeine": {
            "category": "opioid",
            "default_dosage": "30mg",
            "default_frequency": "Every 4-6 hours as needed",
            "default_duration": "3 days",
            "contraindications": ["respiratory_depression", "acute_asthma", "pregnancy"],
            "interactions": ["alcohol", "benzodiazepines"]
        }
    }
    
    @staticmethod
    def _normalize_severity(sev_val: str) -> str:
        s = str(sev_val).lower()
        if s in ("low", "mild"):
            return "mild"
        elif s in ("high", "severe", "critical"):
            return "severe"
        return "moderate"

    def recommend_treatment(
        self, 
        finding: Finding,
        patient_allergies: Optional[List[str]] = None,
        patient_medications: Optional[List[str]] = None,
        patient_conditions: Optional[List[str]] = None
    ) -> Optional[TreatmentCreate]:
        """
        Generate treatment recommendation based on finding and patient context.
        """
        treatment_map = self.FINDING_TO_TREATMENT_MAP.get(finding.type)
        if not treatment_map:
            return None
        
        normalized_sev = self._normalize_severity(finding.severity.value)
        treatment_info = treatment_map.get(normalized_sev) or treatment_map.get("moderate") or treatment_map.get("mild")
        if not treatment_info:
            return None
        
        prescriptions = []
        for drug_name in treatment_info.get("drugs", []):
            drug_info = self.DRUGS_DATABASE.get(drug_name)
            if not drug_info:
                continue

            warnings = self._check_contraindications(
                drug_name=drug_name,
                drug_info=drug_info,
                patient_allergies=patient_allergies or [],
                patient_medications=patient_medications or [],
                patient_conditions=patient_conditions or []
            )
            
            prescription = PrescriptionCreate(
                drug_name=drug_name,
                dosage=drug_info["default_dosage"],
                frequency=drug_info["default_frequency"],
                duration=drug_info["default_duration"],
                instructions=f"⚠️ {'; '.join(warnings)}" if warnings else "[Pending Clinical Validation] Take with water after meals."
            )
            prescriptions.append(prescription)
        
        treatment = TreatmentCreate(
            patient_id="",
            treatment_type=treatment_info["treatment"],
            description=treatment_info["description"],
            estimated_cost=treatment_info["estimated_cost"],
            prescriptions=prescriptions,
            notes=f"[Pending Clinical Validation] AI-recommended based on {finding.type.value} with {finding.severity.value} severity."
        )
        
        return treatment
    
    def _check_contraindications(
        self,
        drug_name: str,
        drug_info: Dict,
        patient_allergies: List[str],
        patient_medications: List[str],
        patient_conditions: List[str]
    ) -> List[str]:
        warnings = []
        
        # 1. Check conditions
        for contra in drug_info.get("contraindications", []):
            contra_clean = contra.replace("_", " ").lower()
            if any(contra_clean in c.lower() for c in patient_conditions):
                warnings.append(f"Contraindicated with condition: {contra_clean}")
            
            # 2. Check allergies
            if "allergy" in contra:
                for allergy in patient_allergies:
                    allergy_lower = allergy.lower()
                    if ("penicillin" in allergy_lower and drug_name in ("Amoxicillin", "Ampicillin")) or \
                       (allergy_lower in contra) or \
                       ("nsaid" in allergy_lower and drug_name in ("Ibuprofen", "Aspirin")):
                        warnings.append(
                            f"Allergy alert: {drug_name} contraindicated due to {allergy} allergy. Consider Azithromycin."
                        )
                        break
        
        # 3. Check drug interactions
        for interaction in drug_info.get("interactions", []):
            for med in patient_medications:
                if interaction.lower() in med.lower():
                    if drug_name == "Ibuprofen" and "warfarin" in med.lower():
                        warnings.append(
                            f"Drug interaction: Ibuprofen co-administered with Warfarin increases bleed risk. Substitute Paracetamol."
                        )
                    else:
                        warnings.append(f"Drug interaction: {drug_name} with {interaction} in {med}")
                    break
        
        return list(dict.fromkeys(warnings))
    
    def check_prescription_safety(
        self,
        drug_name: str,
        patient_allergies: Optional[List[str]] = None,
        patient_medications: Optional[List[str]] = None,
        patient_conditions: Optional[List[str]] = None
    ) -> Dict:
        drug_info = self.DRUGS_DATABASE.get(drug_name)
        if not drug_info:
            return {
                "safe": False,
                "warnings": [f"Drug '{drug_name}' not found in database"]
            }
        
        warnings = self._check_contraindications(
            drug_name=drug_name,
            drug_info=drug_info,
            patient_allergies=patient_allergies or [],
            patient_medications=patient_medications or [],
            patient_conditions=patient_conditions or []
        )
        
        return {
            "safe": len(warnings) == 0,
            "warnings": warnings
        }


# Singleton instance
recommendation_engine = RecommendationEngine()
