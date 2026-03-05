FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
