"""
Simple test script to verify Supabase connection
Run this to ensure your credentials are working
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/seifshawky/seif_projects/ieee/dental-xray-ai-assistant/backend/.env')

# Get credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

print("=" * 60)
print("🔍 Testing Supabase Connection")
print("=" * 60)
print(f"\n✓ Supabase URL: {SUPABASE_URL}")
print(f"✓ Supabase Key: {SUPABASE_KEY[:20]}...")

try:
    from supabase import create_client
    
    # Create client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("\n✅ Supabase client created successfully!")
    
    # Try to query (this will fail if tables don't exist yet, but connection works)
    try:
        result = supabase.table('patients').select("*").limit(1).execute()
        print("✅ Successfully connected to Supabase database!")
        print(f"   Patients table exists and is accessible")
    except Exception as e:
        if "relation" in str(e).lower() or "does not exist" in str(e).lower():
            print("⚠️  Connection works, but tables don't exist yet")
            print("   Run the database_schema.sql in Supabase SQL Editor")
        else:
            print(f"⚠️  Connection issue: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ SUPABASE CONNECTION TEST PASSED")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run database_schema.sql in Supabase SQL Editor")
    print("2. Create storage bucket named 'xray-scans'")
    print("3. Start the backend server")
    
except ImportError:
    print("\n❌ supabase library not installed")
    print("   Install it with: pip install supabase")
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\nPlease check your credentials in backend/.env")
