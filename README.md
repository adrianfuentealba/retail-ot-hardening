# RETAIL OT — Laboratorio de hardening industrial

> **Estado actual:** perfil ampliado ejecutado y validado en Docker Linux ARM64: 39/39 pruebas de escenarios, 58/58 de observabilidad y 4/4 estáticas. Las cinco estaciones noVNC/osquery están conectadas a Logstash → Elasticsearch → Kibana. Leer `docs/validacion.md` para evidencia, plataforma y límites.

Supermercado 3D persistente, cinco estaciones Linux noVNC con osquery, Elastic Stack con dashboard general y cinco dashboards por endpoint, controlador de refrigeración Modbus/OPC UA y evidencia de red real. Ocho talleres guiados más desafío integrador. Implementación educativa nueva e independiente.

> Uso exclusivamente educativo y defensivo en una máquina aislada y autorizada. No conectar a infraestructura OT, tiendas reales ni Internet como servicio público. Las acciones ofensivas son escenarios controlados con marcadores benignos, procesos sleep y destinos internos fijos. No contiene exploits de firmware, malware operativo, cifrado, escaneo ni exfiltración. No retirar el bind `127.0.0.1` ni montar el socket Docker en contenedores.

## Inicio con un comando

Requisitos: Docker Engine/Desktop con Compose v2 o superior, navegador WebGL y 16 GB de RAM asignada a Docker recomendados; 20 GB libres en disco recomendados para imágenes/volúmenes iniciales. Linux amd64 y ARM64: dependencias osquery fijadas para ambas arquitecturas; las pruebas del autor se detallan en `docs/validacion.md`. Descarga de Docker Hub, Debian/Ubuntu, Elastic y PyPI necesaria en el primer build; paquetes osquery oficiales incluidos; navegador no depende de CDN.

```sh
cd retail-ot-hardening
docker compose up -d
docker compose ps
```

Esperar los indicadores de salud de los servicios para comenzar. `bootstrap` debe terminar con código 0; el resto permanece activo. No confundir bootstrap terminado con servicio caído.

Abrir:

| Acceso | Dirección | Uso |
|---|---|---|
| Portal 3D | http://127.0.0.1:8090 | Talleres, consola, topología, PCAP y Anatomy |
| Kibana | http://127.0.0.1:5601/app/dashboards#/view/retail-overview | Dos gráficos, cuatro fuentes de eventos y cinco dashboards por endpoint |
| TI L4 | http://127.0.0.1:6081/vnc.html?autoconnect=true&resize=remote | ws-corporate |
| Proveedor L3.5 | http://127.0.0.1:6082/vnc.html?autoconnect=true&resize=remote | ws-vendor |
| Ingeniería L3 | http://127.0.0.1:6083/vnc.html?autoconnect=true&resize=remote | ws-engineering |
| HMI L2 | http://127.0.0.1:6084/vnc.html?autoconnect=true&resize=remote | ws-hmi |
| SOC | http://127.0.0.1:6085/vnc.html?autoconnect=true&resize=remote | ws-soc |

noVNC/ELK no tienen autenticación: decisión explícita solo para aula local. No equivale a MFA ni hardening de producción. Un usuario local con acceso a estos puertos puede operar el aula.

## Primera demostración

En portal seleccionar taller 04; ejecutar `simulate defrost` desde ingeniería. Mantener escena visible y observar la temperatura. En Paquetes localizar FC06; en Kibana revisar firma Suricata. Aplicar `harden plc`; repetir la escritura. Comparar excepción Modbus y recuperación de temperatura. Stock ya comprometido queda en cuarentena.

En HMI noVNC abrir Terminal:

```sh
labctl simulate malware
osqueryi --json "SELECT pid,name,cmdline FROM processes WHERE name='sleep' AND cmdline LIKE '%retail-benign-malware%';"
labctl harden application
labctl simulate malware
labctl evidence
```

La segunda ejecución está bloqueada por el guard del agente. El archivo se descarga desde una URL INTERNA del aula, no de Internet. El proceso inicial solo ejecuta sleep 45, no malware. osquery puede observar proceso y archivo independientemente del log del agente.

