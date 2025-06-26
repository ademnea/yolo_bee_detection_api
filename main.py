import paramiko
import os
import sys
import cv2
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import torch

videos = [    "1_2024-10-30_060006.mp4", "1_2024-10-30_120006.mp4", "1_2024-10-30_145008.mp4"]


def ssh_download_files(hostname, username, password, remote_path, local_path):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password)
        sftp = ssh.open_sftp()
        os.makedirs(local_path, exist_ok=True)
        remote_files = sftp.listdir(remote_path)
        
        if not remote_files:
            print(f"No files found in {remote_path}")
            return
        
        downloaded_count = 0
        for file_name in remote_files:
            if file_name in videos:
                remote_file_path = os.path.join(remote_path, file_name).replace('\\', '/')
                local_file_path = os.path.join(local_path, file_name)
                print(f"Downloading {file_name}...")
                sftp.get(remote_file_path, local_file_path)
                print(f"Downloaded {file_name} to {local_file_path}")
                downloaded_count += 1
            else:
                print(f"Skipping {file_name} (not in videos list)")
        
        if downloaded_count == 0:
            print("No matching videos found in remote directory")
        else:
            print(f"Successfully downloaded {downloaded_count} video(s)!")
            
    except Exception as e:
        print(f"An error occurred during download: {str(e)}")
        sys.exit(1)
    finally:
        if 'sftp' in locals():
            sftp.close()
        if 'ssh' in locals():
            ssh.close()


def process_video(video_path, yolo_model, deepsort_tracker, output_path):
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
            
            detections = []
            for box in results[0].boxes:
                if results[0].names[int(box.cls)] == "bee":
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf)
                    detections.append(([x1, y1, x2-x1, y2-y1], conf, "bee"))
            
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
        
        with open(output_path, "a") as f:
            f.write(f"{os.path.basename(video_path)}: {bee_count} unique bees\n")
        
        return bee_count
    
    except Exception as e:
        print(f"Error processing video {video_path}: {str(e)}")
        return 0


def main():
    # Configuration
    hostname = os.getenv("SSH_HOST", "")
    username = os.getenv("SSH_USER", "")
    password = os.getenv("SSH_PASS", "")
    remote_path = "/var/www/html/ademnea_website/public/hivevideo"
    local_path = os.path.dirname(os.path.abspath(__file__))
    weights_path = os.path.join(local_path, "best.pt")
    output_path = os.path.join(local_path, "bee_counts.txt")
    
    # Download videos
    ssh_download_files(hostname, username, password, remote_path, local_path)
    
    # Load YOLOv8 model
    try:
        model = YOLO(weights_path)
        print(f"Loaded YOLOv8 model from {weights_path}")
    except Exception as e:
        print(f"Error loading YOLOv8 model: {str(e)}")
        sys.exit(1)
    
    # Initialize DeepSORT
    try:
        deepsort = DeepSort(
            max_age=30,
            n_init=3,
            nn_budget=100,
            embedder="mobilenet",  # Lightweight embedder, no external CLIP dependency
            embedder_gpu=torch.cuda.is_available()
        )
        print("Initialized DeepSORT tracker")
    except Exception as e:
        print(f"Error initializing DeepSORT: {str(e)}")
        sys.exit(1)
    
    # Process each downloaded video
    for video_name in videos:
        video_path = os.path.join(local_path, video_name)
        if os.path.exists(video_path):
            process_video(video_path, model, deepsort, output_path)
        else:
            print(f"Video {video_name} not found in {local_path}")


if __name__ == "__main__":
    main()
