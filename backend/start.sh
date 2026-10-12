#!/bin/bash
# ==============================================================================
# DentalAI Backend - Development Server Startup Script
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "==============================================="
echo "DentalAI Backend - Starting Development Server"
echo "==============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if [ ! -f "venv/bin/uvicorn" ]; then
    echo -e "${YELLOW}Dependencies not installed. Installing...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}Dependencies installed.${NC}"
fi

# Check if .env exists in parent directory
if [ ! -f "../.env" ]; then
    echo -e "${RED}ERROR: .env file not found in project root!${NC}"
    echo "Please create .env file with Supabase credentials."
    exit 1
fi

# Check if ML service is running
echo "Checking ML service availability..."
if curl -s http://localhost:8001/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ ML service (dentex_week3) is running on port 8001${NC}"
else
    echo -e "${YELLOW}⚠ ML service not detected. Start it with:${NC}"
    echo "  cd ../dentex_week3/api && ./start.sh"
fi

echo ""
echo "Starting FastAPI backend on port 8000..."
echo "API Docs will be available at: http://localhost:8000/docs"
echo ""

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
