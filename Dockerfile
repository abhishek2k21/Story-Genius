# Dockerfile for FastAPI Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# ffmpeg is required for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway sets PORT env var, but 8000 is default)
EXPOSE 8000

# Run with Gunicorn for production performance
# Using uvicorn worker class
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
