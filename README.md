# Multi-Agent Debate System

Production-ready full-stack app with:
- Backend: FastAPI + OpenAI API + async debate orchestration
- Frontend: Next.js + Tailwind CSS + Framer Motion
- Deployment targets: Railway (backend) and Vercel (frontend)

## Project Structure

- `backend/`
  - `main.py`
  - `debate_engine.py`
  - `agents/`
  - `memory/`
  - `models/`
  - `services/`
- `frontend/`
  - `components/`
  - `pages/`

## Backend Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
export OPENAI_API_KEY="your_key"
# optional
export OPENAI_MODEL="gpt-4.1-mini"
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API:
- `POST /start-debate`
  - Body:
  ```json
  {
    "prompt": "Should governments subsidize AI compute infrastructure?",
    "confidence_target": 80
  }
  ```
  - Response: Server-Sent Events stream with `started`, `round`, `final` (or `error`) events.

## Frontend Setup

```bash
cd frontend
npm install
export NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
npm run dev
```

## Railway Deployment (Backend)

1. Create Railway project from repo.
2. Set root to repository root.
3. Set service start command to use `Procfile` (already included under `backend/Procfile`).
4. Add env vars:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL` (optional)
5. Ensure service exposes HTTP port.

## Vercel Deployment (Frontend)

1. Import repo in Vercel.
2. Set framework to Next.js and Root Directory to `frontend`.
3. Set env var:
   - `NEXT_PUBLIC_API_BASE_URL` = Railway backend URL
4. Deploy.

## Notes

- `InMemoryDebateStore` is used for MVP memory; switch to Redis for multi-instance persistence.
- If `OPENAI_API_KEY` is missing, backend returns deterministic fallback content for local smoke testing.
