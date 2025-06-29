FROM python:3.9-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy files
COPY requirements.txt .
COPY api_main.py .
COPY best.pt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create videos folder
RUN mkdir -p /app/videos

# Serverless handler doesn't need port exposed
# DO NOT use uvicorn, just let RunPod call the handler

# Set entrypoint for serverless
ENTRYPOINT ["python3", "api_main.py"]
