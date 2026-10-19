# Enterprise Knowledge Base Assistant

FastAPI backend with both Streamlit and Next.js frontends. Features Groq, SentenceTransformers, FAISS, PDF indexing, tool routing, JWT authentication, and SQLite conversation memory.

## Local setup

1. Create an environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env`, set `GROQ_API_KEY`, and replace `JWT_SECRET_KEY` with a long random value.
3. Optional: enable public web search by adding a Tavily key to `.env`:

```env
TAVILY_API_KEY=your-tavily-api-key
TAVILY_MAX_RESULTS=5
TAVILY_SEARCH_DEPTH=advanced
```

Without a key, web-search requests return a clear configuration message and document-only RAG continues to work.

4. Start the API from the repository root:

```powershell
$env:PYTHONPATH = "backend"
uvicorn main:app --app-dir backend --reload --port 8000
```

4. In another terminal, start Streamlit:

```powershell
streamlit run frontend/app.py --server.port 8501
```

API docs: http://localhost:8000/docs. Health: `/health`; readiness: `/ready`.

## Next.js Web Frontend

A modern React-based frontend is available in the `web/` directory for deployment on Vercel or other platforms.

### Local development:
```powershell
cd web
npm install
npm run dev
```

Access at http://localhost:3000

### Deployment:
See [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) for detailed Vercel deployment instructions.

## Docker

```powershell
docker compose up --build
```

The API is at port 8000 and Streamlit at port 8501. SQLite, per-user uploads, FAISS indexes, and mappings are mounted from `backend/data` and `backend/uploads`.

## Tests and quality

```powershell
python -m compileall -q backend frontend
pytest -q
```

Tests use temporary SQLite paths. Do not run production data through test fixtures.

## Configuration

See `.env.example`. Passwords require at least 4 characters and support long passphrases. Never commit `.env`, API keys, passwords, or JWT secrets. Configure `CORS_ALLOWED_ORIGINS` with the exact frontend origins used in deployment.

## Backup and deployment

Back up `backend/data/enterprise.db`, `backend/data/users/`, and `backend/uploads/users/` together so database ownership and files remain consistent. A container-compatible deployment needs one persistent volume for those paths, a backend service on port 8000, a frontend service on port 8501, and environment variables from `.env.example`.

Smoke test after deployment: open `/health` and `/ready`, register and log in, upload a valid PDF, ask a document question, verify a calculator/time question, delete the PDF, and confirm another account cannot access the first account's conversation or documents.

## Known limitations

The embedding model is downloaded at first use, Groq is required for planner and RAG responses, and rate limiting and scheduled backups should be provided at the ingress/operations layer before public exposure.

## Release notes

### 2026-08-23

- Repaired authenticated conversation routes and startup syntax.
- Added upload validation, no-index fallback, Docker support, CI, tests, and Streamlit client.
