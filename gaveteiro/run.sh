#!/usr/bin/with-contenv bashio
# shellcheck shell=bash
set -e

# Banco em /share para o add-on SQLite Web conseguir abrir o arquivo;
# imagens no /data privado do add-on.
export DB_PATH="/share/gaveteiro/gaveteiro.db"
export DATA_DIR="/data"

export AUTH_USER="$(bashio::config 'username')"
export AUTH_PASSWORD="$(bashio::config 'password')"
export IMAGE_MAX_SIZE="$(bashio::config 'image_max_size')"

# A versão aparece no cabeçalho do app: sem ela não dá para saber, olhando a
# tela, se o navegador carregou a build nova ou uma em cache.
export APP_VERSION="$(bashio::addon.version)"

mkdir -p /share/gaveteiro

if bashio::config.equals 'password' 'troque-esta-senha'; then
  bashio::log.warning "A senha ainda é a padrão. Troque nas opções do add-on."
fi

bashio::log.info "Gaveteiro iniciando na porta 8099"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8099 --proxy-headers
