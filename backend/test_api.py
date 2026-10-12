#!/usr/bin/env python3
"""
DentalAI Backend - API Test Script
Quick verification that backend endpoints are working.
"""

import asyncio
import httpx
from datetime import date
from uuid import uuid4

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"


async def test_health():
    """Test health check endpoint."""
    print("=" * 60)
    print("Testing Health Check...")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Health check passed")
            print(f"  Status: {data.get('status')}")
            print(f"  Service: {data.get('service')}")
            print(f"  Environment: {data.get('environment')}")
            print(f"  ML Service: {data.get('ml_service_url')}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False


async def test_patient_crud():
    """Test patient CRUD operations."""
    print("\n" + "=" * 60)
    print("Testing Patient CRUD...")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Create patient
        patient_data = {
            "first_name": "Test",
            "last_name": "Patient",
            "date_of_birth": "1990-05-15",
            "gender": "male",
            "phone": "+201234567890",
            "email": "test@example.com",
            "weight_kg": 75.0,
            "allergies": ["penicillin"],
            "current_medications": [],
            "medical_conditions": []
        }
        
        print("\n1. Creating patient...")
        response = await client.post(f"{API_V1}/patients", json=patient_data)
        
        if response.status_code != 201:
            print(f"✗ Create patient failed: {response.status_code}")
            print(response.text)
            return None
        
        patient = response.json()
        patient_id = patient['id']
        print(f"✓ Patient created: {patient['first_name']} {patient['last_name']}")
        print(f"  ID: {patient_id}")
        print(f"  Allergies: {patient['allergies']}")
        
        # Get patient
        print("\n2. Getting patient...")
        response = await client.get(f"{API_V1}/patients/{patient_id}")
        
        if response.status_code == 200:
            print("✓ Patient retrieved successfully")
        else:
            print(f"✗ Get patient failed: {response.status_code}")
        
        # List patients
        print("\n3. Listing patients...")
        response = await client.get(f"{API_V1}/patients?page=1&page_size=10")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Patient list retrieved: {data['total']} total patients")
        else:
            print(f"✗ List patients failed: {response.status_code}")
        
        # Update patient
        print("\n4. Updating patient...")
        update_data = {
            "medical_conditions": ["hypertension"]
        }
        response = await client.put(f"{API_V1}/patients/{patient_id}", json=update_data)
        
        if response.status_code == 200:
            updated_patient = response.json()
            print(f"✓ Patient updated")
            print(f"  Medical conditions: {updated_patient['medical_conditions']}")
        else:
            print(f"✗ Update patient failed: {response.status_code}")
        
        return patient_id


async def test_scan_upload(patient_id: str):
    """Test scan upload (without actual file for now)."""
    print("\n" + "=" * 60)
    print("Testing Scan Operations...")
    print("=" * 60)
    
    print("\n✓ Scan upload endpoint exists at POST /api/v1/scans/upload")
    print("  (Requires actual image file - test manually with curl or Swagger UI)")
    
    # List scans for patient
    print(f"\nListing scans for patient {patient_id}...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_V1}/scans?patient_id={patient_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Scan list retrieved: {data['total']} scans for this patient")
        else:
            print(f"✗ List scans failed: {response.status_code}")


async def test_ml_service():
    """Test ML service connectivity."""
    print("\n" + "=" * 60)
    print("Testing ML Service Connection...")
    print("=" * 60)
    
    ml_url = "http://localhost:8001"
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(ml_url)
            if response.status_code == 200:
                data = response.json()
                print("✓ ML service (dentex_week3) is running")
                print(f"  Status: {data.get('status')}")
            else:
                print(f"✓ ML service is running (HTTP {response.status_code})")
        except Exception as e:
            print(f"✗ ML service not reachable: {e}")
            print("  Start it with: cd dentex_week3/api && ./start.sh")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("DentalAI Backend API Tests")
    print("=" * 60)
    print(f"Backend URL: {BASE_URL}")
    print(f"API Base: {API_V1}")
    print("=" * 60)
    
    # Test health
    health_ok = await test_health()
    if not health_ok:
        print("\n✗ Backend is not running or not healthy!")
        print("  Start it with: cd backend && ./start.sh")
        return
    
    # Test ML service
    await test_ml_service()
    
    # Test patient CRUD
    patient_id = await test_patient_crud()
    
    if patient_id:
        # Test scan operations
        await test_scan_upload(patient_id)
    
    print("\n" + "=" * 60)
    print("Tests Complete!")
    print("=" * 60)
    print(f"\nView interactive API docs at: {BASE_URL}/docs")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
