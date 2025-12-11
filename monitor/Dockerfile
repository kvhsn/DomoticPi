FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy monitor package files
COPY *.py ./

# Set Python path
ENV PYTHONPATH=/app

# Run the monitoring script
CMD ["python3", "main.py"]
