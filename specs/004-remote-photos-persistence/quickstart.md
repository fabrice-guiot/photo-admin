# Quickstart Guide: Photo Admin Web Application

**Feature**: 004-remote-photos-persistence
**Date**: 2025-12-29
**Target**: Developers setting up local development environment

## Overview

This guide walks you through setting up the photo-admin web application for local development, covering:

1. PostgreSQL database setup
2. Python backend environment (FastAPI)
3. Node.js frontend environment (React)
4. Database migrations (Alembic)
5. Running backend and frontend servers
6. Running tests
7. First-time user workflow

**Prerequisites**:
- Python 3.10 or higher
- Node.js 16+ and npm 8+
- PostgreSQL 12+ installed and running
- Git (for version control)
- macOS, Linux, or Windows with WSL2

**Estimated Setup Time**: 20-30 minutes

---

## 1. PostgreSQL Database Setup

### Install PostgreSQL

**macOS (Homebrew)**:
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows**:
Download and install from [postgresql.org](https://www.postgresql.org/download/windows/)

### Create Database and User

```bash
# Connect to PostgreSQL as superuser
psql postgres

# Inside psql shell:
CREATE DATABASE photo_admin;
CREATE USER photo_admin_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE photo_admin TO photo_admin_user;

# Grant schema privileges (PostgreSQL 15+)
\c photo_admin
GRANT ALL ON SCHEMA public TO photo_admin_user;

# Exit psql
\q
```

### Verify Connection

```bash
psql -U photo_admin_user -d photo_admin -h localhost

# Inside psql:
\dt  # Should show "No relations found" (empty database)
\q
```

---

## 2. Python Backend Environment Setup

### Clone Repository

```bash
# Clone repository (if not already cloned)
git clone <repository-url>
cd photo-admin

# Checkout feature branch
git checkout 004-remote-photos-persistence
```

### Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows
```

### Install Dependencies

```bash
# Install backend dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt
```

**Backend Dependencies** (requirements.txt):
```text
# Web framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9

# Remote storage
boto3==1.29.7
google-cloud-storage==2.10.0
smbprotocol==1.12.0

# Security
cryptography==41.0.7

# Utilities
pyyaml==6.0.1
jinja2==3.1.2

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
websockets==12.0
```

### Configure Environment Variables

Create `.env` file in repository root:

```bash
# backend/.env

# Database configuration
PHOTO_ADMIN_DB_URL=postgresql://photo_admin_user:your_secure_password@localhost:5432/photo_admin

# Encryption key for credentials (generate once)
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
PHOTO_ADMIN_ENCRYPTION_KEY=<generated_key_here>

# Optional: Logging level
LOG_LEVEL=INFO
```

**Generate Encryption Key**:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Copy output to PHOTO_ADMIN_ENCRYPTION_KEY in .env
```

**Security Note**: Never commit `.env` file to version control. Add to `.gitignore`:
```bash
echo ".env" >> .gitignore
```

---

## 3. Database Migrations (Alembic)

### Initialize Alembic (First Time Only)

```bash
cd backend

# Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# Review migration file
# Edit: backend/src/db/migrations/versions/<timestamp>_initial_schema.py
```

### Apply Migrations

```bash
# Run migrations
alembic upgrade head

# Verify tables created
psql -U photo_admin_user -d photo_admin -h localhost -c "\dt"

# Expected output:
#              List of relations
#  Schema |      Name         | Type  |     Owner
# --------+-------------------+-------+---------------
#  public | collections       | table | photo_admin_user
#  public | analysis_results  | table | photo_admin_user
#  public | configurations    | table | photo_admin_user
#  public | pipelines         | table | photo_admin_user
#  public | pipeline_history  | table | photo_admin_user
#  public | alembic_version   | table | photo_admin_user
```

### Useful Alembic Commands

```bash
# Check current migration version
alembic current

# View migration history
alembic history

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Upgrade to latest
alembic upgrade head
```

---

## 4. Node.js Frontend Environment Setup

### Install Node.js

**macOS (Homebrew)**:
```bash
brew install node@18
```

**Linux (using nvm)**:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
nvm install 18
nvm use 18
```

**Windows**:
Download installer from [nodejs.org](https://nodejs.org/)

### Install Frontend Dependencies

```bash
cd frontend

# Install dependencies
npm install
```

**Frontend Dependencies** (package.json):
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2",
    "recharts": "^2.10.3",
    "@mui/material": "^5.14.20",
    "@mui/icons-material": "^5.14.19",
    "@emotion/react": "^11.11.1",
    "@emotion/styled": "^11.11.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.4",
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.1.5",
    "vitest": "^1.0.4"
  }
}
```

### Configure Frontend Environment

Create `frontend/.env.local`:

```bash
# frontend/.env.local

VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_BASE_URL=ws://localhost:8000/api
```

---

## 5. Running the Application

### Start Backend Server

```bash
# Terminal 1: Backend
cd backend
source ../venv/bin/activate  # Activate virtual environment

# Start FastAPI server with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process [12345] using StatReload
# INFO:     Started server process [12346]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
```

**Backend Endpoints**:
- API: http://localhost:8000/api
- OpenAPI docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Start Frontend Dev Server

```bash
# Terminal 2: Frontend
cd frontend

# Start Vite dev server
npm run dev

# Expected output:
# VITE v5.0.4  ready in 423 ms
#
# ➜  Local:   http://localhost:5173/
# ➜  Network: use --host to expose
# ➜  press h to show help
```

**Frontend URL**: http://localhost:5173

### Verify Application Running

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8000/api/health
   # Expected: {"status": "healthy"}
   ```

2. **Frontend**: Open http://localhost:5173 in browser
   - Should see photo-admin web interface
   - Check browser console for errors

---

## 6. Running Tests

### Backend Tests (pytest)

```bash
cd backend
source ../venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_models.py -v

# Run integration tests only
pytest tests/integration/ -v

# Run end-to-end tests
pytest tests/e2e/ -v
```

**Expected Output**:
```
========================= test session starts =========================
collected 87 items

tests/unit/test_models.py::test_collection_model PASSED         [  1%]
tests/unit/test_models.py::test_analysis_result_model PASSED    [  2%]
...
tests/integration/test_api.py::test_create_collection PASSED    [ 98%]
tests/e2e/test_workflows.py::test_full_analysis_workflow PASSED [100%]

========================= 87 passed in 12.45s =========================
```

### Frontend Tests (Vitest)

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- CollectionForm.test.jsx

# Run in watch mode (auto-rerun on file changes)
npm test -- --watch
```

---

## 7. First-Time User Workflow

### Step 1: Import Existing YAML Configuration (Optional)

If you have existing `config/config.yaml`:

1. **Via Web UI**:
   - Navigate to http://localhost:5173/config
   - Click "Import YAML Configuration"
   - Upload `config/config.yaml`
   - Resolve any conflicts (side-by-side comparison)
   - Confirm import

2. **Via CLI** (backend script):
   ```bash
   cd backend
   python scripts/import_config.py ../config/config.yaml

   # Expected output:
   # Configuration imported successfully
   # - photo_extensions: ['.dng', '.cr3', '.tiff']
   # - metadata_extensions: ['.xmp']
   # - camera_mappings: 2 cameras
   # - processing_methods: 3 methods
   ```

### Step 2: Create Your First Collection

**Via Web UI**:

1. Navigate to http://localhost:5173/collections
2. Click "Create Collection"
3. Fill in form:
   - **Name**: "My Photos 2024"
   - **Type**: Local
   - **Location**: /Users/yourname/Photos/2024
   - **State**: Live (1-hour cache)
4. Click "Test Accessibility" (verifies path exists)
5. Click "Create"

**Via API (curl)**:
```bash
curl -X POST http://localhost:8000/api/collections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Photos 2024",
    "type": "local",
    "location": "/Users/yourname/Photos/2024",
    "state": "Live"
  }'

# Expected response:
# {
#   "id": 1,
#   "name": "My Photos 2024",
#   "type": "local",
#   "location": "/Users/yourname/Photos/2024",
#   "state": "Live",
#   "is_accessible": true,
#   "created_at": "2025-12-29T10:00:00Z",
#   ...
# }
```

### Step 3: Run PhotoStats Analysis

1. Navigate to http://localhost:5173/tools
2. Select collection: "My Photos 2024"
3. Select tool: "PhotoStats"
4. Click "Run Analysis"
5. Monitor progress in real-time (WebSocket connection)
   - Files scanned: 1500/5000
   - Issues found: 12
   - Stage: "Scanning photos"
   - Progress: 30%
6. When complete, view HTML report

**Via API**:
```bash
# Start analysis
curl -X POST http://localhost:8000/api/tools/photostats \
  -H "Content-Type: application/json" \
  -d '{"collection_id": 1}'

# Response:
# {
#   "message": "Analysis queued",
#   "job_id": "a3f8d5c2-1234-5678-90ab-cdef12345678",
#   "position": 1,
#   "estimated_start_minutes": 0
# }

# Monitor progress (WebSocket)
wscat -c "ws://localhost:8000/api/tools/progress/a3f8d5c2-1234-5678-90ab-cdef12345678"

# Get job status (REST)
curl http://localhost:8000/api/tools/status/a3f8d5c2-1234-5678-90ab-cdef12345678
```

### Step 4: View Results and Trends

1. Navigate to http://localhost:5173/results
2. Filter by collection: "My Photos 2024"
3. View latest PhotoStats result
4. Click "View Report" (pre-generated HTML)
5. Run PhotoStats again (monthly) to see trends:
   - Orphaned files over time
   - Camera usage changes
   - Collection health metrics

---

## 8. Creating a Remote Collection (AWS S3)

### Prerequisites

- AWS account with S3 bucket
- AWS access key and secret key
- S3 bucket with photos (e.g., `s3://my-photo-bucket/collections/2024/`)

### Create S3 Collection

**Via Web UI**:

1. Navigate to http://localhost:5173/collections
2. Click "Create Collection"
3. Fill in form:
   - **Name**: "Cloud Photos 2024"
   - **Type**: S3
   - **Location**: s3://my-photo-bucket/collections/2024/
   - **State**: Closed (24-hour cache)
   - **Credentials**:
     - AWS Access Key ID: `AKIAIOSFODNN7EXAMPLE`
     - AWS Secret Access Key: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
     - Region: us-east-1
4. Click "Test Accessibility" (validates credentials)
5. Click "Create"

**Security**: Credentials are encrypted using Fernet before storing in database.

### Run Analysis on S3 Collection

Same workflow as local collection:
1. Select "Cloud Photos 2024" in Tools page
2. Run PhotoStats/Photo Pairing/Pipeline Validation
3. First run: Fetches file listing from S3 (slow)
4. Subsequent runs: Uses cached file listing (fast, 24-hour TTL)

---

## 9. Configuring a Pipeline

### Create Pipeline via Form Editor

1. Navigate to http://localhost:5173/pipelines
2. Click "Create Pipeline"
3. Fill in:
   - **Name**: "Standard Workflow"
   - **Description**: "RAW → DNG → Edit → Archive"
4. Add nodes:
   - **Capture** (entry point)
   - **File** (extension: .dng)
   - **Process** (method: HDR)
   - **Pairing** (separator: -)
   - **File** (extension: .jpg)
   - **Termination** (type: Archive)
5. Connect nodes with edges
6. Click "Validate" (checks for cycles, orphaned nodes)
7. Fix any validation errors
8. Click "Save"
9. Click "Activate" (sets as default for Pipeline Validation)

### Preview Expected Filenames

1. Open pipeline "Standard Workflow"
2. Click "Preview Filenames"
3. Input:
   - Camera ID: AB3D
   - Start Counter: 1
4. Expected Output:
   ```
   AB3D0001.dng
   AB3D0001-HDR.jpg
   AB3D0001.xmp
   ```

---

## 10. Troubleshooting

### Database Connection Errors

**Error**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution**:
1. Verify PostgreSQL running: `brew services list` (macOS) or `systemctl status postgresql` (Linux)
2. Check connection details in `.env` file
3. Test connection: `psql -U photo_admin_user -d photo_admin -h localhost`

### Migration Errors

**Error**: `alembic.util.exc.CommandError: Can't locate revision identified by`

**Solution**:
```bash
# Reset migrations (CAUTION: drops all data)
alembic downgrade base
alembic upgrade head
```

### Encryption Key Errors

**Error**: `ValueError: PHOTO_ADMIN_ENCRYPTION_KEY environment variable not set`

**Solution**:
1. Generate key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
2. Add to `backend/.env`: `PHOTO_ADMIN_ENCRYPTION_KEY=<key>`
3. Restart backend server

### Frontend CORS Errors

**Error**: `Access to XMLHttpRequest blocked by CORS policy`

**Solution**:
1. Verify backend running on http://localhost:8000
2. Check `VITE_API_BASE_URL` in `frontend/.env.local`
3. Ensure FastAPI CORS middleware configured:
   ```python
   # backend/src/main.py
   from fastapi.middleware.cors import CORSMiddleware

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:5173"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### WebSocket Connection Errors

**Error**: `WebSocket connection failed: Error during WebSocket handshake`

**Solution**:
1. Verify backend WebSocket endpoint: `http://localhost:8000/api/tools/progress/{job_id}`
2. Test with wscat: `wscat -c "ws://localhost:8000/api/tools/progress/<job_id>"`
3. Check browser console for detailed error messages

### Remote Storage Access Errors

**AWS S3 Error**: `botocore.exceptions.NoCredentialsError: Unable to locate credentials`

**Solution**:
1. Verify credentials in collection configuration
2. Test credentials manually:
   ```python
   import boto3
   s3 = boto3.client('s3',
       aws_access_key_id='...',
       aws_secret_access_key='...',
       region_name='us-east-1'
   )
   s3.list_objects_v2(Bucket='my-photo-bucket', Prefix='collections/2024/')
   ```

---

## 11. Development Workflow

### Making Changes

**Backend Changes**:
1. Edit Python files in `backend/src/`
2. Backend auto-reloads (uvicorn `--reload` flag)
3. Run tests: `pytest tests/`
4. Create migration if models changed: `alembic revision --autogenerate -m "Description"`
5. Apply migration: `alembic upgrade head`

**Frontend Changes**:
1. Edit React files in `frontend/src/`
2. Frontend auto-reloads (Vite HMR)
3. Run tests: `npm test`

### Database Schema Changes

```bash
# 1. Edit SQLAlchemy models in backend/src/models/
# 2. Generate migration
alembic revision --autogenerate -m "Add new column to collections"

# 3. Review migration file
cat backend/src/db/migrations/versions/<timestamp>_add_new_column.py

# 4. Apply migration
alembic upgrade head

# 5. Verify change
psql -U photo_admin_user -d photo_admin -h localhost -c "\d collections"
```

### Adding New API Endpoint

```bash
# 1. Add route in backend/src/api/<module>.py
# 2. Add Pydantic schema in backend/src/schemas/<module>.py
# 3. Add service logic in backend/src/services/<module>.py
# 4. Add test in tests/integration/test_api.py
# 5. Run tests: pytest tests/integration/test_api.py::test_new_endpoint -v
# 6. Update OpenAPI docs: http://localhost:8000/docs (auto-generated)
```

---

## 12. Next Steps

**After Setup**:
1. ✅ Database running and migrated
2. ✅ Backend server running (http://localhost:8000)
3. ✅ Frontend dev server running (http://localhost:5173)
4. ✅ First collection created
5. ✅ First analysis executed

**Recommended Next Actions**:
1. Import existing YAML configuration (if migrating from CLI tools)
2. Create collections for all photo storage locations
3. Set up pipelines for workflow validation
4. Run monthly analysis to build trend history
5. Review API documentation (http://localhost:8000/docs)

**Learning Resources**:
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/)
- [React Documentation](https://react.dev/)
- [PostgreSQL JSONB](https://www.postgresql.org/docs/current/datatype-json.html)

**Getting Help**:
- Check logs: Backend console output, frontend browser console
- Review OpenAPI docs: http://localhost:8000/docs
- Run tests with verbose output: `pytest -vv`
- Check database state: `psql -U photo_admin_user -d photo_admin`

---

## Appendix: Quick Reference

### Start/Stop Services

```bash
# Start PostgreSQL
brew services start postgresql@14  # macOS
sudo systemctl start postgresql    # Linux

# Stop PostgreSQL
brew services stop postgresql@14   # macOS
sudo systemctl stop postgresql     # Linux

# Start Backend (from backend/)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Start Frontend (from frontend/)
npm run dev
```

### Database Commands

```bash
# Connect to database
psql -U photo_admin_user -d photo_admin -h localhost

# List tables
\dt

# Describe table
\d collections

# View data
SELECT * FROM collections;

# Reset database (CAUTION: deletes all data)
DROP DATABASE photo_admin;
CREATE DATABASE photo_admin;
GRANT ALL PRIVILEGES ON DATABASE photo_admin TO photo_admin_user;
```

### Useful URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api
- **OpenAPI Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **WebSocket**: ws://localhost:8000/api/tools/progress/{job_id}

### Environment Variables

```bash
# Backend (.env)
PHOTO_ADMIN_DB_URL=postgresql://user:pass@localhost:5432/photo_admin
PHOTO_ADMIN_ENCRYPTION_KEY=<fernet_key>
LOG_LEVEL=INFO

# Frontend (.env.local)
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_BASE_URL=ws://localhost:8000/api
```

---

**Setup Complete!** 🎉

You're now ready to develop the photo-admin web application. Happy coding!
