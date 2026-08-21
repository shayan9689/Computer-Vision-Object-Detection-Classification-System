# 🎯 VISIONLAB AI  
### Computer Vision Object Detection & Classification System

A full-stack AI app that finds objects in photos (and can sample video / webcam frames), draws boxes, and explains the scene in simple language.

Built as an end-to-end learning + portfolio project: **data → train/eval → inference engine → FastAPI → React UI → cloud deploy**.

---

## ✨ What it does

| Feature | Description |
|--------|-------------|
| 🖼️ **Image detection** | Upload a photo → get boxes, labels, and scores |
| 🧠 **Scene summary** | Plain-English caption, category counts, insights |
| 🎚️ **Match Strictness** | Client-friendly **Low / Medium / High** (not a confusing slider) |
| 🎥 **Video mode** | Sample frames, report latency / effective FPS |
| 📷 **Live cam** | Capture a webcam frame and run detection |
| 📘 **API docs** | Interactive Swagger at `/docs` |

> 💡 This model knows **everyday COCO objects** (people, cars, animals, furniture, phones, bottles…).  
> It does **not** specialize in picture frames / wall art unless you train a custom model.

---

## 🏗️ Architecture

```text
User
  │
  ▼
React (VisionLab UI)  ──►  FastAPI  ──►  YOLOv8n (CPU)  ──►  JSON + analysis
   Vercel / local              Cloud Run / local              ml/inference/
```

- Frontend never loads the model — all inference goes through the API  
- CORS is configured for local Vite + your production frontend URL  

---

## 🧰 Tech stack

| Layer | Tools |
|------|--------|
| 💻 Frontend | React · Vite · Tailwind CSS |
| ⚙️ Backend | Python · FastAPI · Uvicorn |
| 🧪 CV / ML | OpenCV · PyTorch · Ultralytics YOLOv8n |
| ☁️ Deploy | **Frontend → Vercel** · **Backend → Render** (or Google Cloud Run) |

---

## 📁 Project structure

```text
├── frontend/          # VisionLab AI React UI
├── backend/           # FastAPI API (health, predict, video)
├── ml/
│   ├── inference/     # DetectionEngine + scene analysis
│   ├── scripts/       # Phase 2–7 dataset/train/eval helpers
│   ├── configs/       # Data / preprocess configs
│   └── models/        # Local .pt weights (gitignored)
├── data/              # Local datasets (gitignored contents)
├── docs/              # Guides, phase reports, portfolio notes
├── logos/             # Brand / UI icons
├── Dockerfile         # Backend Docker image (Render / Cloud Run)
├── render.yaml        # Render Blueprint config
└── README.md
```

---

## 🚀 Quick start (local)

### ✅ Requirements

- Python **3.12+**
- Node.js **20+** / npm  
- Git  
- No virtualenv required for this project setup (system Python is fine)

### 1️⃣ Backend API

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check:

- Health → http://127.0.0.1:8000/health  
- Docs → http://127.0.0.1:8000/docs  

> ⚠️ Run uvicorn from the **`backend`** folder (not repo root), or you’ll get `No module named 'app'`.

### 2️⃣ Frontend UI

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open → http://localhost:5173  

`frontend/.env` should look like:

```env
VITE_API_URL=http://127.0.0.1:8000
```

### 3️⃣ Model weights (local)

Place weights here (or copy from training):

```text
ml/models/pretrained_yolov8n.pt
```

If you already have `yolov8n.pt` in the repo root from Ultralytics, copy it:

```bash
# PowerShell
Copy-Item .\yolov8n.pt .\ml\models\pretrained_yolov8n.pt
```

Cloud / Docker builds **download** weights automatically during the image build.

---

## 🔌 API reference

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | ✅ Service health |
| `POST` | `/predict` | 🖼️ Image detection (`multipart` file) |
| `POST` | `/predict/video` | 🎬 Video frame sampling |
| `GET` | `/docs` | 📖 Swagger UI |

