# DentalAI System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
│                      (React + Vite + Axios)                     │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  Login   │  │Dashboard │  │ Patients │  │  Scans   │      │
│  │  SignUp  │  │   Page   │  │   Page   │  │   Page   │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐      │
│  │           Auth Context (Supabase Auth)               │      │
│  └─────────────────────────────────────────────────────┘      │
│                          ↓  ↑                                   │
│  ┌─────────────────────────────────────────────────────┐      │
│  │          API Client (Axios + Interceptors)           │      │
│  └─────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              ↓  ↑
                         HTTP/REST API
                         JWT Tokens
                              ↓  ↑
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND LAYER                           │
│                    (FastAPI + Python 3.9+)                      │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │   Auth   │  │ Patients │  │  Scans   │  │Recommend │      │
│  │   API    │  │   API    │  │   API    │  │   API    │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                              ↓  ↑                               │
│  ┌─────────────────────────────────────────────────────┐      │
│  │           Business Logic Layer (Services)            │      │
│  │  • PatientService                                    │      │
│  │  • RecommendationEngine                              │      │
│  │  • ContraindicationChecker                           │      │
│  └─────────────────────────────────────────────────────┘      │
│                              ↓  ↑                               │
│  ┌─────────────────────────────────────────────────────┐      │
│  │         Data Access Layer (Supabase Client)          │      │
│  └─────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              ↓  ↑
                         Supabase API
                         PostgreSQL Protocol
                              ↓  ↑
┌─────────────────────────────────────────────────────────────────┐
│                       SUPABASE LAYER                            │
│                  (Managed Backend-as-a-Service)                 │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │  Authentication │  │    PostgreSQL   │  │   Storage    │  │
│  │   (JWT Auth)    │  │    Database     │  │  (X-rays)    │  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
│                                                                 │
│  Tables:                                                        │
│  • patients (with medical history)                             │
│  • scans (with findings JSON)                                  │
│  • treatments                                                   │
│  • prescriptions                                                │
│  • feedback (for active learning)                              │
│                                                                 │
│  Row-Level Security (RLS):                                     │
│  • Dentists see only their own data                            │
│  • Automatic user_id filtering                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Diagrams

### 1. User Authentication Flow

```
User Action (Login)
        ↓
Frontend (Login Page)
        ↓
AuthContext.signIn()
        ↓
Supabase.auth.signInWithPassword()
        ↓
Supabase Auth Service
        ↓
JWT Token Generated
        ↓
Token Stored in Context
        ↓
Redirect to Dashboard
        ↓
All subsequent API calls include JWT in header
```

### 2. Patient Creation Flow

```
User Action (Create Patient)
        ↓
Frontend Form Submit
        ↓
patientAPI.create(data)
        ↓
Axios Request with JWT
        ↓
Backend: POST /api/v1/patients
        ↓
Auth Middleware (verify JWT)
        ↓
PatientService.create_patient()
        ↓
Supabase.table('patients').insert()
        ↓
Row-Level Security Check
        ↓
Database Insert
        ↓
Response with Patient Object
        ↓
Frontend Updates UI
```

### 3. X-Ray Upload & Analysis Flow (Week 2+)

```
User Uploads X-Ray Image
        ↓
Frontend: scanAPI.upload(file)
        ↓
Backend: POST /api/v1/scans/upload
        ↓
Upload to Supabase Storage
        ↓
Create Scan Record in DB
        ↓
[Week 2] Trigger ML Analysis
        ↓
[Week 2] YOLO Model Inference
        ↓
[Week 2] Extract Findings
        ↓
Update Scan with Findings
        ↓
RecommendationEngine.recommend_treatment()
        ↓
Return to Frontend for Review
```

### 4. Treatment Recommendation Flow

```
AI Detects Finding
        ↓
Frontend: recommendationAPI.getTreatment()
        ↓
Backend: POST /api/v1/recommendations/treatment
        ↓
Get Patient Medical History
        ↓
RecommendationEngine.recommend_treatment()
        ↓
Lookup Finding Type in Mapping Table
        ↓
Generate Treatment Plan
        ↓
For Each Drug:
  ├─ Check Allergies
  ├─ Check Drug Interactions
  ├─ Check Medical Conditions
  └─ Generate Warnings
        ↓
Return Treatment with Prescriptions
        ↓
Display in Confirmation Screen
```

## 🗂️ Database Schema

### Core Tables

```sql
┌─────────────┐
│  patients   │
├─────────────┤
│ id          │ UUID (PK)
│ dentist_id  │ UUID (FK → auth.users)
│ first_name  │ VARCHAR
│ last_name   │ VARCHAR
│ dob         │ TIMESTAMP
│ allergies   │ JSONB[]
│ medications │ JSONB[]
│ conditions  │ JSONB[]
└─────────────┘
        ↓ 1:N
┌─────────────┐
│    scans    │
├─────────────┤
│ id          │ UUID (PK)
│ patient_id  │ UUID (FK)
│ dentist_id  │ UUID (FK)
│ image_url   │ TEXT
│ status      │ ENUM
│ findings    │ JSONB[]
└─────────────┘
        ↓ 1:N
┌─────────────┐
│ treatments  │
├─────────────┤
│ id          │ UUID (PK)
│ patient_id  │ UUID (FK)
│ scan_id     │ UUID (FK)
│ type        │ VARCHAR
│ status      │ ENUM
└─────────────┘
        ↓ 1:N
┌─────────────┐
│prescriptions│
├─────────────┤
│ id          │ UUID (PK)
│ treatment_id│ UUID (FK)
│ drug_name   │ VARCHAR
│ dosage      │ VARCHAR
│ warnings    │ JSONB[]
└─────────────┘
```

