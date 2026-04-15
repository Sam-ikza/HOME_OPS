# HOMEOPS

HomeOps is organized as a monorepo with separate backend and frontend apps.

## Repository Layout

- apps/api: FastAPI backend, Alembic migrations, database layer, and service modules.
- apps/web: Vite + React frontend.
- docs: Architecture notes and runbooks.
- scripts: Local automation and guardrail scripts.

## Quick Start (Local)

1. Backend setup:

```powershell
cd apps/api
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

2. Frontend setup:

```powershell
cd ../web
npm install
```

3. Start both services from repo root:

```powershell
./scripts/start-local.ps1
```

The script launches:
- API at http://127.0.0.1:8000
- Web app at http://127.0.0.1:5173

## Environment

- API example env file: apps/api/.env.example
- Local API env file: apps/api/.env
- Frontend proxy target: `VITE_BACKEND_TARGET` (fallback: `http://127.0.0.1:8000`)

## Security Guardrail

Before pushing, run:

```powershell
./scripts/prepush-secret-check.ps1
```

This scans staged diffs for obvious secret patterns and blocks push on detection.
