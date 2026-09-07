# MindVault production image: multi-stage build.
# Stage 1: build the React frontend.
FROM node:22-alpine AS web-build
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime.
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MV_HOST=0.0.0.0 \
    MV_WEB_DIST=/app/web \
    MV_HOME=/data \
    # Hosts like Render inject $PORT; the entrypoint below passes it through.
    MV_PORT=8000

RUN useradd --create-home --uid 10001 mindvault \
    && mkdir -p /data /app/web \
    && chown -R mindvault:mindvault /data /app/web

WORKDIR /app

# Install backend with its runtime dependencies (no ML extra by default).
COPY backend/pyproject.toml backend/README.md ./
COPY backend/mindvault ./mindvault
RUN pip install --no-cache-dir .

# Copy the built frontend.
COPY --from=web-build /web/dist /app/web

USER mindvault
EXPOSE 8000
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('MV_PORT','8000')+'/health', timeout=3)"

# $PORT (injected by hosts like Render) wins over MV_PORT when present.
ENTRYPOINT ["sh", "-c", "exec python -m mindvault --host 0.0.0.0 --port ${PORT:-$MV_PORT}"]
