#!/usr/bin/env python3
"""
Verification script for the ML model setup.
Run this to check if all models load correctly.

Usage:
    cd ml
    python3 verify_setup.py
"""

import json
import sys
from pathlib import Path


def check_directory_structure():
    """Verify directory structure is correct."""
    print("=" * 60)
    print("STEP 1: Directory Structure Check")
    print("=" * 60)

    base_dir = Path(__file__).parent.parent
    required_dirs = {
        "pipeline": base_dir / "pipeline",
        "service": base_dir / "service",
        "weights": base_dir / "weights",
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

    base_dir = Path(__file__).parent.parent
    weights_dir = base_dir / "weights"
    pipeline_dir = base_dir / "pipeline"

    required_files = {
        "Tooth Detector": weights_dir / "tooth_best.pt",
        "Disease Detector": weights_dir / "disease_best.pt",
        "Pipeline Config": pipeline_dir / "pipeline_config.json",
    }

    all_ok = True
    for name, filepath in required_files.items():
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"✅ {name}: {filepath.name} ({size_mb:.2f} MB)")
        else:
            print(f"❌ {name}: {filepath.name} NOT FOUND")
            all_ok = False

    print()
    return all_ok


def check_pipeline_config():
    """Verify pipeline configuration is correct."""
    print("=" * 60)
    print("STEP 3: Pipeline Configuration Check")
    print("=" * 60)

    base_dir = Path(__file__).parent.parent
    config_path = base_dir / "pipeline" / "pipeline_config.json"

    try:
        with open(config_path) as f:
            config = json.load(f)

        print("✅ Config file loaded successfully")

        # Check model paths are relative (not absolute Windows/Unix paths)
        for key in ("tooth_model", "disease_model"):
            value = config.get(key, "")
            if not value:
                print(f"❌ Missing {key} in config")
                return False
            if value.startswith(("D:", "C:", "/")) or "\\" in value:
                print(f"⚠️  {key} path appears to be absolute: {value}")
            else:
                print(f"✅ {key} is relative: {value}")

        print(f"\n📊 Architecture: {config.get('architecture', 'unknown')}")
        print(f"   Association: {config.get('association', 'unknown')}")

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
        print("   cd ml/service")
        print("   pip install -r requirements.txt")

    print()
    return all_ok


def test_model_loading():
    """Try to load the models."""
    print("=" * 60)
    print("STEP 5: Model Loading Test")
    print("=" * 60)

    base_dir = Path(__file__).parent.parent
    pipeline_dir = base_dir / "pipeline"

    # Make the pipeline package importable
    sys.path.insert(0, str(pipeline_dir))

    try:
        print("Attempting to import inference pipeline...")
        from inference import CONFIG, _model

        print("✅ Inference pipeline imported successfully")

        # Models load lazily, so touch both to prove the weights are readable.
        _model("tooth")
        print(f"✅ Tooth detector loaded ({CONFIG['tooth_model']})")
        _model("disease")
        print(f"✅ Disease detector loaded ({CONFIG['disease_model']})")

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
        print("   1. Check that weights exist in ml/weights/")
        print("   2. Verify pipeline_config.json has correct paths")
        print("   3. Install dependencies: pip install -r service/requirements.txt")
        print()
        return False


def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("DENTEX v3 setup verification")
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
        print("1. Run this from the ml/ directory")
        print("2. Verify weights exist in ml/weights/")
        print("3. Install dependencies: cd service && pip install -r requirements.txt")
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
