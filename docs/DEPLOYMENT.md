# Deployment Guide

## Local Development

1. Copy `.env.example` to `.env`.
2. Install frontend dependencies with `npm install`.
3. Install backend dependencies from `apps/api` with `python -m pip install -e ".[dev]"`.
4. Run `npm run dev:api` and `npm run dev:web`.

## Docker Deployment

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Services:

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

## Production Notes

- Replace owner-mode headers with JWT/session auth in `app/core/security.py`.
- Use PostgreSQL by setting `DATABASE_URL=postgresql+asyncpg://...`.
- Mount `models/` into the API container and point `LOCAL_MODEL_ID` to the local model path.
- Keep ChromaDB and upload directories on persistent volumes.
- Put the API behind a local reverse proxy when exposing beyond localhost.
- Add provider-specific implementations behind the web search and IoT tools before enabling them.
