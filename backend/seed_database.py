#!/usr/bin/env python3
"""
DentalAI Backend - Database Seeding Script
Populates database with realistic test data for development and testing.
"""

import asyncio
import httpx
from datetime import date, datetime, timedelta
from uuid import uuid4
import random

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"


# Test patient profiles based on competition branches
TEST_PATIENTS = [
    {
        "first_name": "Ahmed",
        "last_name": "Hassan",
        "date_of_birth": "1985-03-15",
        "gender": "male",
        "phone": "+201012345678",
        "email": "ahmed.hassan@example.com",
        "weight_kg": 75.0,
        "allergies": [],
        "current_medications": [],
        "medical_conditions": [],
        "notes": "Clean active infection case - first-line Amoxicillin candidate"
    },
    {
        "first_name": "Mona",
        "last_name": "El-Sayed",
        "date_of_birth": "1992-07-22",
        "gender": "female",
        "phone": "+201123456789",
        "email": "mona.elsayed@example.com",
        "weight_kg": 62.0,
        "allergies": ["penicillin", "amoxicillin"],
        "current_medications": [],
        "medical_conditions": [],
        "notes": "Penicillin allergy - should trigger Clindamycin alternative"
    },
    {
        "first_name": "Tarek",
        "last_name": "Mahmoud",
        "date_of_birth": "1978-11-05",
        "gender": "male",
        "phone": "+201234567890",
        "email": "tarek.mahmoud@example.com",
        "weight_kg": 88.0,
        "allergies": [],
        "current_medications": ["warfarin"],
        "medical_conditions": ["cardiac_endocarditis_risk"],
        "notes": "Cardiac risk patient - AHA pre-procedure prophylaxis required"
    },
    {
        "first_name": "Nour",
        "last_name": "Ibrahim",
        "date_of_birth": "2005-01-18",
        "gender": "female",
        "phone": "+201345678901",
        "email": "nour.ibrahim@example.com",
        "weight_kg": 52.0,
        "allergies": [],
        "current_medications": [],
        "medical_conditions": [],
        "notes": "Superficial caries - restorative only, no antibiotics"
    },
    {
        "first_name": "Omar",
        "last_name": "Farouk",
        "date_of_birth": "1988-09-30",
        "gender": "male",
        "phone": "+201456789012",
        "email": "omar.farouk@example.com",
        "weight_kg": 82.0,
        "allergies": ["nsaid", "ibuprofen"],
        "current_medications": [],
        "medical_conditions": ["gi_ulcer"],
        "notes": "NSAID contraindication - should use Paracetamol for pain"
    },
    {
        "first_name": "Layla",
        "last_name": "Mansour",
        "date_of_birth": "1995-04-12",
        "gender": "female",
        "phone": "+201567890123",
        "email": "layla.mansour@example.com",
        "weight_kg": 58.0,
        "allergies": [],
        "current_medications": ["alcohol_chronic"],
        "medical_conditions": ["hepatic_impairment"],
        "notes": "Hepatic impairment - requires dosage adjustment"
    },
    {
        "first_name": "Youssef",
        "last_name": "Abdel-Rahman",
        "date_of_birth": "2010-08-25",
        "gender": "male",
        "phone": "+201678901234",
        "email": "youssef.ar@example.com",
        "weight_kg": 35.0,
        "allergies": [],
        "current_medications": [],
        "medical_conditions": [],
        "notes": "Pediatric patient - weight-based dosing (50 mg/kg)"
    },
    {
        "first_name": "Salma",
        "last_name": "Kamal",
        "date_of_birth": "1982-12-08",
        "gender": "female",
        "phone": "+201789012345",
        "email": "salma.kamal@example.com",
        "weight_kg": 68.0,
        "allergies": ["aspirin"],
        "current_medications": ["warfarin"],
        "medical_conditions": ["asthma"],
        "notes": "Multiple contraindications - aspirin-sensitive asthma + anticoagulant"
    },
    {
        "first_name": "Khaled",
        "last_name": "Naguib",
        "date_of_birth": "1990-06-17",
        "gender": "male",
        "phone": "+201890123456",
        "email": "khaled.naguib@example.com",
        "weight_kg": 95.0,
        "allergies": [],
        "current_medications": [],
        "medical_conditions": ["renal_impairment"],
        "notes": "Renal impairment - NSAID contraindicated"
    },
    {
        "first_name": "Yasmine",
        "last_name": "Fouad",
        "date_of_birth": "1998-02-14",
        "gender": "female",
        "phone": "+201901234567",
        "email": "yasmine.fouad@example.com",
        "weight_kg": 55.0,
        "allergies": [],
        "current_medications": [],
        "medical_conditions": [],
        "notes": "Healthy patient - standard treatment protocol"
    }
]


async def create_patients():
    """Create all test patients."""
    print("\n" + "=" * 70)
    print("Creating Test Patients")
    print("=" * 70)
    
    created_patients = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, patient_data in enumerate(TEST_PATIENTS, 1):
            print(f"\n{i}. Creating patient: {patient_data['first_name']} {patient_data['last_name']}")
            
            try:
                response = await client.post(f"{API_V1}/patients", json=patient_data)
                
                if response.status_code == 201:
                    patient = response.json()
                    created_patients.append(patient)
                    print(f"   ✓ Created: ID {patient['id']}")
                    print(f"   - Age: {calculate_age(patient['date_of_birth'])} years")
                    print(f"   - Allergies: {patient['allergies'] or 'None'}")
                    print(f"   - Conditions: {patient['medical_conditions'] or 'None'}")
                else:
                    print(f"   ✗ Failed: HTTP {response.status_code}")
                    print(f"   Error: {response.text}")
            
            except Exception as e:
                print(f"   ✗ Exception: {e}")
    
    print(f"\n{'=' * 70}")
    print(f"Created {len(created_patients)} of {len(TEST_PATIENTS)} patients")
    print("=" * 70)
    
    return created_patients


