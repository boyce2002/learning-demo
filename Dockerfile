FROM node:22-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/sparklab.sqlite3 \
    FRONTEND_DIST_PATH=/app/frontend/dist \
    DEMO_MODE=true \
    DEMO_RESET_ENABLED=false \
    PUBLIC_DEMO_ENABLED=true \
    VISITOR_RESET_ENABLED=true \
    COOKIE_SECURE=true \
    APP_TIMEZONE=Asia/Shanghai

WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend/ /app/backend/
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

RUN mkdir -p /data

WORKDIR /app/backend
EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
