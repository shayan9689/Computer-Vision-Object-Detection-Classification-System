# Phase 11 - Testing, Deployment & Production Setup

## Local verification

```bash
cd backend && pytest
cd frontend && npm run build
```

## Environment variables

| Where | Variable | Purpose |
|-------|----------|---------|
| Railway (backend) | `CORS_ORIGINS` | Comma-separated frontend URLs |
| Railway | `PORT` | Provided automatically |
| Vercel (frontend) | `VITE_API_URL` | Public Railway API base URL |

## Deploy steps (your accounts required)

### Backend → Railway

1. Create a Railway project from this GitHub repo
2. Root / watch path: `backend` (or use repo `Dockerfile`)
3. Add volume or include `ml/models/best.pt` in the deploy image
4. Set `CORS_ORIGINS` to your Vercel URL
5. Confirm `https://<railway>/health` returns OK

### Frontend → Vercel

1. Import the repo in Vercel
2. Root directory: `frontend`
3. Build: `npm run build` · Output: `dist`
4. Set `VITE_API_URL` to the Railway URL (no trailing slash)
5. Redeploy after env change

## Acceptance checklist

- [x] Backend + frontend tests/build scripts ready
- [x] Env examples documented
- [x] Railway / Vercel / Docker configs present
- [ ] Live production URLs (requires your deploy login)
