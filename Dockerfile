FROM python:3.11-slim

# Avoid Python buffering
ENV PYTHONUNBUFFERED=1

# Create working directory
WORKDIR /app

# Copy dependencies first
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose Railway port
EXPOSE 8080

# Start FastAPI with Gunicorn + UvicornWorker
CMD ["gunicorn", "main:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]
