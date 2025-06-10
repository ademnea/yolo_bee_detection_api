from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import cv2
import numpy as np
import os
from ultralytics import YOLO

# Path to local model weights
MODEL_PATH = "best.pt"

# Load model from local file
model = YOLO(MODEL_PATH)

# FastAPI setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def get_upload_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/detect/")
async def detect(file: UploadFile = File(...)):
    contents = await file.read()

    # Save uploaded video
    with open("temp_video.mp4", "wb") as f:
        f.write(contents)

    cap = cv2.VideoCapture("temp_video.mp4")
    bee_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model.predict(frame)
        for r in results:
            bee_count += sum(1 for c in r.boxes.cls if int(c) == 0)  # 0 = 'bee'

    cap.release()
    os.remove("temp_video.mp4")

    return JSONResponse({"bee_count": bee_count})
