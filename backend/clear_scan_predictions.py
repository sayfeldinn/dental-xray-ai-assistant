"""
Utility script to clear all predictions for a specific scan.
This helps test that new inference results properly replace old ones.

Usage:
    python clear_scan_predictions.py <scan_id>
"""
import sys
import os
from supabase import create_client

# Add the app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings

def clear_predictions(scan_id: str):
    """Clear all predictions for a given scan_id."""
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    try:
        # Delete from predictions table
        result = supabase.table("predictions").delete().eq("scan_id", scan_id).execute()
        print(f"✓ Deleted {len(result.data if result.data else [])} predictions from table")
        
        # Clear the findings array in the scan record
        supabase.table("scans").update({"findings": []}).eq("id", scan_id).execute()
        print(f"✓ Cleared findings array in scan record")
        
        print(f"\n✓ Successfully cleared all predictions for scan {scan_id}")
        print("Now re-run inference on this scan through the frontend.")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python clear_scan_predictions.py <scan_id>")
        print("\nExample: python clear_scan_predictions.py c2140756-feca-4ea2-aad1-bd3c47d1ea61")
        sys.exit(1)
    
    scan_id = sys.argv[1]
    clear_predictions(scan_id)
