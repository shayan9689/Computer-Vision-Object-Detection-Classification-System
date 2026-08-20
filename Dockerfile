# Cloud Run backend image (FastAPI + YOLOv8 CPU)
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend \
    PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# CPU-only PyTorch (smaller / correct for Cloud Run free CPU)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY backend/requirements-cloudrun.txt /app/requirements-cloudrun.txt
RUN pip install --no-cache-dir -r /app/requirements-cloudrun.txt

COPY backend /app/backend
COPY ml /app/ml

# Weights are gitignored locally — download during image build
RUN mkdir -p /app/ml/models \
    && curl -L --fail -o /app/ml/models/pretrained_yolov8n.pt \
      https://github.com/ultralytics/assets/releases/download/v8.4.0/yolov8n.pt \
    && python -c "from pathlib import Path; p=Path('/app/ml/models/pretrained_yolov8n.pt'); assert p.exists() and p.stat().st_size > 1_000_000, p.stat().st_size"

WORKDIR /app/backend

# Cloud Run injects $PORT (must use shell form)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
