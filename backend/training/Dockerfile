FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
# Lock file provides reproducible builds with exact versions
# Fallback to requirements.txt if lock doesn't exist (dev flexibility)
COPY requirements.txt requirements.lock* ./
RUN if [ -f requirements.lock ]; then \
        pip install --no-cache-dir -r requirements.lock; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# Copy training scripts
COPY *.py ./

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Entry point
CMD ["python", "train.py"]
