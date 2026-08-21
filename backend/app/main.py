"""Computer Vision Detection API - FastAPI application entrypoint."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import health, predict, video

app = FastAPI(
    title="CV Object Detection API",
    description="Inference API for the Computer Vision Object Detection and Classification System",
    version="1.0.0",
)

default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
raw = os.getenv("CORS_ORIGINS", "").strip()
extra = [o.strip().rstrip("/") for o in raw.split(",") if o.strip() and o.strip() != "*"]
allow_all = raw == "*" or os.getenv("ALLOW_ALL_CORS", "").lower() in {"1", "true", "yes"}

# Browser calls from Vercel fail unless the exact origin is allowed.
# Also allow any https://*.vercel.app preview/production URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else (default_origins + extra),
    allow_origin_regex=None if allow_all else r"https://.*\.vercel\.app",
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(predict.router)
app.include_router(video.router)


@app.get("/")
def root():
    return {
        "message": "CV Object Detection API",
        "docs": "/docs",
        "health": "/health",
        "predict": "/predict",
        "predict_video": "/predict/video",
    }
