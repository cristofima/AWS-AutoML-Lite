FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy training package (new modular structure)
COPY . ./training/

# Set Python path to find the training package
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Entry point (now uses package structure)
CMD ["python", "-m", "training.main"]
