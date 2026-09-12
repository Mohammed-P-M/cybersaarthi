FROM python:3.11-slim

WORKDIR /app

# Disable PaddlePaddle PIR/oneDNN path that can fail on PP-OCRv5 models.
ENV FLAGS_enable_pir_api=0

# Install system dependencies for OpenCV and PaddleOCR
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --retries 10 --timeout 120 -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
