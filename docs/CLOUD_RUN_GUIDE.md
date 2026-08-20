# Google Cloud Run — beginner guide (backend)

This deploys the **FastAPI + YOLOv8** API to Cloud Run.  
Frontend stays on **Vercel** (or local). Point `VITE_API_URL` at your Cloud Run URL.

---

## Before you start (checklist)

- [ ] Google account (Gmail)
- [ ] Credit/debit card for Google Cloud billing (required to turn APIs on; free tier still applies)
- [ ] This GitHub repo pushed:  
  `https://github.com/shayan9689/Computer-Vision-Object-Detection-Classification-System`
- [ ] ~20–40 minutes the first time

> Google asks for a card even for free use. New accounts often get **$300 trial credit**. Cloud Run also has a **monthly free tier**. Stay on the settings in this guide to keep cost near $0 for a portfolio demo.

---

## Part A — Create a Google Cloud project

### A1. Open Google Cloud Console
1. Go to: https://console.cloud.google.com/
2. Sign in with your Google account.

### A2. Create / select a project
1. Top bar: click the **project dropdown** (next to “Google Cloud”).
2. Click **New Project**.
3. **Project name:** `visionlab-cv` (any name is fine).
4. Leave Organization as default if shown.
5. Click **Create**.
6. Wait a few seconds, then open the project dropdown again and **select** `visionlab-cv`.

### A3. Enable billing (required)
1. Left menu (☰) → **Billing**.
2. Click **Link a billing account** / **Manage billing accounts**.
3. Create a billing account if needed (add card).
4. Link it to project `visionlab-cv`.

Without billing linked, Cloud Run deploy will fail.

---

## Part B — Enable required APIs

1. Left menu ☰ → **APIs & Services** → **Library**.
2. Search and enable each (click → **Enable**):
   - **Cloud Run API**
   - **Cloud Build API**
   - **Artifact Registry API**

Or open this and enable while your project is selected:  
https://console.cloud.google.com/apis/library

---

## Part C — Deploy with Cloud Shell (recommended for beginners)

Cloud Shell is a free Linux terminal **inside** the browser. No local install needed.

### C1. Open Cloud Shell
1. Top-right of Console: click the **Cloud Shell** icon (`>_`).
2. Click **Continue** / **Authorize** if asked.
3. Wait until you see a terminal prompt like:  
   `yourname@cloudshell:~ (visionlab-cv)$`

Confirm project:

```bash
gcloud config get-value project
```

If empty / wrong:

```bash
gcloud config set project visionlab-cv
```

(Use your real project **ID** if different — find it under project dropdown → project ID.)

### C2. Clone your GitHub repo

```bash
cd ~
git clone https://github.com/shayan9689/Computer-Vision-Object-Detection-Classification-System.git
cd Computer-Vision-Object-Detection-Classification-System
```

If the repo is private, Cloud Shell will ask you to authenticate to GitHub.

### C3. Build the container image

This can take **10–20 minutes** (PyTorch + Ultralytics).

```bash
gcloud builds submit --tag gcr.io/$(gcloud config get-value project)/visionlab-api
```

What this does:
- Uploads source (respects `.gcloudignore`)
- Builds the `Dockerfile`
- Downloads `yolov8n.pt` into the image
- Stores the image in Google Container Registry

Wait until you see **SUCCESS**.

### C4. Deploy to Cloud Run

```bash
gcloud run deploy visionlab-api \
  --image gcr.io/$(gcloud config get-value project)/visionlab-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 2 \
  --min-instances 0 \
  --set-env-vars "CORS_ORIGINS=http://localhost:5173"
```

Prompts:
- **Allow unauthenticated:** `y` (so your Vercel frontend can call it)

When finished, Cloud Shell prints a URL like:

```text
https://visionlab-api-xxxxxxxx-uc.a.run.app
```

**Copy that URL** — you need it next.

### C5. Test the API in browser

Open:

```text
https://YOUR-CLOUD-RUN-URL/health
```

You should see JSON like:

```json
{"status":"ok","service":"cv-detection-api","phase":12}
```

Also try docs:

```text
https://YOUR-CLOUD-RUN-URL/docs
```

---

## Part D — Connect frontend (Vercel or local)

### Local frontend

Edit `frontend/.env`:

```env
VITE_API_URL=https://YOUR-CLOUD-RUN-URL
```

No trailing slash.

Restart:

```bash
cd frontend
npm run dev
```

### Vercel frontend
1. Vercel → your project → **Settings** → **Environment Variables**
2. Add:
   - Name: `VITE_API_URL`
   - Value: `https://YOUR-CLOUD-RUN-URL`
3. **Redeploy** the frontend (env vars apply at build time for Vite).

### Update CORS on Cloud Run (after you have Vercel URL)

In Cloud Shell:

```bash
gcloud run services update visionlab-api \
  --region us-central1 \
  --set-env-vars "CORS_ORIGINS=https://YOUR-VERCEL-APP.vercel.app,http://localhost:5173"
```

---

## Part E — Useful Console navigation (visual map)

| Goal | Path |
|------|------|
| Projects | Top bar project dropdown |
| Billing | ☰ → Billing |
| Enable APIs | ☰ → APIs & Services → Library |
| See Cloud Run services | ☰ → Cloud Run |
| Open your service | Cloud Run → click `visionlab-api` |
| Logs (errors) | Cloud Run → `visionlab-api` → **Logs** |
| URL | Cloud Run → `visionlab-api` → top **URL** |
| Env vars later | Cloud Run → service → **Edit & deploy new revision** → Containers → Variables |

---

## Part F — Settings that keep cost low

Use these (already in the deploy command):

| Setting | Value | Why |
|---------|--------|-----|
| Memory | **2Gi** | Torch + YOLO need RAM; 512Mi will crash |
| CPU | 1 | Enough for nano model |
| Min instances | **0** | Scale to zero when idle (free-tier friendly) |
| Max instances | **2** | Caps surprise traffic |
| Timeout | 300s | First request after sleep can be slow |

First request after idle may take **30–90 seconds** (cold start). That is normal on free/min=0.

---

## Part G — Common problems

### 1) “Billing account not configured”
Link billing (Part A3).

### 2) Build fails / timeout
Re-run `gcloud builds submit ...`. First build is heavy.

### 3) `/health` works but `/predict` returns 503
Model missing — rebuild with the updated Dockerfile that downloads `yolov8n.pt`.

### 4) Frontend says CORS / network error
- Set `VITE_API_URL` correctly and redeploy frontend
- Update `CORS_ORIGINS` to include your Vercel domain

### 5) Out of memory
Raise memory to `2Gi` (or `4Gi` if needed):

```bash
gcloud run services update visionlab-api --region us-central1 --memory 2Gi
```

### 6) Very slow first request
Cold start. Click once, wait, then try again. Optional (costs more): `--min-instances 1`.

---

## Part H — Update after code changes

```bash
cd ~/Computer-Vision-Object-Detection-Classification-System
git pull
gcloud builds submit --tag gcr.io/$(gcloud config get-value project)/visionlab-api
gcloud run deploy visionlab-api \
  --image gcr.io/$(gcloud config get-value project)/visionlab-api \
  --region us-central1
```

---

## What success looks like

1. `https://...run.app/health` → `"status":"ok"`
2. `https://...run.app/docs` → Swagger UI
3. VisionLab UI (local or Vercel) uploads an image and shows boxes/results
