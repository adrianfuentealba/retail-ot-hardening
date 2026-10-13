# Operación y diagnóstico paso a paso

## 1. Comprobar estado

```sh
docker compose ps -a
docker compose logs --tail=80 plc gateway panel
docker compose logs --tail=80 ws-hmi sensor collector
docker compose logs --tail=80 logstash kibana bootstrap
```

PLC, gateway, panel y estaciones healthy; Elasticsearch healthy; Logstash/Kibana healthy; sensor/collector running; bootstrap exited 0. Si falla una construcción, leer el mensaje exacto. ARM64 soportado por paquetes oficiales osquery; sensor Ubuntu 24.04 contiene Suricata ARM64.

## 2. Validar un escritorio

```sh
docker compose exec -T ws-hmi labctl status
docker compose exec -T ws-hmi osqueryi --version
docker compose exec -T ws-hmi sh -c 'tail -5 /evidence/osquery/osqueryd.results.log'
```

Abrir 6084/vnc.html. Si aparece pantalla noVNC, conectar y esperar XFCE. Sin contraseña porque está en loopback. `No matching security types` requiere confirmar SecurityTypes None en tigervnc y URL correcta, no retirar aislamiento.

## 3. Ver eventos y dashboard

```sh
docker compose exec -T elasticsearch curl -fsS 'http://localhost:9200/retail-ot-*/_count'
docker compose logs bootstrap
```

Discover → retail-ot-* → últimos 15 minutos. Sin documentos: comprobar logs osquery y collector, puerto Logstash 5044 interno, host exacto. El collector envía JSON por TCP a Logstash y conserva cursor solo tras envío; no es un transporte con ack aplicativo/exactly-once. Reinicios/crashes pueden producir duplicados o perder mensajes en vuelo; no equivale a cadena de custodia certificada. Capturar expediente explícitamente.

Dashboards por defecto: general con dos gráficos y cuatro paneles de eventos; cinco dashboards filtrados por host (tres tablas cada uno), además de cinco búsquedas guardadas. No se afirma que sean detecciones SIEM de producción. `event.outcome=blocked` identifica bloqueo del guard; `event.dataset=suricata` firma EVE; `event.dataset=osquery` SQL real.

## 4. Modbus y captura

```sh
docker compose exec -T ws-engineering labctl simulate defrost
docker compose logs --tail=50 sensor
```

Suricata captura interfaz de subred 172.30.40.0/24. PCAP rotativo de hasta 3*8MB, visor payload truncado 160 bytes; no reensambla TCP. Firmas FC06 asumen PDU alineada al inicio del payload: límite de regla simple; usar análisis Modbus de Wireshark para casos de segmentación TCP. OPC UA HEL indica presencia, no Write descifrado ni intrusión.

## 5. Recuperar y resetear

`labctl recover`: frío nominal y contención central de los procesos benignos registrados. Stock permanece comprometido. `labctl reset`: solo endpoint local. Botón portal Restablecer aula: proceso + todos endpoints, evidencia conservada. Los marcadores de downloads permanecen como evidencia. Reiniciar contenedor endpoint puede reiniciar flags no persistentes; declararlo en evaluación, no confundir reinicio con control duradero.

## 6. Cambiar puertos

Copiar `.env.example` a `.env` y editar únicamente puertos locales. Si cambias noVNC/Kibana, abrir direcciones nuevas manualmente: enlaces actuales del portal usan defaults. No cambiar destinos OT, redes internas ni bind de loopback.

## 7. Recursos

Límite agregado de memoria de servicios aproximadamente 16 GB, pero consumo real depende de Firefox, XFCE y volumen Elastic. Usar 16 GB asignada a Docker y reservar memoria al anfitrión. En el dispositivo de construcción se observaron 16 vCPU y cerca de 62.4 GiB disponibles para Docker; no se modificó configuración Docker Desktop.

## 8. Verificación completa

```sh
python3 scripts/verify-lab.py
python3 scripts/verify-observability.py
```

Ejecutar secuencialmente, sin otra práctica concurrente. La segunda prueba verifica WebSocket→RFB en cinco noVNC, proceso sleep observado por osquery, eventos nuevos de permitido/bloqueado por host en Elastic, escritura denegada como estudiante, pipeline Logstash y objetos Kibana. Cada prueba conserva resultados JSON y restablece aula. No confundir refresco de 5 segundos con detección instantánea.

Si el visor de paquetes no muestra FC06 de una acción antigua, recordar que solo muestra los últimos 60 payloads: reproducir una escritura controlada y revisar inmediatamente. El PCAP/EVE conservan evidencia más amplia. La prueba fue corregida para comprobar una FC06 reciente, no para inventar un paquete.
