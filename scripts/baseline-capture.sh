#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p pcaps
FILE="pcaps/retail-$(date -u +%Y%m%dT%H%M%SZ).pcap"
curl -fsS "http://127.0.0.1:${LAB_PORT:-8090}/api/capture" -o "$FILE"
printf 'Captura real guardada: %s\nNo garantiza tráfico solo normal: puede contener prácticas anteriores.\n' "$FILE"
