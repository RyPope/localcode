# Build context: repository root.
FROM node:22.23.4-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

FROM python:3.14.10-slim-trixie
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --gid 1000 localcode \
 && useradd --uid 1000 --gid 1000 --no-create-home --shell /usr/sbin/nologin localcode \
 && mkdir -p /data && chown localcode:localcode /data
WORKDIR /app
COPY backend/pyproject.toml backend/
COPY backend/localcode backend/localcode
RUN pip install --no-cache-dir ./backend
COPY --from=web /web/dist /app/web_dist
# A copy of the repo-kept problems for runs without the compose bind mount (which takes precedence).
COPY content /content
COPY backend/docker-entrypoint.sh /usr/local/bin/docker-entrypoint
ENV LOCALCODE_WEB=/app/web_dist LOCALCODE_DATA=/data LOCALCODE_CONTENT=/content HOME=/tmp PYTHONDONTWRITEBYTECODE=1
EXPOSE 4173
ENTRYPOINT ["docker-entrypoint"]
CMD ["uvicorn", "localcode.api.app:app", "--host", "0.0.0.0", "--port", "4173", "--no-server-header"]
