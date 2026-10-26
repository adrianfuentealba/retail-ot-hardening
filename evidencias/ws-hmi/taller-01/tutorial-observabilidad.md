# Tutorial de observabilidad: cinco estaciones Linux y Elastic Stack

## Objetivo y criterio de éxito

El alumno debe demostrar una **acción permitida, proceso real observado por osquery, control aplicado y reintento bloqueado**. Debe identificar el endpoint y la ventana temporal en Elasticsearch/Kibana, y distinguir un registro del agente de una observación independiente. El SOC reúne evidencia; no ejecuta SQL mágicamente sobre otros hosts.

> Aula aislada y autorizada. Todos los puertos publicados están en `127.0.0.1`. noVNC y Elastic sin autenticación son una simplificación local, NO una configuración productiva. Los escenarios descargan un archivo de texto interno y ejecutan `sleep 45`; no hay malware operativo, cifrado, exploit, acceso a tiendas reales ni exfiltración.

## 1. Arrancar y asignar roles

En la terminal del anfitrión, dentro del repositorio:

```sh
docker compose up -d
docker compose ps -a
```

Esperar que las cinco estaciones, PLC/gateway/panel, Elasticsearch, Logstash y Kibana estén `healthy`. `bootstrap` debe finalizar `Exited (0)`: importa los dashboards y no es un servicio permanente. Collector/sensor permanecen activos. Si algo falla, revisar:

```sh
docker compose logs --tail=60 ws-hmi logstash collector bootstrap
```

No usar `down -v`, porque descarta evidencia. La primera construcción necesita conexión a registries, Debian, PyPI y Elastic. Los paquetes osquery ARM64/amd64 están incluidos localmente.

