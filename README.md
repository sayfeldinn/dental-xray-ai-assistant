# DentalAI - IEEE FCTAI Competition Project

AI-Assisted Diagnostic & Patient History System for Dental Clinics

## 🏗️ Project Structure

```
dental-xray-ai-assistant/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Config, security, dependencies
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API client
│   │   ├── hooks/         # Custom hooks
│   │   └── utils/         # Utilities
│   ├── public/
│   └── package.json
├── docs/                  # Documentation
└── .gitignore
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Supabase account (free tier)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from `.env.example` and fill in your Supabase credentials

5. Run the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000
API documentation: http://localhost:8000/docs

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env.local` file from `.env.example` and fill in your Supabase credentials

4. Run the development server:
```bash
npm run dev
```

Frontend will be available at: http://localhost:5173

## 📝 Week 1 Features

### Backend
- ✅ Patient record management (CRUD)
- ✅ X-ray upload and storage
- ✅ Recommendation engine skeleton
- ✅ Contraindication checking logic
- ✅ Supabase integration

### Frontend
- ✅ Authentication (login/signup)
- ✅ X-ray review screen
- ✅ Treatment confirmation screen
- ✅ Patient history viewer

## 🔐 Environment Variables

### Backend (.env)
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
```

### Frontend (.env.local)
```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_URL=http://localhost:8000
```

## 📚 Documentation

See the `/docs` folder for detailed project documentation:
- `Project_Context.md` - Full project context and scope
- `Week1_Execution_Plan.md` - Week 1 detailed execution plan

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🤝 Team Roles

- ML Engineer - Dataset preparation & model training
- Backend Engineer - API & business logic
- Frontend Engineer - UI/UX implementation
- Integration/QA Engineer - Testing & synthetic data
- Team Lead - Coordination & clinical liaison

## 📄 License

IEEE FCTAI Competition Project
