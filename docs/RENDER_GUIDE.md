# Render backend deploy guide (beginner)

Deploy the **FastAPI + YOLOv8** API to [Render](https://render.com).  
Keep the frontend on **Vercel** (or local) and point `VITE_API_URL` at your Render URL.

---

## Before you start

- [ ] GitHub repo is up to date (this project)
- [ ] Render account: https://dashboard.render.com/ (sign up with GitHub is easiest)
- [ ] ~20–40 minutes for the first Docker build

### Important memory note

YOLOv8 + PyTorch needs a lot of RAM.

| Render plan | RAM | Likely result |
|-------------|-----|----------------|
| **Free** | 512 MB | May crash (Out of Memory) on `/predict` |
| **Starter** | 512 MB | Same risk |
| **Standard** | 2 GB | Recommended if Free OOMs |

**Try Free first.** If `/health` works but `/predict` dies, upgrade to **Standard (2 GB)** or use Google Cloud Run (easier 2Gi).

---

## Method A — Click-by-click (recommended)

### 1) Open Render
1. Go to https://dashboard.render.com/
2. Sign in with **GitHub**

### 2) New Web Service
1. Click **New +** (top right)
2. Click **Web Service**
3. Connect your GitHub if asked → **Configure account** → allow access to  
   `Computer-Vision-Object-Detection-Classification-System`
4. Find the repo → click **Connect**

### 3) Service settings (fill exactly)

| Field | Value |
|-------|--------|
| **Name** | `visionlab-api` |
| **Region** | Oregon (or closest to you) |
| **Branch** | `main` |
| **Runtime** | **Docker** |
| **Dockerfile Path** | `./Dockerfile` |
| **Docker Context** | `.` (repo root) |
| **Instance type** | **Free** (upgrade later if needed) |

Leave **Docker Command** empty (Dockerfile `CMD` is enough).

### 4) Environment variables
Click **Environment** → **Add Environment Variable**:

| Key | Value |
|-----|--------|
| `CORS_ORIGINS` | `http://localhost:5173` |

Later, when Vercel is live, change to:

```text
https://YOUR-APP.vercel.app,http://localhost:5173
```

(No spaces issues if you use commas; no trailing slash on URLs.)

### 5) Health check (optional but good)
- **Health Check Path:** `/health`

### 6) Create
1. Click **Create Web Service**
2. Watch **Logs** / **Events**
3. First build downloads Torch + YOLO weights → often **15–30+ minutes**

Wait until status is **Live**.

### 7) Copy your URL
On the service page, copy the URL, e.g.:

```text
https://visionlab-api.onrender.com
```

### 8) Test in browser
Open:

- `https://YOUR-SERVICE.onrender.com/health`  
  → should show `"status":"ok"`
- `https://YOUR-SERVICE.onrender.com/docs`  
  → Swagger UI

Then try **POST /predict** from the docs page with a small photo.

---

## Method B — Blueprint (`render.yaml`)

1. Dashboard → **New +** → **Blueprint**
2. Select this GitHub repo
3. Render reads `render.yaml`
4. Set `CORS_ORIGINS` when prompted (sync: false)
5. Apply

Same Docker build as Method A.

---

## Connect the frontend

### Local
Edit `frontend/.env`:

```env
VITE_API_URL=https://visionlab-api.onrender.com
```

No trailing `/`. Then restart:

```bash
cd frontend
npm run dev
```

### Vercel
1. Project → **Settings** → **Environment Variables**
2. `VITE_API_URL` = `https://visionlab-api.onrender.com`
3. **Redeploy** frontend (Vite bakes env at build time)
4. Update Render env `CORS_ORIGINS` to include your Vercel domain
5. **Manual Deploy** → **Deploy latest commit** on Render (or just restart) so CORS updates

---

## Free tier behavior (normal)

- Service **sleeps** after ~15 minutes idle  
- First request after sleep can take **30–90 seconds** (cold start)  
- Wait once; later requests are faster until it sleeps again  

---

## Common problems

### Build fails
- Confirm Dockerfile is at **repo root**
- Runtime must be **Docker**, not Python
- Check Logs for `curl` / pip errors → **Manual Deploy** → clear build cache if available, redeploy

### Live but `/predict` returns 500 / service restarts
- Almost always **Out of Memory** on 512 MB  
- Upgrade instance to **Standard (2 GB)**  
- Or switch to Cloud Run with `--memory 2Gi` (see `docs/CLOUD_RUN_GUIDE.md`)

### CORS / frontend blocked
- Set `CORS_ORIGINS` to your exact frontend origin(s)
- Redeploy frontend after changing `VITE_API_URL`

### `No module named 'app'`
- Should not happen with this Dockerfile (`WORKDIR /app/backend`, `PYTHONPATH` set). If you changed Dockerfile, restore from repo.

### Model missing / 503
- Dockerfile must download `yolov8n.pt` into `ml/models/pretrained_yolov8n.pt`  
- Do not remove that `RUN curl ...` step

---

## After code changes

1. Push to `main` on GitHub  
2. Render auto-deploys (if Auto-Deploy is on)  
3. Or **Manual Deploy** → **Deploy latest commit**

---

## Success checklist

- [ ] `/health` returns OK  
- [ ] `/docs` opens  
- [ ] Sample image predict works (or you upgraded RAM if OOM)  
- [ ] Frontend `VITE_API_URL` points to Render  
- [ ] `CORS_ORIGINS` includes frontend URL  
