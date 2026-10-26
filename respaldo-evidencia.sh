#!/usr/bin/env bash
# Respalda ~/lab/evidencias de las 5 estaciones en ./evidencias/<estacion> y lo sube al fork
cd /workspaces/retail-ot-hardening || exit 1
mkdir -p evidencias
for ws in ws-hmi ws-engineering ws-vendor ws-soc ws-corporate; do
  if docker compose exec -T "$ws" test -d /home/student/lab/evidencias 2>/dev/null; then
    rm -rf "evidencias/$ws"
    docker compose cp "$ws:/home/student/lab/evidencias" "evidencias/$ws" \
      && echo "OK  $ws" || echo "ERROR $ws"
  else
    echo "--  $ws (sin evidencia todavía)"
  fi
done
date -u +'%Y-%m-%dT%H:%M:%SZ' > evidencias/ultimo-respaldo-utc.txt
git add evidencias respaldo-evidencia.sh
git commit -m "Respaldo evidencia ${1:-labs} $(date -u +%Y-%m-%d)" && git push
