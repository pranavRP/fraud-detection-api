# Match the Python version the model bundle was trained/pickled with (3.9)
# so joblib.load() in src/model.py deserializes cleanly.
FROM python:3.9-slim

# Faster, quieter, unbuffered logs so `docker compose logs` is live.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install deps first so this layer is cached unless requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code. The model (models/) and dataset (data/) are mounted at runtime
# via docker-compose volumes rather than baked into the image.
COPY src ./src

EXPOSE 8000

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