def calculate_age(date_of_birth: str) -> int:
    """Calculate age from date of birth string."""
    dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age


async def check_backend_health():
    """Check if backend is running and healthy."""
    print("\n" + "=" * 70)
    print("Checking Backend Status")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Backend is healthy")
                print(f"  Service: {data.get('service')}")
                print(f"  Environment: {data.get('environment')}")
                print(f"  Supabase: {'✓' if data.get('supabase_configured') else '✗'}")
                print(f"  ML Service: {data.get('ml_service_url')}")
                return True
            else:
                print(f"✗ Backend unhealthy: HTTP {response.status_code}")
                return False
        
        except Exception as e:
            print(f"✗ Cannot connect to backend: {e}")
            print(f"  Make sure backend is running: cd backend && ./start.sh")
            return False


async def check_ml_service():
    """Check if ML service is running."""
    print("\n" + "=" * 70)
    print("Checking ML Service Status")
    print("=" * 70)
    
    ml_url = "http://localhost:8001"
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(ml_url)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ ML service (dentex_week3) is running")
                print(f"  Status: {data.get('status')}")
                return True
            else:
                print(f"✓ ML service is reachable (HTTP {response.status_code})")
                return True
        except Exception as e:
            print(f"✗ ML service not reachable: {e}")
            print(f"  Start it with: cd dentex_week3/api && ./start.sh")
            return False


async def list_all_patients():
    """List all patients in database."""
    print("\n" + "=" * 70)
    print("Current Patients in Database")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{API_V1}/patients?page=1&page_size=100")
            
            if response.status_code == 200:
                data = response.json()
                patients = data.get('patients', [])
                total = data.get('total', 0)
                
                print(f"\nTotal patients: {total}\n")
                
                for i, patient in enumerate(patients, 1):
                    print(f"{i}. {patient['first_name']} {patient['last_name']}")
                    print(f"   ID: {patient['id']}")
                    print(f"   DOB: {patient['date_of_birth']} ({calculate_age(patient['date_of_birth'])} years)")
                    print(f"   Gender: {patient['gender'].title()}")
                    print(f"   Weight: {patient.get('weight_kg', 'N/A')} kg")
                    
                    if patient.get('allergies'):
                        print(f"   ⚠ Allergies: {', '.join(patient['allergies'])}")
                    
                    if patient.get('medical_conditions'):
                        print(f"   ⚠ Conditions: {', '.join(patient['medical_conditions'])}")
                    
                    if patient.get('current_medications'):
                        print(f"   💊 Medications: {', '.join(patient['current_medications'])}")
                    
                    print()
                
                return patients
            else:
                print(f"✗ Failed to list patients: HTTP {response.status_code}")
                return []
        
        except Exception as e:
            print(f"✗ Exception: {e}")
            return []


async def show_statistics():
    """Show database statistics."""
    print("\n" + "=" * 70)
    print("Database Statistics")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Count patients
        try:
            response = await client.get(f"{API_V1}/patients?page=1&page_size=1")
            if response.status_code == 200:
                patient_count = response.json().get('total', 0)
                print(f"  Patients: {patient_count}")
        except:
            print(f"  Patients: Unable to retrieve")
        
        # Count scans
        try:
            response = await client.get(f"{API_V1}/scans?page=1&page_size=1")
            if response.status_code == 200:
                scan_count = response.json().get('total', 0)
                print(f"  Scans: {scan_count}")
        except:
            print(f"  Scans: Unable to retrieve")
    
    print("=" * 70)


async def main():
    """Main seeding workflow."""
    print("\n" + "=" * 70)
    print("DentalAI Database Seeding Script")
    print("=" * 70)
    print(f"Backend URL: {BASE_URL}")
    print(f"API Base: {API_V1}")
    print("=" * 70)
    
    # Check backend
    backend_ok = await check_backend_health()
    if not backend_ok:
        print("\n❌ Backend is not running. Exiting.")
        return
    
    # Check ML service (optional but recommended)
    await check_ml_service()
    
    # Show existing data
    print("\n" + "=" * 70)
    print("Checking Existing Data")
    print("=" * 70)
    existing_patients = await list_all_patients()
    
    if existing_patients:
        print(f"\n⚠ Found {len(existing_patients)} existing patients.")
        print("Do you want to add more test patients? (y/n): ", end="")
        
        # For automation, default to yes
        response = input().lower()
        if response != 'y':
            print("Exiting without adding new patients.")
            await show_statistics()
            return
    
    # Create test patients
    created = await create_patients()
    
    # Show final statistics
    await show_statistics()
    
    print("\n" + "=" * 70)
    print("✅ Database Seeding Complete!")
    print("=" * 70)
    print(f"\nCreated {len(created)} new patients.")
    print(f"View all patients at: {BASE_URL}/docs")
    print("\nNext steps:")
    print("  1. Upload X-ray scans via API or Swagger UI")
    print("  2. Review AI-generated findings")
    print("  3. Test recommendation engine (Phase 3)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
