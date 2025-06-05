from fastapi import FastAPI, File, UploadFile
import cv2
import numpy as np
import os
import requests
from ultralytics import YOLO

# URL to your Google Drive file (converted to direct download)
MODEL_URL = "https://drive.google.com/uc?export=download&id=1g4VMUerAHNnOeG5Su2xdt2xPFQObFMcB"
MODEL_PATH = "yolov8m.pt"

# Function to download model weights
def download_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading model weights...")
        response = requests.get(MODEL_URL)
        with open(MODEL_PATH, "wb") as f:
            f.write(response.content)
        print("Download complete.")

# Ensure model is downloaded before loading
download_model()

# Load YOLO model
model = YOLO(MODEL_PATH)

# FastAPI app
app = FastAPI()

@app.post("/detect/")
async def detect_objects(file: UploadFile):
    image_bytes = await file.read()
    image = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    results = model.predict(image)
    detections = results[0].boxes.xyxy.tolist() if results else []

    return {"detections": detections}

@app.get("/")
async def root():
    return {"message": "YOLO model ready"}
