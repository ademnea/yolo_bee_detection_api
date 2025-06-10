from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import cv2
import numpy as np
import os
import uuid
import tempfile
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
    # Save the uploaded video to a temporary file
    temp_dir = tempfile.gettempdir()
    temp_filename = f"bee_video_{uuid.uuid4()}.mp4"
    video_path = os.path.join(temp_dir, temp_filename)

    contents = await file.read()
    with open(video_path, "wb") as f:
        f.write(contents)

    # Run YOLO tracking on the video using ByteTrack
    results = model.track(
        source=video_path,
        tracker="bytetrack.yaml",  # Uses Ultralytics built-in tracker config
        persist=True,
        verbose=False
    )

    # Count unique bee IDs (assuming class 0 is 'bee')
    unique_ids = set()
    for r in results:
        for box in r.boxes:
            if int(box.cls[0]) == 0 and box.id is not None:
                unique_ids.add(int(box.id[0]))

    # Clean up
    os.remove(video_path)

    return JSONResponse({
        "unique_bee_count": len(unique_ids),
        "bee_ids": list(unique_ids)
    })
