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
extra = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
allow_origins = default_origins + extra

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins or ["*"],
    allow_credentials=True,
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