## 🔐 Security Architecture

### Authentication Flow

```
1. User Registration
   ├─ Email + Password → Supabase Auth
   ├─ User created in auth.users table
   └─ JWT token issued

2. All API Requests
   ├─ Frontend includes JWT in Authorization header
   ├─ Backend validates JWT with Supabase
   ├─ Extract user_id from token
   └─ Use for Row-Level Security

3. Row-Level Security
   ├─ Database policies enforce access control
   ├─ WHERE dentist_id = auth.uid()
   └─ Automatic on all queries
```

### Data Protection Layers

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│  • Input validation (Pydantic)          │
│  • CORS configuration                   │
│  • Request rate limiting (future)       │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│        Authentication Layer             │
│  • JWT token validation                 │
│  • User session management              │
│  • Password hashing (bcrypt)            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Database Layer                  │
│  • Row-Level Security (RLS)             │
│  • SQL injection prevention             │
│  • Encrypted connections                │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Infrastructure Layer            │
│  • Environment variables                │
│  • Secrets management                   │
│  • HTTPS enforcement (production)       │
└─────────────────────────────────────────┘
```

## 📦 Component Architecture

### Frontend Component Hierarchy

```
App
├── AuthProvider (Context)
│   └── Protected Route Wrapper
│       ├── Dashboard
│       │   └── Navigation Cards
│       ├── Patients Page
│       │   ├── Patient List
│       │   ├── Patient Form
│       │   └── Patient Detail
│       ├── Scans Page
│       │   ├── Upload Form
│       │   ├── Scan List
│       │   └── Scan Review
│       │       └── Bounding Box Overlay (Week 2)
│       └── Treatments Page
│           ├── Treatment List
│           └── Confirmation Screen
│               ├── Recommended Treatment
│               ├── Prescription Details
│               └── Warning Alerts
└── Public Routes
    ├── Login
    └── SignUp
```

### Backend Service Architecture

```
API Layer (FastAPI Routes)
    ↓
Service Layer (Business Logic)
    ├── PatientService
    │   ├── CRUD operations
    │   └── Data validation
    ├── ScanService (Week 2)
    │   ├── Image processing
    │   └── ML model integration
    └── RecommendationEngine
        ├── Finding-to-treatment mapping
        ├── Drug database lookup
        └── Contraindication checking
    ↓
Data Access Layer (Supabase Client)
    ├── Database operations
    └── Storage operations
```

## 🔌 API Design

### RESTful Endpoint Structure

```
/api/v1/
    ├── /auth
    │   ├── POST /signup
    │   ├── POST /signin
    │   ├── POST /signout
    │   └── GET /me
    ├── /patients
    │   ├── GET /            (list with pagination)
    │   ├── POST /           (create)
    │   ├── GET /{id}        (detail)
    │   ├── PUT /{id}        (update)
    │   └── DELETE /{id}     (delete)
    ├── /scans
    │   ├── GET /            (list with filters)
    │   ├── POST /upload     (upload image)
    │   ├── GET /{id}        (detail)
    │   ├── PUT /{id}        (update findings)
    │   └── DELETE /{id}     (delete)
    └── /recommendations
        ├── POST /treatment  (get recommendation)
        ├── POST /check-contraindication
        ├── GET /drugs       (list database)
        └── GET /finding-mappings
```

### Request/Response Patterns

**Standard Success Response:**
```json
{
  "data": { /* resource object */ },
  "status": "success"
}
```

**Paginated List Response:**
```json
{
  "items": [ /* array of resources */ ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

**Error Response:**
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## 🚀 Deployment Architecture (Future)

```
                    ┌─────────────┐
                    │   Users     │
                    └─────────────┘
                          ↓
                    ┌─────────────┐
                    │    CDN      │ (Cloudflare/Vercel)
                    └─────────────┘
                          ↓
        ┌─────────────────┴─────────────────┐
        ↓                                    ↓
┌─────────────────┐              ┌─────────────────┐
│ Frontend (React)│              │ Backend (API)    │
│   Vercel/       │              │   Railway/       │
│   Netlify       │              │   Render         │
└─────────────────┘              └─────────────────┘
                                         ↓
                              ┌─────────────────┐
                              │    Supabase     │
                              │  • Database     │
                              │  • Auth         │
                              │  • Storage      │
                              └─────────────────┘
```

## 📊 Performance Considerations

### Database Optimization
- Indexes on frequently queried columns
- JSONB indexes for findings/allergies
- Pagination for large lists
- Connection pooling via Supabase

### API Optimization
- Async/await for non-blocking I/O
- Response compression
- Query result caching (future)
- CDN for static assets

### Frontend Optimization
- Code splitting
- Lazy loading components
- Image optimization
- Bundle size monitoring

## 🔄 Scalability Path

### Current (Week 1)
- Single FastAPI instance
- Supabase free tier
- Development environment

### Phase 2 (Competition)
- Multiple API instances
- Supabase Pro tier
- Load balancer
- Redis cache

### Phase 3 (Production)
- Microservices architecture
- Dedicated ML inference service
- Message queue (RabbitMQ/Redis)
- Monitoring & logging (Sentry)

---

**Architecture designed for:**
- ✅ Clean separation of concerns
- ✅ Easy testing and maintenance
- ✅ Horizontal scalability
- ✅ Security by default
- ✅ Rapid feature development
