#!/usr/bin/env python3
"""
Verification script to check Supabase storage configuration.
Run this to diagnose upload issues.

Usage:
    cd backend
    python3 verify_storage_config.py
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.supabase import SupabaseClient
import requests


def check_environment():
    """Check if all required environment variables are set."""
    print("=" * 60)
    print("STEP 1: Environment Variables Check")
    print("=" * 60)
    
    checks = {
        "SUPABASE_URL": settings.SUPABASE_URL,
        "SUPABASE_KEY (anon)": settings.SUPABASE_KEY,
        "SUPABASE_SERVICE_KEY": settings.SUPABASE_SERVICE_KEY,
    }
    
    all_ok = True
    for name, value in checks.items():
        if value and value != "":
            # Mask the keys for security
            masked = value[:20] + "..." if len(value) > 20 else value
            print(f"✅ {name}: {masked}")
        else:
            print(f"❌ {name}: NOT SET")
            all_ok = False
    
    print()
    return all_ok


def check_supabase_connection():
    """Test connection to Supabase."""
    print("=" * 60)
    print("STEP 2: Supabase Connection Test")
    print("=" * 60)
    
    try:
        # Test anon client
        anon_client = SupabaseClient.get_client()
        print("✅ Anon client initialized")
        
        # Test service client
        service_client = SupabaseClient.get_service_client()
        print("✅ Service client initialized")
        
        print()
        return True
    except Exception as e:
        print(f"❌ Failed to initialize clients: {e}")
        print()
        return False


def check_storage_bucket():
    """Check if xray-scans bucket exists and is accessible."""
    print("=" * 60)
    print("STEP 3: Storage Bucket Check")
    print("=" * 60)
    
    try:
        service_client = SupabaseClient.get_service_client()
        
        # Try to list buckets
        try:
            buckets_response = service_client.storage.list_buckets()
            print(f"✅ Connected to storage API")
            
            # Check if xray-scans bucket exists
            bucket_names = [b.name for b in buckets_response]
            if "xray-scans" in bucket_names:
                print(f"✅ 'xray-scans' bucket exists")
                
                # Get bucket details
                for bucket in buckets_response:
                    if bucket.name == "xray-scans":
                        print(f"   - Public: {bucket.public}")
                        print(f"   - Created: {bucket.created_at}")
                        if not bucket.public:
                            print(f"   ⚠️  WARNING: Bucket is PRIVATE. Images may not be viewable via public URLs.")
                            print(f"   💡 FIX: Set bucket to public in Supabase Dashboard")
            else:
                print(f"❌ 'xray-scans' bucket NOT FOUND")
                print(f"   Available buckets: {', '.join(bucket_names) if bucket_names else 'None'}")
                print(f"   💡 FIX: Create 'xray-scans' bucket in Supabase Dashboard")
                return False
                
        except Exception as e:
            print(f"❌ Failed to list buckets: {e}")
            print(f"   💡 FIX: Check SUPABASE_SERVICE_KEY is correct")
            return False
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Storage check failed: {e}")
        print()
        return False


def test_storage_upload():
    """Test uploading a small file to storage."""
    print("=" * 60)
    print("STEP 4: Storage Upload Test")
    print("=" * 60)
    
    try:
        service_client = SupabaseClient.get_service_client()
        
        # Create a small test file
        test_content = b"Test upload from verification script"
        test_filename = "test_verification_upload.txt"
        test_path = f"scans/{test_filename}"
        
        print(f"Attempting to upload test file: {test_path}")
        
        try:
            # Try to upload
            response = service_client.storage.from_("xray-scans").upload(
                test_path,
                test_content,
                {"content-type": "text/plain", "upsert": "true"}
            )
            print(f"✅ Upload successful!")
            
            # Try to get public URL
            public_url = service_client.storage.from_("xray-scans").get_public_url(test_path)
            print(f"✅ Public URL generated: {public_url[:60]}...")
            
            # Clean up - delete the test file
            try:
                service_client.storage.from_("xray-scans").remove([test_path])
                print(f"✅ Test file cleaned up")
            except:
                print(f"⚠️  Could not delete test file (not a problem)")
            
            print()
            return True
            
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            print(f"   💡 This is the same error your scan upload is experiencing")
            print(f"   💡 FIX: Check storage RLS policies and bucket permissions")
            print()
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print()
        return False


def check_database_policies():
    """Check if database RLS policies are configured."""
    print("=" * 60)
    print("STEP 5: Database RLS Policies Check")
    print("=" * 60)
    
    try:
        service_client = SupabaseClient.get_service_client()
        
        # Try to query scans table
        try:
            result = service_client.table("scans").select("id", count="exact").limit(0).execute()
            print(f"✅ Can query 'scans' table (found {result.count} rows)")
        except Exception as e:
            print(f"❌ Cannot query 'scans' table: {e}")
            return False
        
        # Try to query patients table
        try:
            result = service_client.table("patients").select("id", count="exact").limit(0).execute()
            print(f"✅ Can query 'patients' table (found {result.count} rows)")
        except Exception as e:
            print(f"❌ Cannot query 'patients' table: {e}")
            return False
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        print()
        return False


def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("Supabase Storage Configuration Verification")
    print("=" * 60 + "\n")
    
    results = {
        "Environment": check_environment(),
        "Connection": check_supabase_connection(),
        "Storage Bucket": check_storage_bucket(),
        "Upload Test": test_storage_upload(),
        "Database Policies": check_database_policies(),
    }
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All checks passed! Your storage configuration is correct.")
        print("=" * 60)
        print("\nIf uploads still fail, check:")
        print("1. Frontend is using the correct backend URL")
        print("2. JWT token is valid and not expired")
        print("3. Patient ID exists and belongs to the authenticated user")
        print("4. File size is within limits (50MB default)")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("=" * 60)
        print("\nQuick fixes:")
        print("1. Add SUPABASE_SERVICE_KEY to backend/.env")
        print("2. Create 'xray-scans' bucket in Supabase Dashboard")
        print("3. Set bucket to PUBLIC in bucket settings")
        print("4. Restart the backend after changing .env")
        print("\nFor detailed instructions, see:")
        print("  docs/QUICK_FIX_STORAGE.md")
    
    print()
    return 0 if all_passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
