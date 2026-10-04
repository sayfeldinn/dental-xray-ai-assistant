#!/usr/bin/env python3
"""
Verification script for dentex_week3 model setup.
Run this to check if all models load correctly.

Usage:
    cd dentex_week3
    python3 verify_setup.py
"""
import os
import sys
import json
from pathlib import Path

def check_directory_structure():
    """Verify directory structure is correct."""
    print("=" * 60)
    print("STEP 1: Directory Structure Check")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    required_dirs = {
        "api": base_dir / "api",
        "production": base_dir / "production",
        "feedback": base_dir / "feedback",
    }
    
    all_ok = True
    for name, path in required_dirs.items():
        if path.exists():
            print(f"✅ {name}/ directory exists")
        else:
            print(f"❌ {name}/ directory NOT FOUND")
            all_ok = False
    
    print()
    return all_ok


def check_model_files():
    """Check if all required model files exist."""
    print("=" * 60)
    print("STEP 2: Model Files Check")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    production_dir = base_dir / "production"
    
    required_files = {
        "Coordinator Model": "coordinator_best.pt",
        "Disease Detector": "disease_detector_best.pt",
        "Tooth Association RF": "tooth_association_rf_300.joblib",
        "Pipeline Config": "pipeline_config.json",
        "Evaluation Results": "final_evaluation.json",
    }
    
    all_ok = True
    for name, filename in required_files.items():
        filepath = production_dir / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"✅ {name}: {filename} ({size_mb:.2f} MB)")
        else:
            print(f"❌ {name}: {filename} NOT FOUND")
            all_ok = False
    
    print()
    return all_ok


def check_pipeline_config():
    """Verify pipeline configuration is correct."""
    print("=" * 60)
    print("STEP 3: Pipeline Configuration Check")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    config_path = base_dir / "production" / "pipeline_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("✅ Config file loaded successfully")
        
        # Check model paths
        coordinator = config.get("coordinator_model", "")
        disease = config.get("disease_model", "")
        
        # Check if paths are relative (not absolute Windows/Unix paths)
        if coordinator.startswith(("D:", "C:", "/")) or "\\" in coordinator:
            print(f"⚠️  Coordinator path appears to be absolute: {coordinator}")
            print(f"   💡 Should be: coordinator_best.pt")
        else:
            print(f"✅ Coordinator path is relative: {coordinator}")
        
        if disease.startswith(("D:", "C:", "/")) or "\\" in disease:
            print(f"⚠️  Disease path appears to be absolute: {disease}")
            print(f"   💡 Should be: disease_detector_best.pt")
        else:
            print(f"✅ Disease path is relative: {disease}")
        
        # Check metrics
        tooth_acc = config.get("final_tooth_accuracy", 0)
        disease_acc = config.get("final_disease_accuracy", 0)
        full_acc = config.get("final_full_accuracy", 0)
        
        print(f"\n📊 Model Performance Metrics:")
        print(f"   - Tooth Accuracy: {tooth_acc * 100:.2f}%")
        print(f"   - Disease Accuracy: {disease_acc * 100:.2f}%")
        print(f"   - Full Match Accuracy: {full_acc * 100:.2f}%")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        print()
        return False


def check_python_dependencies():
    """Check if required Python packages are installed."""
    print("=" * 60)
    print("STEP 4: Python Dependencies Check")
    print("=" * 60)
    
    required_packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "ultralytics": "Ultralytics YOLO",
        "PIL": "Pillow (PIL)",
        "numpy": "NumPy",
        "pandas": "Pandas",
        "joblib": "Joblib",
    }
    
    all_ok = True
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {name} is installed")
        except ImportError:
            print(f"❌ {name} is NOT installed")
            all_ok = False
    
    if not all_ok:
        print("\n💡 Install missing packages:")
        print("   cd dentex_week3/api")
        print("   pip install -r requirements.txt")
    
    print()
    return all_ok


def test_model_loading():
    """Try to load the models."""
    print("=" * 60)
    print("STEP 5: Model Loading Test")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    production_dir = base_dir / "production"
    
    # Add production dir to Python path
    sys.path.insert(0, str(production_dir))
    
    try:
        print("Attempting to import inference pipeline...")
        from inference_pipeline import (
            COORDINATOR_MODEL,
            DISEASE_MODEL,
            TOOTH_RF,
            CONFIG
        )
        print("✅ Inference pipeline imported successfully")
        print(f"✅ Coordinator model loaded")
        print(f"✅ Disease model loaded")
        print(f"✅ Tooth RF classifier loaded")
        
        # Check disease map
        disease_map = CONFIG.get("disease_map", {})
        print(f"\n📋 Supported Diseases: {len(disease_map)}")
        for did, dname in disease_map.items():
            print(f"   {did}: {dname}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Failed to load models: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check that model files exist in production/")
        print("   2. Verify pipeline_config.json has correct paths")
        print("   3. Install dependencies: pip install ultralytics joblib")
        print()
        return False


def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("DENTEX Week 3 Model Setup Verification")
    print("=" * 60 + "\n")
    
    results = {
        "Directory Structure": check_directory_structure(),
        "Model Files": check_model_files(),
        "Pipeline Config": check_pipeline_config(),
        "Python Dependencies": check_python_dependencies(),
        "Model Loading": test_model_loading(),
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
        print("🎉 All checks passed! Your setup is ready.")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start the API:")
        print("   cd api")
        print("   ./start.sh")
        print("   (or: uvicorn app:app --port 8001 --reload)")
        print("\n2. Test the API:")
        print("   curl http://localhost:8001/")
        print("\n3. Update backend/.env:")
        print("   ML_API_URL=http://localhost:8001")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("=" * 60)
        print("\nQuick fixes:")
        print("1. Ensure you're in the dentex_week3 directory")
        print("2. Verify model files exist in production/")
        print("3. Install dependencies: cd api && pip install -r requirements.txt")
        print("4. Check docs/ML_MODEL_SWITCH_GUIDE.md for details")
    
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
