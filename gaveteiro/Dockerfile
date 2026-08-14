# O Supervisor passa BUILD_FROM conforme a arquitetura (ver build.yaml).
# Precisa ser declarado antes do primeiro FROM para valer no escopo global.
ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.24

# Etapa 1: build do frontend (sai em /build/dist).
FROM node:20-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install
COPY frontend/ ./
RUN npx vite build --outDir dist --emptyOutDir

# Etapa 2: runtime. A imagem base do HA já traz bashio.
FROM ${BUILD_FROM}

WORKDIR /app

COPY backend/requirements.txt ./
# As libs de build só existem durante esta camada; em arquiteturas com wheel
# pronto (amd64/aarch64) elas nem chegam a ser usadas.
RUN apk add --no-cache --virtual .build-deps gcc musl-dev zlib-dev jpeg-dev libwebp-dev \
    && apk add --no-cache zlib jpeg libwebp \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

COPY backend/app ./app
COPY --from=frontend /build/dist ./app/static

COPY run.sh /run.sh
RUN chmod a+x /run.sh

EXPOSE 8099
CMD ["/run.sh"]
