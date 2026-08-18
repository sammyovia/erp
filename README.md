# Erp Platform - Candidate Compliance Module

## Overview

Erp is a multi-tenant, compliance-native SaaS operating platform for regulated workforce services. This implementation represents a vertical slice of the Candidate Compliance module, demonstrating:

- **Multi-tenant isolation** with defense-in-depth (application middleware + PostgreSQL RLS)
- **Immutable audit logging** with tamper-evident hashing
- **Versioned compliance documents** preserving full history
- **Async document verification** workflow with Celery
- **Governed AI feature** for CV extraction with human confirmation
- **Full-stack implementation** with Django REST API + Next.js frontend

---

## Table of Contents

- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Running the Application](#running-the-application)
- [Key Design Decisions](#key-design-decisions)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Django 6.1 + Django REST Framework 3.14 | API development |
| Database | PostgreSQL 15 with Row-Level Security | Multi-tenant data isolation |
| Authentication | JWT (SimpleJWT) with token blacklisting | Secure authentication |
| Async Tasks | Celery 5.3 + Redis | Document verification |
| AI Integration | OpenAI/Claude with mock fallback | CV data extraction |
| API Docs | drf-yasg (Swagger/ReDoc) | API documentation |
| Deployment | Render (Web Service + PostgreSQL) | Production hosting |

### Frontend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Next.js 14 (App Router) | React framework |
| Language | TypeScript | Type safety |
| Styling | Tailwind CSS | Utility-first styling |
| State Management | TanStack React Query | Data fetching & caching |
| Forms | React Hook Form + Zod | Form validation |
| HTTP Client | Axios | API communication |
| UI Components | Lucide React + Radix UI | Icons and components |
| Toast Notifications | React Hot Toast | User feedback |

---

## Project Structure

```
erp/
├── backend/                      # Django Backend
│   ├── apps/
│   │   ├── tenants/              # Tenant management
│   │   ├── candidates/           # Candidate CRUD
│   │   ├── documents/            # Document management & versioning
│   │   ├── audit/                # Immutable audit logging
│   │   ├── ai/                   # AI CV extraction
│   │   ├── authentication/       # JWT authentication
│   │   └── core/                 # Middleware, permissions, exceptions
│   ├── erp/
│   │   ├── settings.py           # Django settings
│   │   └── urls.py               # Main URL configuration
│   ├── manage.py
│   ├── requirements.txt
│   └── .env                      # Environment variables
│
├── frontend/                      # Next.js Frontend
│   ├── app/
│   │   ├── (auth)/              # Authentication pages (login/register)
│   │   ├── (dashboard)/         # Protected pages
│   │   │   ├── dashboard/       # Dashboard
│   │   │   ├── candidates/      # Candidate management
│   │   │   ├── documents/       # Document management
│   │   │   ├── ai/              # AI CV analysis
│   │   │   └── audit/           # Audit logs viewer
│   │   ├── layout.tsx           # Root layout
│   │   ├── providers.tsx        # React Query provider
│   │   └── globals.css          # Global styles
│   ├── components/
│   │   ├── layout/              # Layout components
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── LayoutWrapper.tsx
│   │   └── ui/                  # Reusable UI components
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       └── Card.tsx
│   ├── lib/
│   │   ├── api.ts               # API client
│   │   ├── auth.ts              # Authentication helpers
│   │   └── utils.ts             # Utility functions
│   ├── types/
│   │   └── index.ts             # TypeScript types
│   ├── hooks/
│   │   └── useAuth.ts           # Authentication hook
│   ├── .env.local               # Frontend environment variables
│   ├── package.json
│   └── tailwind.config.js
│
├── docs/
│   ├── architecture.md           # Architecture decisions
│   └── review.md                 # Code review task
│
├── docker-compose.yml            # Docker setup
├── render.yaml                   # Render deployment config
└── README.md                     # This file
```

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend runtime |
| PostgreSQL | 15+ | Production database |
| Redis | 7+ | Celery broker (optional for local dev) |
| Git | Latest | Version control |

### Optional

- Docker Desktop - For containerized development
- Render Account - For deployment

---

## Backend Setup

### 1. Clone the Repository

```bash
git clone https://github.com/sammyovia/erp.git
cd erp/backend
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Django Settings
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/erp_db

# Or use individual variables:
DB_NAME=erp_db
DB_USER=erp_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis (for Celery)
CELERY_BROKER_URL=redis://localhost:6379/0

# AI Configuration
AI_MODEL=mock  # or 'openai' or 'claude'
AI_API_KEY=your-api-key  # Only if using real LLM

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### 5. Initialize Database

```bash
# Create migrations
python manage.py makemigrations tenants
python manage.py makemigrations candidates
python manage.py makemigrations documents
python manage.py makemigrations audit
python manage.py makemigrations ai

# Apply migrations
python manage.py migrate

# Create superuser (admin)
python manage.py createsuperuser
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

### 7. Run Celery Worker (for Async Tasks)

```bash
# In a separate terminal
celery -A erp worker --loglevel=info
```

---

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd ../frontend
```

### 2. Install Dependencies

```bash
npm install
# or
yarn install
```

### 3. Configure Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 4. Run the Development Server

```bash
npm run dev
# or
yarn dev
```

The frontend will be available at `http://localhost:3000`

---

## Running the Application

### Complete Local Development Setup

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python manage.py runserver

# Terminal 2: Celery Worker (Optional)
cd backend
source venv/bin/activate
celery -A erp worker --loglevel=info

# Terminal 3: Frontend
cd frontend
npm run dev
```

### Using Docker (Recommended for Production-like Environment)

```bash
# From the project root
docker-compose up -d

# Services will be available at:
# Backend API: http://localhost:8000
# Frontend: http://localhost:3000
# PostgreSQL: localhost:5432
# Redis: localhost:6379
```

### First User Registration

1. Open `http://localhost:3000/register`
2. Fill in the registration form:
   - Username: `admin`
   - Email: `admin@example.com`
   - Password: `SecurePassword123!`
   - Organization: `My Agency`
   - Tenant Slug: `my-agency`
3. Click "Create Account"
4. You'll be redirected to the dashboard

### Admin Panel Access

```
http://localhost:8000/admin/
```

Login with the superuser credentials created during `createsuperuser`.

---

## Key Design Decisions

### 1. Multi-Tenant Isolation

**Decision:** Implemented defense-in-depth with three layers:
- Application middleware validates tenant context
- ORM query filtering automatically scopes all queries
- PostgreSQL RLS provides database-level enforcement

**Why:** Financial/compliance systems require absolute tenant isolation. Multiple layers prevent data leaks even if one layer fails. RLS provides a safety net that protects against application bugs.

### 2. Immutable Audit Logging

**Decision:** Append-only audit logs with SHA-256 hashes, enforced at model, application, and database levels.

**Why:** Regulatory compliance requires tamper-evident logs. By making logs immutable and storing hashes, we can detect any unauthorized modifications.

### 3. Versioned Documents

**Decision:** Documents are versioned by creating new records (not updating existing ones).

**Why:** Compliance records must preserve history. When a correction is needed, the old version remains intact and the new version supersedes it with a clear lineage.

### 4. AI Feature with Human Confirmation

**Decision:** AI extracts data but never auto-creates candidates. Human recruiter must confirm or reject.

**Why:** AI errors could have serious consequences. Human oversight ensures quality and prevents automation bias. Also aligns with the requirement "AI must never auto-reject a candidate."

### 5. Async Document Verification

**Decision:** Used Celery for async document verification instead of synchronous API calls.

**Why:** Verification may take seconds or involve external services. Async processing prevents blocking the main API server and improves user experience.

### 6. Mock AI by Default

**Decision:** AI service uses mock implementation with regex extraction by default.

**Why:** Reduces friction during development—no API keys required, works offline, and provides predictable results for testing. Easy to switch to real LLM with environment variable.

### 7. Monorepo Structure

**Decision:** Both backend and frontend in a single repository.

**Why:** Simplifies deployment coordination, ensures version compatibility, easier to manage for a take-home assessment.

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user with tenant |
| POST | `/api/auth/login/` | Login and get JWT tokens |
| POST | `/api/auth/logout/` | Logout (blacklist token) |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| GET | `/api/auth/profile/` | Get user profile |

### Candidates

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/candidates/` | List candidates (paginated) |
| POST | `/api/candidates/` | Create candidate |
| GET | `/api/candidates/{id}/` | Get candidate details |
| PATCH | `/api/candidates/{id}/` | Update candidate |
| DELETE | `/api/candidates/{id}/` | Delete candidate |
| POST | `/api/candidates/{id}/add_document/` | Add document to candidate |
| GET | `/api/candidates/expiring_documents/` | Get expiring documents |

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents/` | List documents |
| POST | `/api/documents/` | Create document |
| GET | `/api/documents/{id}/` | Get document details |
| PATCH | `/api/documents/{id}/` | Update document |
| DELETE | `/api/documents/{id}/` | Delete document |
| GET | `/api/documents/{id}/versions/` | Get document versions |
| GET | `/api/documents/expiring_soon/` | Get expiring documents |

### AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ai/cv-analyze/` | Upload and analyze CV |
| GET | `/api/ai/extractions/` | List AI extractions |
| POST | `/api/ai/extractions/{id}/confirm/` | Confirm or reject extraction |

### Audit

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit/logs/` | List audit logs |
| GET | `/api/audit/stats/` | Get audit statistics |
| GET | `/api/audit/logs/by_record/` | Get logs by record |
| GET | `/api/audit/logs/recent/` | Get recent logs |
| GET | `/api/audit/logs/summary/` | Get audit summary |

### Tenants

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tenants/` | List tenants |
| POST | `/api/tenants/` | Create tenant |
| GET | `/api/tenants/{id}/users/` | Get tenant users |
| POST | `/api/tenants/{id}/add_user/` | Add user to tenant |
| POST | `/api/tenants/switch/` | Switch tenant |

### API Documentation

- Swagger UI: `http://localhost:8000/swagger/`
- ReDoc: `http://localhost:8000/docs/`

---

## Testing

### Backend Tests

```bash
cd backend
python manage.py test apps.candidates.tests
python manage.py test apps.documents.tests
python manage.py test apps.tenants.tests
python manage.py test apps.audit.tests
python manage.py test apps.ai.tests
```

### API Testing with cURL

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"Test123!","tenant_name":"Test","tenant_slug":"test"}'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"Test123!"}'

# Create Candidate (with token and tenant)
curl -X POST http://localhost:8000/api/candidates/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","role_applied_for":"Developer"}'
```

### Frontend Testing

```bash
cd frontend
npm run test  # If tests are configured
npm run lint  # Check for linting issues
```

---

## Deployment

### Deploy to Render

1. **Push to GitHub:**
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

2. **Create PostgreSQL Database on Render:**
   - Render Dashboard → New → PostgreSQL
   - Name: `erp-db`
   - Copy the connection string

3. **Deploy Backend:**
   - Render Dashboard → New → Web Service
   - Connect GitHub repo
   - Name: `erp-backend`
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn erp.wsgi:application`
   - Environment Variables:
     - `DJANGO_SECRET_KEY`
     - `DATABASE_URL` (from PostgreSQL)
     - `DEBUG=False`
     - `ALLOWED_HOSTS=your-backend.onrender.com`
     - `CORS_ALLOWED_ORIGINS=https://your-frontend.onrender.com`

4. **Deploy Frontend:**
   - Render Dashboard → New → Web Service
   - Connect GitHub repo
   - Name: `e3os-frontend`
   - Root Directory: `frontend`
   - Build Command: `npm install && npm run build`
   - Start Command: `npm start`
   - Environment Variables:
     - `NEXT_PUBLIC_API_URL=https://erp-backend.onrender.com/api`

### Deploy with Docker (Alternative)

```bash
# Build and run all services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## Troubleshooting

### Common Issues

**CORS Errors (Backend 500)**

**Problem:** Frontend cannot connect to backend due to CORS
**Solution:** Ensure `CORS_ALLOWED_ORIGINS` in settings includes your frontend URL. Add `x-tenant-id` to `CORS_ALLOW_HEADERS`.

**Audit Log Creation Failing**

**Problem:** Audit logs are immutable and cannot be updated
**Solution:** Make sure you're using `AuditLog.objects.create()` not `.save()`. Check that you're not trying to update existing audit logs.

**Tenant ID Missing**

**Problem:** `X-Tenant-ID` header not being sent
**Solution:** Ensure your API client is sending the header after login. Check frontend axios interceptor.

**Migration Issues**

**Problem:** Database schema mismatch
**Solution:** 
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
```

**PostgreSQL Connection Issues**

**Problem:** Can't connect to PostgreSQL
**Solution:** 
- Check PostgreSQL is running: `sudo service postgresql status`
- Verify connection string in `.env`
- Ensure database exists: `createdb erp_db`

**Frontend Build Fails**

**Problem:** Next.js build errors
**Solution:**
```bash
rm -rf .next
rm -rf node_modules
npm install
npm run build
```

### Debug Mode

**Enable detailed logging:**

```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

---

## Contributing

### Branch Strategy

- `main` - Production-ready code
- `develop` - Development branch
- `feature/*` - Feature branches

### Commit Messages

```
feat: Add candidate document versioning
fix: Resolve CORS tenant header issue
docs: Update API documentation
test: Add audit log tests
refactor: Simplify tenant middleware
```

### Code Style

- **Backend:** Follow PEP 8
- **Frontend:** Follow ESLint configuration

---

## License

@MIT. All rights reserved.

---

## Contact

For questions about this implementation:
- Email: [sammyigbinovia@gmail.com]
- GitHub: [sammyovia]

---

## Acknowledgments

- Built with Django, Django REST Framework, and Next.js
- AI assistance provided by DeepSeek and Google Gemini

---

**Architecture & Implementation by Samuel E. Igbinovia**
**Date: August 2026**
