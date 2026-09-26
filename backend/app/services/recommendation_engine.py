"""
Recommendation engine for treatment suggestions based on detected findings.
This is Week 1 skeleton - will be populated with validated finding-to-treatment table.
"""
from typing import List, Dict, Optional
from app.schemas.scan import Finding, FindingTypeEnum, FindingSeverityEnum
from app.schemas.treatment import TreatmentCreate, PrescriptionCreate


class RecommendationEngine:
    """
    Core recommendation engine that maps findings to treatment recommendations.
    
    Week 1: Skeleton implementation with placeholder data.
    Week 2+: Populated with validated dentist-approved finding-to-treatment mappings.
    """
    
    # Placeholder finding-to-treatment mapping (to be validated by dentist)
    FINDING_TO_TREATMENT_MAP: Dict[FindingTypeEnum, Dict] = {
        FindingTypeEnum.CAVITY: {
            "low": {
                "treatment": "Dental Filling",
                "description": "Small cavity requiring composite or amalgam filling",
                "estimated_cost": 500.0,
                "drugs": []
            },
            "medium": {
                "treatment": "Dental Filling with Possible Root Canal Evaluation",
                "description": "Moderate cavity, may need deeper evaluation",
                "estimated_cost": 800.0,
                "drugs": []
            },
            "high": {
                "treatment": "Root Canal Treatment",
                "description": "Deep cavity affecting pulp, root canal required",
                "estimated_cost": 2000.0,
                "drugs": ["Amoxicillin", "Ibuprofen"]
            }
        },
        FindingTypeEnum.ROOT_CANAL: {
            "medium": {
                "treatment": "Root Canal Treatment",
                "description": "Root canal therapy with crown",
                "estimated_cost": 2500.0,
                "drugs": ["Amoxicillin", "Ibuprofen"]
            },
            "high": {
                "treatment": "Root Canal Treatment or Extraction",
                "description": "Severe infection, may require extraction",
                "estimated_cost": 3000.0,
                "drugs": ["Amoxicillin", "Metronidazole", "Ibuprofen"]
            }
        },
        FindingTypeEnum.EXTRACTION: {
            "medium": {
                "treatment": "Tooth Extraction",
                "description": "Simple extraction",
                "estimated_cost": 1000.0,
                "drugs": ["Amoxicillin", "Ibuprofen"]
            },
            "high": {
                "treatment": "Surgical Extraction",
                "description": "Complex surgical extraction",
                "estimated_cost": 2000.0,
                "drugs": ["Amoxicillin", "Ibuprofen", "Codeine"]
            }
        }
    }
    
    # Drugs in scope (to be validated by dentist)
    DRUGS_DATABASE: Dict[str, Dict] = {
        "Amoxicillin": {
            "category": "antibiotic",
            "default_dosage": "500mg",
            "default_frequency": "3 times daily",
            "default_duration": "7 days",
            "contraindications": ["penicillin_allergy"],
            "interactions": []
        },
        "Metronidazole": {
            "category": "antibiotic",
            "default_dosage": "400mg",
            "default_frequency": "3 times daily",
            "default_duration": "5 days",
            "contraindications": ["alcohol_use", "pregnancy_first_trimester"],
            "interactions": ["warfarin"]
        },
        "Ibuprofen": {
            "category": "nsaid",
            "default_dosage": "400mg",
            "default_frequency": "every 6-8 hours as needed",
            "default_duration": "5 days",
            "contraindications": ["nsaid_allergy", "active_ulcer", "severe_kidney_disease"],
            "interactions": ["aspirin", "warfarin"]
        },
        "Paracetamol": {
            "category": "analgesic",
            "default_dosage": "500mg",
            "default_frequency": "every 4-6 hours as needed",
            "default_duration": "5 days",
            "contraindications": ["severe_liver_disease"],
            "interactions": ["warfarin"]
        },
        "Codeine": {
            "category": "opioid",
            "default_dosage": "30mg",
            "default_frequency": "every 4-6 hours as needed",
            "default_duration": "3 days",
            "contraindications": ["respiratory_depression", "acute_asthma", "pregnancy"],
            "interactions": ["alcohol", "benzodiazepines"]
        }
    }
    
    def recommend_treatment(
        self, 
        finding: Finding,
        patient_allergies: Optional[List[str]] = None,
        patient_medications: Optional[List[str]] = None,
        patient_conditions: Optional[List[str]] = None
    ) -> Optional[TreatmentCreate]:
        """
        Generate treatment recommendation based on finding and patient context.
        
        Args:
            finding: Detected finding from X-ray analysis
            patient_allergies: List of patient allergies
            patient_medications: List of current patient medications
            patient_conditions: List of patient medical conditions
            
        Returns:
            TreatmentCreate schema with recommendation or None
        """
        # Get treatment mapping for this finding type
        treatment_map = self.FINDING_TO_TREATMENT_MAP.get(finding.type)
        if not treatment_map:
            return None
        
        # Get severity-specific treatment
        severity_key = finding.severity.value
        treatment_info = treatment_map.get(severity_key)
        if not treatment_info:
            # Fallback to medium severity if exact match not found
            treatment_info = treatment_map.get("medium")
            if not treatment_info:
                return None
        
        # Build prescription recommendations
        prescriptions = []
        for drug_name in treatment_info.get("drugs", []):
            drug_info = self.DRUGS_DATABASE.get(drug_name)
            if drug_info:
                # Check contraindications
                warnings = self._check_contraindications(
                    drug_name=drug_name,
                    drug_info=drug_info,
                    patient_allergies=patient_allergies or [],
                    patient_medications=patient_medications or [],
                    patient_conditions=patient_conditions or []
                )
                
                # Still create prescription but with warnings
                prescription = PrescriptionCreate(
                    drug_name=drug_name,
                    dosage=drug_info["default_dosage"],
                    frequency=drug_info["default_frequency"],
                    duration=drug_info["default_duration"],
                    instructions=f"Warnings: {', '.join(warnings)}" if warnings else None
                )
                prescriptions.append(prescription)
        
        # Create treatment recommendation
        treatment = TreatmentCreate(
            patient_id="",  # Will be filled by caller
            treatment_type=treatment_info["treatment"],
            description=treatment_info["description"],
            estimated_cost=treatment_info["estimated_cost"],
            prescriptions=prescriptions,
            notes=f"AI-recommended based on {finding.type.value} with {finding.severity.value} severity"
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
        """
        Check for contraindications and drug interactions.
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check contraindications
        for contraindication in drug_info.get("contraindications", []):
            # Check against conditions
            if contraindication in patient_conditions:
                warnings.append(f"Contraindicated: {contraindication.replace('_', ' ')}")
            
            # Check against allergies
            if "allergy" in contraindication and any(
                allergy.lower() in contraindication.lower() 
                for allergy in patient_allergies
            ):
                warnings.append(f"Allergy alert: {drug_name} may cause allergic reaction")
        
        # Check drug interactions
        for interaction in drug_info.get("interactions", []):
            if any(
                interaction.lower() in med.lower() 
                for med in patient_medications
            ):
                warnings.append(f"Drug interaction: {drug_name} with {interaction}")
        
        return warnings
    
    def check_prescription_safety(
        self,
        drug_name: str,
        patient_allergies: Optional[List[str]] = None,
        patient_medications: Optional[List[str]] = None,
        patient_conditions: Optional[List[str]] = None
    ) -> Dict:
        """
        Standalone contraindication check for a specific drug.
        
        Returns:
            Dictionary with 'safe' boolean and 'warnings' list
        """
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
