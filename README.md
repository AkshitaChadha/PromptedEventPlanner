# CelebrAI

CelebrAI is an AI-powered celebration and event planning assistant for birthdays, weddings, anniversaries, and community events. This project targets the **Celebration & Event Planner** GenAI challenge vertical.

## Project status

This repository currently contains the initial application skeleton. Event planning features are not implemented yet.

## Planned approach

The application will collect event details and constraints, then use deterministic Python business logic for validation, budget arithmetic, and timeline dates. An optional backend-only language model integration will produce personalized ideas in validated structured output. A clearly labelled mock mode will support local use without an API key. Suggestions and estimates will be distinguished from verified facts.

## Planned architecture

- `backend/`: Flask REST API and Python business logic
- `frontend/`: React and Vite client
- SQLite for initial local persistence (to be added with the persistence feature)

## Local setup

Requirements: Python 3.10+ and Node.js 20+.

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example .env
python backend\run.py
```

The API health endpoint is available at `http://127.0.0.1:5000/api/health`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Configuration and security

Copy `.env.example` to `.env` for local configuration. `.env` is ignored by Git. Provider credentials must only be used by the backend and must never be added to frontend code or committed.

## Development status and assumptions

The initial vertical is event planning for celebrations. INR is the planned default currency. No vendor search, booking, payments, or real AI-generated planning is available in this skeleton. The API currently exposes only a health check.

## License

No license has been selected yet.
