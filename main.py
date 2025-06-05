from fastapi import FastAPI
import cv2
import numpy as np
from ultralytics import YOLO
from fastapi import File, UploadFile

from fastapi import FastAPI, File, UploadFile
import cv2
import numpy as np
from ultralytics import YOLO

model = YOLO("yolov8m.pt")

app = FastAPI()

@app.post("/detect/")
async def detect_objects(file: UploadFile):
    image_bytes = await file.read()
    image = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    # Perform object detection with YOLOv8
    results = model.predict(image)
    
    # Optional: Format the output nicely
    detections = results[0].boxes.xyxy.tolist() if results else []

    return {"detections": detections}

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}
