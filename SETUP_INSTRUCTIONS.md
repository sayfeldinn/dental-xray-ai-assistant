# ⚠️ Important Setup Note - Python Version

## Issue: Python 3.14 Compatibility

Your system is using Python 3.14, which is very new and has compatibility issues with some dependencies (specifically pydantic-core).

## Solution: Use Python 3.11 or 3.12

You need to install Python 3.11 or 3.12. Here's how:

### Option 1: Install Python 3.11 or 3.12 via Homebrew
```bash
# Install Python 3.12
brew install python@3.12

# Recreate virtual environment with Python 3.12
cd backend
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Option 2: Use pyenv
```bash
# Install pyenv if you don't have it
brew install pyenv

# Install Python 3.12
pyenv install 3.12

# Set it as local version for this project
cd /Users/seifshawky/seif_projects/ieee/dental-xray-ai-assistant
pyenv local 3.12

# Recreate virtual environment
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Quick Workaround (If You Can't Install Another Python Version)

I've created a simplified setup that uses pre-built wheels. Try this:

```bash
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn supabase-py python-dotenv python-jose[cryptography] passlib[bcrypt] python-multipart email-validator pydantic-settings
```

Then try starting the server:
```bash
uvicorn app.main:app --reload
```

## After Fixing Python Version

Once you have the right Python version:

1. **Backend**:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

2. **Frontend** (in a new terminal):
```bash
cd frontend
npm run dev
```

3. **Test** it by visiting:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000/docs

## Environment Files Already Configured

✅ Your `.env` files are already set up with your Supabase credentials:
- `backend/.env` - Backend configuration
- `frontend/.env.local` - Frontend configuration

You just need to fix the Python version issue and you're ready to go!

## Next Step

**Run the database setup SQL** in your Supabase dashboard:
1. Go to https://dnsitfbvxubrjqcjkqot.supabase.co
2. Click "SQL Editor"
3. Copy the content from `backend/database_schema.sql`
4. Paste and run it

Then you'll be fully set up! 🚀
