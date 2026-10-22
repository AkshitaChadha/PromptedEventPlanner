# CelebrAI

CelebrAI is an AI-powered celebration and event planning assistant for birthdays, weddings, anniversaries, and community events. This project targets the **Celebration & Event Planner** GenAI challenge vertical.

## Project status

The starter application, event validation, priority-aware budget allocation, dynamic timelines, and SQLite persistence for events and tasks are in place. AI planning, expense tracking, and vendor planning are not implemented yet.

## Planned approach

The application will collect event details and constraints, then use deterministic Python business logic for validation, budget arithmetic, and timeline dates. An optional backend-only language model integration will produce personalized ideas in validated structured output. A clearly labelled mock mode will support local use without an API key. Suggestions and estimates will be distinguished from verified facts.

## Planned architecture

- `backend/`: Flask REST API and Python business logic
- `frontend/`: React and Vite client
- SQLite and SQLAlchemy for local event and task persistence

## Local setup

Requirements: Python 3.10+ and Node.js 20+.

### Backend

```powershell
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
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

The API provides `POST /api/events`, `GET /api/events`, `GET /api/events/{id}`, and `PATCH /api/events/{id}/tasks/{task_id}` to create and retrieve saved events and complete or reopen their generated tasks. Event creation validates the request and persists its initial timeline in SQLite. The local database file is ignored by Git. No vendor search, booking, payments, or real AI-generated planning is available yet.

The budget engine uses decimal arithmetic, reduces lower-priority estimates first, preserves configured category minimums, and reports infeasible minimums as overspend instead of claiming the budget fits. The timeline engine creates planning deadlines relative to the event date, marks past deadlines overdue for upcoming events, skips new preparation tasks for past events, and preserves completed, user-edited, and custom tasks when rescheduling. Backend logic is covered with Python's built-in `unittest` runner:

```powershell
$env:PYTHONPATH = "backend"
..\.venv\Scripts\python.exe -m unittest discover -s backend\tests -v
```

## License

No license has been selected yet.