## Capturas reales

![Supermercado 3D y talleres sin duración sugerida](docs/screenshots/01-supermercado-3d.png)

[Ver galería completa: nueve capturas](docs/galeria.md) del portal, consola, red, paquetes, estaciones, Anatomy, Kibana y escritorio Linux.

## Observabilidad paso a paso

[Guía de cinco estaciones, osquery y Elastic](docs/tutorial-observabilidad.md): comandos de alumno, consultas KQL, bloqueos visibles, permisos Linux, evidencia y solución. En la pestaña **Estaciones** hay enlaces al escritorio, dashboard de cada host y tutorial completo. Importación reproducible en `elastic/retail-dashboards.ndjson`.

## Talleres

**Aprendizaje a tu ritmo:** no se asignan duraciones sugeridas, límites de resolución ni metas de velocidad. La evaluación se basa en objetivos, evidencia y criterios de éxito. Los intervalos técnicos del sistema y plazos normativos no son tiempos de resolución de los alumnos.

01 Inventario; 02 Permisos Linux; 03 HMI y allowlist; 04 Parámetros PLC; 05 Conductos/proveedor; 06 OPC UA; 07 Firmware ficticio; 08 Recuperación; 09 desafío. Todos tienen tutorial, explicación, comandos copiar/pegar y solución en `exercises/`. En portal **Abrir tutorial completo y solución**.

**Escena siempre visible**: panel derecho contextual con pestañas Taller, Consola, Red, Paquetes y Estaciones. En móvil la escena queda fijada arriba y el trabajo debajo. Se identifica pérdida de telemetría; no se genera estado ficticio cuando falta conexión.

## Pruebas y capturas

```sh
python3 scripts/verify-lab.py
python3 scripts/verify-observability.py
bash scripts/baseline-capture.sh
```

La prueba ejecuta escenarios y restablece aula al finalizar: coordinar para no interrumpir un taller. La captura no cambia el proceso; copia el segmento actual, que puede contener tráfico previo de prácticas. Para una línea base pura iniciar el sensor con una captura nueva antes de usar escenarios; no llamar “solo normal” a un PCAP mixto.

## Parada sin perder evidencia

```sh
docker compose down
```

No ejecutar `down -v` salvo decisión consciente de descartar evidencia. El reset del portal conserva eventos/PCAP; `labctl reset` solo afecta el endpoint local. Contenedores y volúmenes ocupan recursos hasta detenerlos.

## Qué es real y qué se simula

Real: XFCE/noVNC, procesos Linux, permisos/propietario de un archivo, osqueryd/osqueryi, Elasticsearch/Logstash/Kibana, Modbus TCP FC03/FC06, OPC UA Write/Read, TLS de OPC UA, captura Ethernet, EVE Suricata.

Simulado: controlador industrial, firmware, térmica acelerada, riesgo de incendio, stock, rol de mantenimiento, guard de ejecución y movimiento lateral por marcadores. Las cinco estaciones son cinco roles/redes, NO cinco tiendas térmicas independientes. Escena representa SCL-01; multitienda se trabaja en ejercicio de mesa. No se implementan DNP3, BACnet, S7, GOOSE, Zeek ni IDS comercial. No se llama firewall transparente a la pasarela Modbus de aplicación.

OPC UA seguro usa una variable read-only y certificado compartido de laboratorio: None continúa accesible internamente y no se declara eliminado. No se obtiene certificación ni SL-A. Ver arquitectura, mapeo y límites.

## Procedencia

Inspirado en el incidente reportado por France 24/Reuters el 12-10-2026. No reproduce vulnerabilidades Danfoss ni atribuye autoría. Anatomy aporta kit MIT para el despiece de controlador; Three.js r180 para escena. Código nuevo; el repositorio de agua anterior se consultó como referencia, no se copió porque su README no declara licencia del código original.

Fuentes y licencias: `docs/fuentes.md`, `THIRD_PARTY_NOTICES.md`. Repositorio público: [vtomasv/retail-ot-hardening](https://github.com/vtomasv/retail-ot-hardening). El laboratorio se ejecuta localmente; no se publica como servicio en Internet.