### Example image request

```bash
curl -X POST "http://127.0.0.1:8000/predict?conf=0.45" \
  -F "file=@your-photo.jpg"
```

### Match Strictness (UI) → API `conf`

| UI choice | Approx. threshold | Meaning |
|-----------|-------------------|---------|
| 🟢 Low | `0.25` | More results (may include unsure boxes) |
| 🟡 Medium | `0.45` | Balanced (default) |
| 🔴 High | `0.70` | Only strong matches |

---

## 🧪 Tests

```bash
cd backend
pytest
```

---

## ☁️ Deployment

You need **both** hosts for a live demo:

| Piece | Platform | Why |
|-------|----------|-----|
| Frontend | **Vercel** | Static React app |
| Backend | **Render** (or Cloud Run) | Python + Torch + YOLO (not for Vercel alone) |

### Backend → Render (current path)

Deep beginner walkthrough (every click):

👉 **[docs/RENDER_GUIDE.md](docs/RENDER_GUIDE.md)**

Summary:

1. Render → **New +** → **Web Service** → connect this GitHub repo  
2. Runtime **Docker**, Dockerfile `./Dockerfile`  
3. Set env `CORS_ORIGINS=http://localhost:5173`  
4. Wait for build → test `/health` and `/docs`  
5. Point frontend `VITE_API_URL` at the Render URL  

> Free Render is **512 MB RAM** — YOLO may run out of memory. If `/predict` crashes, upgrade to **Standard (2 GB)** or use Cloud Run.

### Backend → Google Cloud Run (alternative)

👉 **[docs/CLOUD_RUN_GUIDE.md](docs/CLOUD_RUN_GUIDE.md)**

### Frontend → Vercel

1. Import this GitHub repo  
2. Root directory: `frontend`  
3. Env var: `VITE_API_URL=https://your-render-url` (no trailing slash)  
4. Redeploy after changing env vars  

---

## 📊 Training notes (local / optional)

Phases 2–6 include COCO128 experiments on CPU:

| Stage | mAP@0.5 (approx.) |
|-------|-------------------|
| Baseline eval | ~0.54 |
| Improved run | ~0.70 |

For everyday photos, the app prefers **official pretrained YOLOv8n** (better general quality than a tiny fine-tune).

---

## 📚 Documentation

| Doc | What’s inside |
|-----|----------------|
| [Architecture](docs/ARCHITECTURE.md) | System design |
| [Render guide](docs/RENDER_GUIDE.md) | Backend deploy on Render |
| [Cloud Run guide](docs/CLOUD_RUN_GUIDE.md) | Backend deploy on Google Cloud Run |
| [Your inputs](docs/YOUR_INPUTS.md) | What you still need to do |
| [Portfolio / LinkedIn](docs/PHASE12_PORTFOLIO.md) | Sharing notes |
| [Phase reports](docs/) | Phase 1–12 summaries |

---

## ⚠️ Limits (honest)

- ❌ Not a specialist “frame / wall art” detector (COCO classes only)  
- 🐢 CPU-only inference is slower than GPU  
- 💤 Cloud Run with `min-instances=0` has cold starts (first request can take a while)  
- 🔐 Don’t commit `.env`, secrets, or large `.pt` / dataset files (already gitignored)

---

## 📜 Data & license

- Dataset experiments used **COCO128 / COCO** — check COCO terms before commercial use  
- Model: Ultralytics YOLOv8 (see Ultralytics license)  
- This repo is for learning / portfolio use unless you add your own license

---

## 🙌 Credits

- Ultralytics YOLOv8  
- COCO dataset  
- FastAPI · React · Vite · Tailwind  

---

## ⭐ Status

✅ Phases **1–12** complete locally  
☁️ Backend deploy path: **Render** (or Cloud Run)  
🌐 Frontend deploy path: **Vercel**

If this helped your learning journey, consider starring the repo ⭐
