# Unified Tribal Scholarship Platform

A runnable full-stack prototype based on the consolidated PRD:
- Student, Nodal Officer, Admin and Bank/DBT portals
- Combined Login/Register experience
- Scholarship discovery and application journey
- Document Wallet
- Common Verification Layer (CVL) with exception/manual-review workflow
- Event-driven notification center
- DBT/payment simulation
- Jago scholarship assistant
- Duplicate/integrity flags
- PostgreSQL-ready backend, with SQLite default for easy local demo

## Run

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

The frontend expects the API at http://localhost:8000.

This prototype uses local/demo adapters. Live DigiLocker/API Setu/NPCI/DBT access requires authorized production onboarding and credentials.
