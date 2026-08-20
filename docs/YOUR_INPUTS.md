# YOUR INPUTS — what you need to do

Everything through Phase 12 is implemented and verified **locally**. Cloud go-live and publishing need your accounts/actions.

## 1. Run the demo locally (required to see the UI)

**Terminal A — API**
```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal B — UI**
```bash
cd frontend
npm run dev
```

Open http://localhost:5173  
Try: upload image → Run detection · optional video/webcam tabs.

## 2. GitHub (if not pushed yet)

1. Create a GitHub repo
2. Commit & push this project
3. Paste the repo URL into `docs/LINKEDIN_POST.md`

## 3. Deploy (Phase 11 — your logins)

### Railway (backend)
1. New project from GitHub
2. Use `Dockerfile` at repo root **or** backend `Procfile` / `railway.toml`
3. Ensure `ml/models/best.pt` is available on the server
4. Set env: `CORS_ORIGINS=https://YOUR_VERCEL_URL`
5. Copy public API URL

### Vercel (frontend)
1. Import repo · Root = `frontend`
2. Env: `VITE_API_URL=https://YOUR_RAILWAY_URL` (no trailing slash)
3. Deploy · copy frontend URL

Details: `docs/PHASE11_DEPLOY.md`

## 4. Portfolio publish (Phase 12)

1. Take 2–3 screenshots/GIF of the working UI
2. Edit & post `docs/LINKEDIN_POST.md` (add GitHub + live URLs)
3. Optional: create a GitHub Release (e.g. `v1.0.0`)

## Not required from you for code to work locally

- Dataset (already downloaded under `data/raw/coco128`)
- Model training (weights in `ml/models/best.pt`)
- Frontend/backend feature code (Phases 1–12 done)