Abrir [portal](http://127.0.0.1:8090) → **Estaciones**. Asignar:

| Rol | Endpoint | Escritorio | Dashboard |
|---|---|---|---|
| TI L4 | ws-corporate | http://127.0.0.1:6081/vnc.html?autoconnect=true&resize=remote | http://127.0.0.1:5601/app/dashboards#/view/retail-ws-corporate |
| Proveedor DMZ L3.5 | ws-vendor | http://127.0.0.1:6082/vnc.html?autoconnect=true&resize=remote | http://127.0.0.1:5601/app/dashboards#/view/retail-ws-vendor |
| Ingeniería L3 | ws-engineering | http://127.0.0.1:6083/vnc.html?autoconnect=true&resize=remote | http://127.0.0.1:5601/app/dashboards#/view/retail-ws-engineering |
| HMI L2 | ws-hmi | http://127.0.0.1:6084/vnc.html?autoconnect=true&resize=remote | http://127.0.0.1:5601/app/dashboards#/view/retail-ws-hmi |
| SOC | ws-soc | http://127.0.0.1:6085/vnc.html?autoconnect=true&resize=remote | http://127.0.0.1:5601/app/dashboards#/view/retail-ws-soc |

El dashboard general es [Centro de operaciones](http://127.0.0.1:5601/app/dashboards#/view/retail-overview). Incluye conteos por activo y fuente, y cuatro tablas: endpoint, osquery, proceso/control y alertas Suricata. **Un documento no equivale a un incidente único**. Los cinco dashboards filtran automáticamente por host.

En el portal restablecer aula antes de comenzar; coordinar para no interrumpir a otra cohorte. La escena sigue visible mientras se usan las pestañas o las ventanas noVNC/Kibana.

## 2. Cómo viaja la evidencia

```text
Cinco Linux/XFCE/noVNC
 ├─ labctl → API local → acciones Linux reales y guards de aula
 │                        └─ /evidence/endpoint.jsonl
 └─ osqueryd → SQL local programado → /evidence/osquery/*.log
                      ↓ volúmenes montados read-only
Collector → normalización → TCP JSON lines interno :5044
                      ↓
Logstash → índice retail-ot-AAAA.MM.DD en Elasticsearch
                      ↓
Kibana → dashboard general + cinco dashboards por host

PLC/gateway/panel → sus registros ────────┐
Suricata → EVE y Tshark → PCAP ───────────┘ → Collector
```

No se usa Elastic Agent, Fleet ni Beats: el envío de esta aula se hace por collector propio. TCP 5044 acepta **JSON lines**, no el protocolo Beats. Los flags `--disable_events=true` desactivan publishers de eventos osquery; aquí se usan **tablas consultadas periódicamente**, no auditd/eBPF. Process/download/config cada 5 s, inventory cada 30 s y listeners cada 15 s. El collector recorre fuentes cada 2 s; Kibana refresca cada 5 s. El transporte no tiene ack aplicativo/exactly-once ni custodia forense certificada.

## 3. Preparar la HMI y línea base

En noVNC HMI, abrir **Terminal del laboratorio** con doble clic. Si XFCE pregunta si confiar en un lanzador, leer el nombre y elegir lanzarlo; alternativamente **Applications → Terminal Emulator**. Usar el menú de portapapeles de noVNC para pegar si el navegador captura atajos.

Todos los siguientes comandos se ejecutan **en la terminal de ws-hmi**, salvo que se indique anfitrión.

```sh
whoami
hostname
date -u +%Y-%m-%dT%H:%M:%SZ
labctl status
labctl inventory
```

Esperado: `student`, `ws-hmi`, versión osquery 5.23.1, políticas iniciales `false`. La hora UTC fija la ventana de comparación; Kibana puede presentar hora local.

```sh
osqueryi --json "SELECT hostname,cpu_type FROM system_info;"
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/controller.conf';"
osqueryi --json "SELECT pid,name,cmdline,uid FROM processes WHERE name='sleep' AND cmdline LIKE '%retail-benign-malware%';"
```

La configuración inicial es modo `0666`, propietario estudiante. La consulta de `sleep` puede estar vacía antes del escenario: registrar **no observado en esa consulta**, no “host libre de malware”. Filtrar por `name='sleep'` evita confundir el propio proceso osqueryi con la evidencia buscada.

## 4. Actividad permitida y observación independiente

```sh
labctl simulate malware
```

La respuesta debe indicar `event.action=malware-emulation` y `event.outcome=success`. El agente descarga desde `http://panel:8000/api/training-artifact`, escribe `retail-marker.txt` y crea un proceso benigno de 45 s. **No descargar ni ejecutar archivos de Internet ajenos al aula.**

Ejecutar inmediatamente:

```sh
osqueryi --json "SELECT pid,name,cmdline,uid FROM processes WHERE name='sleep' AND cmdline LIKE '%retail-benign-malware%';"
osqueryi --json "SELECT path,mode,uid,size FROM file WHERE path='/home/student/lab/downloads/retail-marker.txt';"
```

Esperado: nombre `sleep`, cmdline `retail-benign-malware 45`, UID `1000`. El texto se crea por el agente root: no asumir que su propietario es estudiante. Registrar PID y tamaño real, no inventarlos.

En [dashboard HMI](http://127.0.0.1:5601/app/dashboards#/view/retail-ws-hmi), últimos 15 min, refresco 5 s:

- **Acciones Linux:** `malware-emulation`, `success`.
- **osquery:** `processes`, `added`, cmdline del proceso y host HMI.
- **Todos los eventos:** línea temporal del mismo host.

Para búsquedas precisas usar Discover → data view `retail-ot-*`, y pegar **KQL**:

```kql
host.name : "ws-hmi" AND event.dataset : "lab.endpoint" AND event.action : "malware-emulation"
```

```kql
host.name : "ws-hmi" AND event.dataset : "osquery" AND osquery.name : "processes" AND osquery.columns.name : "sleep"
```

```kql
host.name : "ws-hmi" AND event.dataset : "osquery" AND osquery.name : "downloads"
```

Abrir una fila y revisar `_id`, `@timestamp`, `host.name`, `event.dataset`, `osquery.columns`. El agente acredita lo que intentó; osquery acredita lo que vio en Linux. **No son el mismo registro duplicado.** Si el proceso termina antes de observarlo, repetir después de restablecer, documentando el reintento.

## 5. Hardening de aplicación y reintento

```sh
labctl harden application
labctl simulate malware
```

El primer comando activa el guard del agente y termina los procesos benignos que este creó. El segundo todavía descarga texto, pero responde `blocked` y no inicia un nuevo `sleep`.

```sh
osqueryi --json "SELECT pid,name,cmdline FROM processes WHERE name='sleep' AND cmdline LIKE '%retail-benign-malware%';"
```

Esperado: sin proceso lanzado por el escenario. En Kibana buscar:

```kql
host.name : "ws-hmi" AND event.dataset : "lab.endpoint" AND event.outcome : "blocked"
```

La política **no es antivirus ni allowlisting global del kernel**. Un usuario puede ejecutar otros comandos Linux: no afirmar que se bloquea toda ejecución maliciosa del sistema. El control limita el lanzador del ejercicio. La evidencia osquery del proceso puede mostrar `removed` en el siguiente ciclo.

## 6. Hardening de permisos y evidencia diferencial

```sh
labctl harden os
stat -c '%a:%U:%G' /home/student/lab/controller.conf
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/controller.conf';"
```

Esperado: `640:root:student`, UID `0`, GID del grupo estudiante. Prueba real como alumno:

```sh
printf 'student-write-test\n' >> /home/student/lab/controller.conf
```

Esperado: **Permission denied**; no modifica archivo. El alumno conserva lectura por grupo, pero pierde escritura. El agente root sigue pudiendo aplicar los cambios de aula; no equivale a SELinux/AppArmor ni separación completa de funciones.

En Kibana:

```kql
host.name : "ws-hmi" AND event.dataset : "osquery" AND osquery.name : "config_integrity"
```

Comparar filas `added/removed`, `osquery.columns.mode`, UID y SHA256. Cambiar permisos no necesariamente cambia hash del contenido. Esta distinción es parte de la evaluación.

## 7. Proveedor y marcadores laterales

En portal restablecer aula, guardar antes la evidencia. En terminal noVNC **ws-vendor**:

```sh
labctl simulate lateral
```

Esperado: dos resultados `success`, destinos fijos `ws-engineering` y `ws-hmi`. Los destinos crean `lateral-marker.txt`, no se explotan credenciales ni servicios.

En dashboard general/Discover:

```kql
event.dataset : "lab.endpoint" AND event.action : "lateral"
```

```kql
event.dataset : "osquery" AND osquery.name : "downloads" AND osquery.columns.path : "/home/student/lab/downloads/lateral-marker.txt"
```

En la misma terminal proveedor:

```sh
labctl harden network
labctl simulate lateral
```

Esperado: ambos destinos `blocked`. La pasarela también rechaza FC06 y mantiene FC03. **El guard lateral actúa en las APIs de los agentes por la red training; no prueba filtrado kernel entre todas las zonas Purdue.**

## 8. Repetir por los cinco endpoints

Restablecer aula una sola vez antes de esta ronda. Repetir secciones 3–5 en cada estación, dejando registro del host y hora. Usar su dashboard correspondiente. En el general, el gráfico “Eventos por activo” debe incluir los cinco nombres; el conteo cambia continuamente y no es un criterio fijo.

La prueba automática secuencial desde anfitrión cubre esta ronda y valida además WebSocket→RFB real y eventos nuevos por host:

```sh
python3 scripts/verify-observability.py
```

No ejecutar junto a otro taller ni con `verify-lab.py` simultáneo: ambas restablecen estado. Resultados detallados en `docs/observability-verification-results.json`. La latencia medida es acción→documentos visibles por consulta ES, **no SLA, ni MTTD, ni latencia visual completa de Kibana**. Añadir hasta el próximo refresco de la UI.

## 9. Evidencia y resolución

En cada estación:

```sh
labctl evidence
```

Desde anfitrión, guardar expediente local del aula:

```sh
mkdir -p evidence
curl -fsS http://127.0.0.1:8090/api/evidence -o evidence/panel.json
docker compose exec -T ws-hmi cat /evidence/endpoint.jsonl > evidence/ws-hmi-endpoint.jsonl
docker compose exec -T ws-hmi cat /evidence/osquery/osqueryd.results.log > evidence/ws-hmi-osquery.jsonl
bash scripts/baseline-capture.sh
```

`api/evidence` no exporta todos los logs Linux/Elastic por sí solo. PCAP de red no prueba un permiso de archivo local. Para concluir cada control presentar al menos **dos fuentes apropiadas**, con comando, host, hora UTC, `_id` del evento, resultado y límite. El reset conserva registros y marcadores: no elimina evidencias históricas del dashboard.

### Rúbrica (10 puntos)

| Criterio | Puntos |
|---|---|
| Identifica las cinco estaciones y fuentes | 2 |
| Correlaciona agente + proceso osquery real por host/hora | 2 |
| Demuestra ejecución bloqueada y proceso ausente tras control | 2 |
| Verifica `0640 root` y escritura denegada como estudiante | 2 |
| Entrega expediente, latencia y límites correctamente | 2 |

**Solución:** seguir secciones 3→4→5→6; luego 7 y repetir 3→5 para los demás endpoints. Resultado correcto no consiste en que el botón cambie a verde, sino en la comparación de evidencias. Para errores: verificar host, tiempo, política, disponibilidad y logs en ese orden. No reducir controles ni exponer puertos para solucionar una búsqueda vacía.

## Referencias de control

IEC 62443 FR2/FR3: control de uso e integridad; FR5: conductos acotados; FR6: evidencia/respuesta; FR7: continuidad. Referencias pedagógicas, no cumplimiento de cada SR ni SL-A certificado. MITRE ICS T0836/T0831 se usa en las escrituras/efectos de proceso de los talleres 04/06; los procesos benignos y marcadores laterales no demuestran una APT. Ley 21.663: preservar la evidencia para evaluar significancia y preparar el borrador de aula; no enviar notificaciones reales. Ver `respuesta-chile.md` para sujeto obligado, RACI y plazos.
