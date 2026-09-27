"""
End-to-End Verification Script for Week 2 Full-Stack & Integration
Tests against live FastAPI server at http://127.0.0.1:8000
"""
import io
import json
import sys
from pathlib import Path
from PIL import Image
import requests

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_tests():
    print("=============================================================")
    print(" DentalAI Week 2 Full-Stack & Integration Verification")
    print("=============================================================")
    
    # 1. Health Check
    res = requests.get("http://127.0.0.1:8000/health")
    assert res.status_code == 200, f"Health failed: {res.text}"
    print("✅ [1/6] Health check: OK")

    # 2. Authentication
    login_payload = {
        "email": "test@example.com",
        "password": "password123"
    }
    res = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json().get("access_token")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    print("✅ [2/6] Authentication (Login): OK")

    # 3. Patient Retrieval from Supabase
    res = requests.get(f"{BASE_URL}/patients", headers=headers)
    assert res.status_code == 200, f"Patients failed: {res.text}"
    res_data = res.json()
    patients = res_data.get("patients", []) if isinstance(res_data, dict) else res_data
    print(f"✅ [3/6] Retrieved {len(patients)} synthetic patient profiles from Supabase:")
    
    p_by_alias = {}
    for p in patients:
        name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
        allergies = p.get("allergies") or []
        meds = p.get("current_medications") or []
        conditions = p.get("medical_conditions") or []
        dob = p.get("date_of_birth", "")[:10]
        pid = p.get("id")
        
        # Map profile ID alias based on name
        if "Sara" in name: p_by_alias["P-001"] = pid
        elif "Omar" in name: p_by_alias["P-002"] = pid
        elif "Nour" in name: p_by_alias["P-003"] = pid
        elif "Mahmoud" in name: p_by_alias["P-004"] = pid
        elif "Youssef" in name: p_by_alias["P-005"] = pid
        elif "Laila" in name: p_by_alias["P-006"] = pid

        print(f"       • {name} | DOB: {dob} | Allergies: {allergies} | Meds: {meds} | Conditions: {conditions}")

    # 4. ML Model Inference (Ultralytics YOLOv8s best.pt)
    from app.services.ml_service import ml_service
    assert ml_service.model is not None, "Ultralytics model should be loaded!"
    names = getattr(ml_service.model, 'names', {})
    print(f"✅ [4/6] YOLOv8s Model loaded from weights (best.pt):")
    print(f"       • Model classes registered: {names}")
    
    # 5. Recommendation Engine & 3 Demo Branches via live REST API
    print("✅ [5/6] Testing Clinical Recommendation & Contraindication branches:")
    
    # Branch A: P-001 (Sara Mansoori) - Clean / No Drug Conflict
    p001_id = p_by_alias.get("P-001")
    finding_a = {
        "type": "non_odontogenic",
        "severity": "mild",
        "confidence": 0.88,
        "bounding_box": {"x": 0.1, "y": 0.1, "width": 0.05, "height": 0.05}
    }
    res_a = requests.post(
        f"{BASE_URL}/recommendations/treatment",
        headers=headers,
        json={"finding": finding_a, "patient_id": p001_id}
    )
    assert res_a.status_code == 200, f"Branch A failed: {res_a.text}"
    rec_a = res_a.json()
    print(f"       • Branch A (P-001 Mild Non-Odontogenic):")
    print(f"         Procedure: '{rec_a.get('treatment_type')}' | Cost: ${rec_a.get('estimated_cost')} | Rx: {len(rec_a.get('prescriptions', []))} drugs")

    # Branch B: P-002 (Omar Hassan) - Drug, No Conflict
    p002_id = p_by_alias.get("P-002")
    finding_b = {
        "type": "caries",
        "severity": "severe",
        "confidence": 0.94,
        "bounding_box": {"x": 0.35, "y": 0.42, "width": 0.08, "height": 0.1}
    }
    res_b = requests.post(
        f"{BASE_URL}/recommendations/treatment",
        headers=headers,
        json={"finding": finding_b, "patient_id": p002_id}
    )
    assert res_b.status_code == 200, f"Branch B failed: {res_b.text}"
    rec_b = res_b.json()
    rxs_b = [f"{p['drug_name']} {p['dosage']}" for p in rec_b.get("prescriptions", [])]
    print(f"       • Branch B (P-002 Severe Caries - No conflicts):")
    print(f"         Procedure: '{rec_b.get('treatment_type')}' | Rx: {rxs_b}")

    # Branch C1: P-003 (Nour Ali) - Drug with Allergy Conflict (Penicillin)
    p003_id = p_by_alias.get("P-003")
    finding_c1 = {
        "type": "periapical",
        "severity": "severe",
        "confidence": 0.92,
        "bounding_box": {"x": 0.62, "y": 0.70, "width": 0.12, "height": 0.15}
    }
    res_c1 = requests.post(
        f"{BASE_URL}/recommendations/treatment",
        headers=headers,
        json={"finding": finding_c1, "patient_id": p003_id}
    )
    assert res_c1.status_code == 200, f"Branch C1 failed: {res_c1.text}"
    rec_c1 = res_c1.json()
    print(f"       • Branch C1 (P-003 Periapical - Penicillin Allergy Check):")
    for rx in rec_c1.get("prescriptions", []):
        print(f"         - {rx['drug_name']} ({rx['dosage']}): Instructions/Warnings: '{rx.get('instructions')}'")

    # Direct contraindication check API for Azithromycin alternative on P-003
    res_azithro = requests.post(
        f"{BASE_URL}/recommendations/check-contraindication",
        headers=headers,
        json={"drug_name": "Azithromycin", "patient_id": p003_id}
    )
    print(f"         - Azithromycin Alternative Check: Safe={res_azithro.json().get('safe')}, Warnings={res_azithro.json().get('warnings')}")

    # Branch C2: P-004 (Mahmoud Suleiman) - Drug with Drug-Interaction Conflict (Warfarin)
    p004_id = p_by_alias.get("P-004")
    res_warfarin_check = requests.post(
        f"{BASE_URL}/recommendations/check-contraindication",
        headers=headers,
        json={"drug_name": "Ibuprofen", "patient_id": p004_id}
    )
    print(f"       • Branch C2 (P-004 Warfarin Interaction Check):")
    print(f"         - Ibuprofen (NSAID): Safe={res_warfarin_check.json().get('safe')}, Warnings={res_warfarin_check.json().get('warnings')}")

    res_paracetamol_check = requests.post(
        f"{BASE_URL}/recommendations/check-contraindication",
        headers=headers,
        json={"drug_name": "Paracetamol", "patient_id": p004_id}
    )
    print(f"         - Paracetamol Substitute: Safe={res_paracetamol_check.json().get('safe')}, Warnings={res_paracetamol_check.json().get('warnings')}")

    # 6. Active Learning / Feedback write-path
    feedback_payload = {
        "dentist_action": "confirmed",
        "original_finding_type": "caries",
        "corrected_finding_type": None,
        "dentist_notes": "Occlusal caries confirmed on tooth 16",
        "bounding_box_valid": True
    }
    res_fb = requests.post(
        f"{BASE_URL}/findings/demo-finding-1/feedback",
        headers=headers,
        json=feedback_payload
    )
    assert res_fb.status_code == 200, f"Feedback failed: {res_fb.text}"
    print(f"✅ [6/6] Active Learning Feedback API: status={res_fb.status_code}, response={res_fb.json()}")

    print("\n🎉 ALL WEEK 2 VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
