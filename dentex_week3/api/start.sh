#!/bin/bash
# Start script for dentex_week3 ML API

echo "============================================"
echo "Starting DENTEX Week 3 ML API"
echo "============================================"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Verify model files exist
echo "🔍 Verifying model files..."
MODELS_DIR="../production"
REQUIRED_FILES=(
    "coordinator_best.pt"
    "disease_detector_best.pt"
    "tooth_association_rf_300.joblib"
)

ALL_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$MODELS_DIR/$file" ]; then
        echo "   ❌ Missing: $file"
        ALL_EXIST=false
    else
        SIZE=$(du -h "$MODELS_DIR/$file" | cut -f1)
        echo "   ✅ Found: $file ($SIZE)"
    fi
done

if [ "$ALL_EXIST" = false ]; then
    echo ""
    echo "❌ ERROR: Some model files are missing!"
    echo "Please ensure all model files are in: $MODELS_DIR/"
    exit 1
fi

echo ""
echo "✅ All checks passed!"
echo ""
echo "============================================"
echo "🚀 Starting API server on port 8001..."
echo "============================================"
echo ""
echo "API will be available at:"
echo "  - Local:   http://localhost:8001"
echo "  - Network: http://0.0.0.0:8001"
echo "  - Docs:    http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload
