# Deployment preparation

## Render free-tier demo

The root `render.yaml` defines separate Docker web services for the API and Streamlit frontend. In Render, create a Blueprint from this repository and select the branch containing `render.yaml`. Enter `GROQ_API_KEY` and a unique, random `JWT_SECRET_KEY` when prompted; keep these values in Render's secret environment settings, not in the repository.

This configuration uses free instances, which can sleep when idle and have ephemeral filesystems. The SQLite database, uploaded documents, and FAISS indexes can be lost when an instance restarts or is redeployed. Use this only for a disposable demo; use persistent storage and backups for real user data. The first request after idle may also take longer while the backend starts.

## Services

Run `backend/Dockerfile` as the API on port 8000 and `frontend/Dockerfile` as Streamlit on port 8501. Set the frontend `BACKEND_URL` to the internal backend URL and set backend `CORS_ALLOWED_ORIGINS` to the public frontend origin.

## Required variables

`GROQ_API_KEY`, `GROQ_MODEL`, `JWT_SECRET_KEY`, `CORS_ALLOWED_ORIGINS`, `BACKEND_URL`, and `MAX_UPLOAD_BYTES`. Never put secrets in an image or repository.

## Storage

Attach persistent storage to `/app/backend/data` and `/app/backend/uploads`. Keep the SQLite database, user FAISS indexes, mappings, and uploads in the same backup schedule.

## Operations

```powershell
docker compose up --build -d
docker compose logs -f backend
```

Back up the SQLite file and both user storage trees before upgrades. Restore them together and verify ownership mappings.

## Smoke checklist

- `/health` returns healthy and `/ready` returns ready.
- Registration, login, expired/invalid token rejection work.
- Upload, list, re-index, delete, and citation responses work.
- Two users cannot read each other's conversations or files.
- Calculator/time routing works without document data.
- Groq and FAISS failures produce clear API errors.
