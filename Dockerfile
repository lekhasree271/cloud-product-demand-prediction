# Dockerfile for Cloud-Based Product Demand Prediction System
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY data/ ./data/
COPY static/ ./static/
COPY run_app.py .

EXPOSE 8000

CMD ["python", "run_app.py"]
