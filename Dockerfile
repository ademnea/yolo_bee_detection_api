FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY requirements.txt .
COPY api_main.py .
COPY best.pt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for videos
RUN mkdir -p /app/videos

# Expose port
EXPOSE 8000

# Command to run the FastAPI app
CMD ["uvicorn", "api_main:app", "--host", "0.0.0.0", "--port", "8000"]