# Build context: repository root.
FROM node:22.12.0-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

FROM python:3.12.12-slim-trixie
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/pyproject.toml backend/
COPY backend/localcode backend/localcode
RUN pip install --no-cache-dir ./backend
COPY --from=web /web/dist /app/web_dist
ENV LOCALCODE_WEB=/app/web_dist LOCALCODE_DATA=/data
EXPOSE 4173
CMD ["uvicorn", "localcode.api.app:app", "--host", "0.0.0.0", "--port", "4173"]
