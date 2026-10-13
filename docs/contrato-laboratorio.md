# Contrato del laboratorio Retail OT

Repositorio nuevo y local. Perfil ampliado: Linux, cinco noVNC, osquery 5.23.1, Elasticsearch/Logstash/Kibana 8.17.3, Suricata, PCAP, Three.js y kit Anatomy. Ocho talleres más desafío integrador, sin duración sugerida.

## Servicios y zonas

- `panel`: orquestador pedagógico y portal 3D, publicado solo en `127.0.0.1:8090`.
- `ws-corporate`: TI L4, noVNC `127.0.0.1:6081`.
- `ws-vendor`: DMZ L3.5, noVNC `127.0.0.1:6082`.
- `ws-engineering`: ingeniería L3, noVNC `127.0.0.1:6083`.
- `ws-hmi`: supervisión L2, noVNC `127.0.0.1:6084`.
- `ws-soc`: SOC, noVNC `127.0.0.1:6085`.
- `gateway`: pasarela Modbus de aplicación, en supervisión y control; no es firewall transparente ni iptables DPI.
- `plc`: controlador ficticio de refrigeración, red de control, Modbus 502 y OPC UA 4840, sin puertos publicados.
- `sensor`: PCAP y Suricata pasivos en el namespace de red de la pasarela, con privilegios de captura mínimos.
- `collector`: lee volúmenes de evidencia separados en modo lectura y envía JSON a Logstash; no reenvía IP.
- `elasticsearch`, `logstash`, `kibana`: red SOC/telemetría; Kibana solo loopback 5601. Un inicializador instala índice, búsquedas y dashboards.

El panel tiene una red de administración pedagógica fuera de banda para comunicarse con los agentes. Es una excepción de diseño declarada, no un conducto OT de producción. La topología distinguirá red de proceso y administración. Las estaciones no serán routers; la conectividad de datos depende de las redes asignadas, no de etiquetas Purdue.

## Comandos de lista blanca

En cualquier escritorio abra Terminal. `labctl` está en PATH, escribe evidencia local y expone exactamente:

```sh
labctl status
labctl inventory
labctl baseline
labctl simulate defrost
labctl simulate malware
labctl simulate lateral
labctl simulate firmware
labctl simulate opcua
labctl harden os
labctl harden application
labctl harden plc
labctl harden network
labctl harden access
labctl harden opcua
labctl harden supply-chain
labctl detect
labctl recover
labctl reset
labctl evidence
```

No acepta direcciones, scripts arbitrarios ni objetivos externos. La consola web utiliza las mismas acciones permitidas. La ejecución Linux real se realiza dentro del endpoint mediante comandos concretos (chmod, creación de artefactos benignos, procesos de prueba y osquery), no sobre el anfitrión. Los cambios de política PLC/pasarela se ejecutan por API de entrenamiento fija y se verifican por transacciones de protocolo.

`simulate malware` es emulación benigna: descarga local de un marcador de entrenamiento, proceso temporizado y archivo dentro de `/home/student/lab`; no cifra archivos ni explota equipos. `simulate lateral` solicita únicamente dos agentes internos fijos; la prevención es una política de laboratorio, no una prueba de explotación o un firewall del kernel.

## Evidencia

Fuentes diferentes: `lab.endpoint` (acciones Linux), `osquery` (SQL ejecutado por osqueryd), `suricata` (EVE), `lab.control` (políticas/telemetría), PCAP (Ethernet real). El dashboard debe separar fuentes y resultado permitido/bloqueado. Eventos de simulación no se etiquetan como detectados por Suricata u osquery sin evidencia de esas fuentes.

## Criterios de entrega

Un `docker compose up -d` construye e inicia todo. Pruebas: cinco osquery reales, cinco noVNC, eventos indexados de las cinco estaciones, dashboards importados, FC03/FC06 capturados, firma Suricata FC06, efecto térmico y contramedida, controles de archivos comprobables y OPC UA real. Toda limitación o prueba no completada se documenta sin afirmar funcionalidad total.
