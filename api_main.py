print("Starting imports")
import paramiko
import os
import sys
import cv2
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import torch
import runpod

print("Working on the ssh function")
def ssh_download_files(hostname, username, password, remote_path, local_path, videos):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password)
        sftp = ssh.open_sftp()
        os.makedirs(local_path, exist_ok=True)
        remote_files = sftp.listdir(remote_path)
        
        if not remote_files:
            print(f"No files found in {remote_path}")
            return 0
        
        downloaded_count = 0
        for file_name in remote_files:
            if file_name in videos:
                remote_file_path = os.path.join(remote_path, file_name).replace('\\', '/')
                local_file_path = os.path.join(local_path, file_name)
                print(f"Downloading {file_name}...")
                sftp.get(remote_file_path, local_file_path)
                print(f"Downloaded {file_name} to {local_file_path}")
                downloaded_count += 1
        
        return downloaded_count
    
    except Exception as e:
        print(f"An error occurred during download: {str(e)}")
        raise Exception(f"Download error: {str(e)}")
    finally:
        if 'sftp' in locals():
            sftp.close()
        if 'ssh' in locals():
            ssh.close()

print("Defining process video function")
def process_video(video_path, yolo_model, deepsort_tracker):
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error opening video {video_path}")
            return 0
        
        unique_bee_ids = set()
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            results = yolo_model(frame, conf=0.5, iou=0.7)
            
            # Format detections for DeepSort
            detections = []
            for box in results[0].boxes:
                if results[0].names[int(box.cls)] == "item":
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf)
                    detections.append(([x1, y1, x2-x1, y2-y1], conf, "item"))
            
            # Update tracks with DeepSort
            tracks = deepsort_tracker.update_tracks(detections, frame=frame)
            for track in tracks:
                if not track.is_confirmed() or track.time_since_update > 1:
                    continue
                track_id = track.track_id
                unique_bee_ids.add(track_id)
            
            if frame_count % 100 == 0:
                print(f"Processed {frame_count} frames for {os.path.basename(video_path)}")
        
        cap.release()
        bee_count = len(unique_bee_ids)
        print(f"Video {os.path.basename(video_path)}: Detected {bee_count} unique bees")
        
        return bee_count
    
    except Exception as e:
        print(f"Error processing video {video_path}: {str(e)}")
        return 0
print("Defining a print handler function")
def handler(job):
    print("Extracting videos from job")
    # Extract input from the job
    video_list = job["input"].get("videos", [])
    if not video_list:
        return {"error": "No videos provided in input"}

    # Configuration
    print("Initializing credentials")
    hostname = os.getenv("SSH_HOST", "196.43.168.57")
    username = os.getenv("SSH_USER", "hivemonitor")
    password = os.getenv("SSH_PASS", "Ad@mnea321")
    remote_path = "/var/www/html/ademnea_website/public/hivevideo"
    local_path = "./videos"  # Docker container path
    weights_path = "./best.pt"  # Docker container path
    
    # Load YOLOv8 model
    print("Loading weights")
    try:
        model = YOLO(weights_path)
        print(f"Loaded YOLOv8 model from {weights_path}")
    except Exception as e:
        return {"error": f"Error loading YOLOv8 model: {str(e)}"}
    
    print("Initializing deeosort")
    # Initialize DeepSort
    try:
        deepsort = DeepSort(
            max_age=30,
            n_init=3,
            nn_budget=100,
            embedder="mobilenet",
            embedder_gpu=torch.cuda.is_available()
        )
        print("Initialized DeepSORT tracker")
    except Exception as e:
        return {"error": f"Error initializing DeepSORT: {str(e)}"}
    
    print("Downloading videos from server")
    # Download videos
    try:
        downloaded_count = ssh_download_files(hostname, username, password, remote_path, local_path, video_list)
        if downloaded_count == 0:
            return {"error": "No matching videos found in remote directory"}
    except Exception as e:
        return {"error": str(e)}
    
    # Process videos and collect results
    print("processing videos")
    results = {}
    for video_name in video_list:
        video_path = os.path.join(local_path, video_name)
        if os.path.exists(video_path):
            bee_count = process_video(video_path, model, deepsort)
            results[video_name] = bee_count
        else:
            results[video_name] = 0
            print(f"Video {video_name} not found in {local_path}")
    print("Returning results")
    return {"results": results}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
