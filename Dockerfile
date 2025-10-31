# ===============================
# FastAPI Food Delivery App
# ===============================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev && apt-get clean

# Copy dependency list and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Set environment variable for Google Cloud credentials
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/gcloud_creds.json

# Expose the container port
EXPOSE 8080

# Default command to run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
