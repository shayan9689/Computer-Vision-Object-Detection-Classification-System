# LinkedIn post draft

**Title idea:** Built an end-to-end Computer Vision Object Detection system (React + FastAPI + YOLOv8)

I just finished a full-stack computer vision project that detects objects in images (and supports video + webcam capture).

**What it does**
- Upload an image → FastAPI runs YOLOv8 inference → React draws bounding boxes with confidence scores
- Dataset pipeline on COCO128, training/eval (mAP, precision, recall), then a reusable inference engine
- Video frame sampling with latency/FPS reporting

**Stack**
React + Vite + Tailwind · FastAPI · PyTorch / Ultralytics YOLOv8 · OpenCV · GitHub  
Deploy targets: Vercel (frontend) + Railway (API)

**Why I built it**
To practice the full ML product loop — data, training, evaluation, API design, and a clean UI — not just a notebook demo.

Repo: [add your GitHub URL]
Live demo: [add Vercel URL after deploy]

#ComputerVision #ObjectDetection #YOLOv8 #FastAPI #ReactJS #MachineLearning #Portfolio
