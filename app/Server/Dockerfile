# LanguageCoach API image. See context/spec/features/new/aws-deployment.md.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install deps first for better layer caching.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# App code (routers, services, storage, config, main, etc.).
COPY . .

EXPOSE 8000

# STORAGE_BACKEND / DATABASE_URL / OPENAI_API_KEY / JWT_SECRET / CORS_ORIGINS
# are injected by App Runner (Secrets Manager + env), not baked in.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
