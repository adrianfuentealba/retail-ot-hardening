# 01 · Inventario y línea base

> **Borrador local para el laboratorio Retail OT.** Esta guía reemplaza la dependencia de instrucciones del portal: se lee en el Firefox local de la estación y todos los bloques de comandos se ejecutan en la **Terminal del laboratorio** del noVNC indicado. No es un PPTX ni una certificación de seguridad.

## Estación recomendada y forma de trabajo

- **Estación recomendada:** `ws-hmi`.
- **Dónde ejecutar comandos:** escritorio noVNC de `ws-hmi` → Firefox local para esta guía → doble clic en **Terminal del laboratorio**. No usar una shell del anfitrión, una consola web como sustituto, el clipboard del anfitrión ni un pivote entre estaciones.
- **Copiar y pegar:** usar el botón **Copiar** de esta guía y pegar con `Ctrl+Shift+V` en `xfce4-terminal`; como alternativa, seleccionar el comando dentro del Firefox local y usar `Ctrl+C`/`Ctrl+V` dentro de la misma estación. No copiar el `$` del prompt ni una salida JSON como si fuera un comando.
- **Coordinación:** la maqueta es compartida. Una persona opera, otra observa y otra conserva evidencia. No ejecutar dos escenarios simultáneos.
- **Alcance:** los comandos locales (`hostname`, `id`, `labctl status`, `inventory`, `baseline`, `evidence` y las consultas `osqueryi`) observan únicamente la estación cuya Terminal los ejecuta. `labctl classroom-state` observa el gemelo de aula completo. `labctl reset` restablece solo el endpoint actual; `labctl reset-all` es global y requiere coordinación explícita porque afecta a otros alumnos.

## Objetivos medibles

Al terminar, la persona debe poder:

1. Identificar el host y usuario de la Terminal y distinguir el endpoint local del estado global.
2. Inventariar el endpoint observado y corroborar los cinco hosts del aula y sus roles/zona sin confundir una vista de aplicación con un inventario de sistema.
3. Registrar la línea base de `controller.conf`, proceso térmico y políticas antes de cualquier cambio.
4. Identificar tráfico Modbus TCP **FC03** legítimo con una fuente de paquetes/PCAP y conservar una segunda fuente de evidencia.
5. Ejecutar consultas manuales `osqueryi` sobre versión, procesos, usuarios, puertos, permisos y hash, explicando qué significa un resultado vacío.
6. Entregar evidencia con endpoint, hora UTC, fuente, resultado y limitación; no inventar hashes, PID, timestamps ni capturas.

### Mapa pedagógico de hosts

El aula publica cinco hosts fijos. La siguiente es una **asignación de trabajo por nombre**, no una prueba de segmentación de red; el rol que el agente devuelva en `classroom-state` es la fuente para confirmar la sesión:

| Host | Rol/zona pedagógica | Alcance en este taller |
|---|---|---|
| `ws-corporate` | corporativo | inventario global del aula |
| `ws-vendor` | proveedor | inventario global del aula |
| `ws-engineering` | ingeniería | inventario global del aula |
| `ws-hmi` | HMI/operación | estación recomendada y consultas locales |
| `ws-soc` | SOC/observabilidad | inventario global del aula |

## Preparación limpia y segura

### 0. Abrir la guía local y verificar identidad

**Propósito.** Confirmar que las instrucciones se leen localmente y que la sesión corresponde a `ws-hmi` y a un usuario sin privilegios generales.

**Acción exacta — ejecutar cada línea por separado y esperar su respuesta:**

```sh
labctl guides
```

```sh
hostname
```

```sh
id
```

```sh
mkdir -p ~/lab/evidencias/taller-01
```

**Resultado esperado y significado.** `labctl guides` abre la guía HTML local de la estación; no abre la interfaz de evaluación del portal. `hostname` debe identificar la estación recomendada como `ws-hmi` y `id` debe mostrar al usuario de laboratorio (`student`, normalmente UID 1000) sin convertirlo en root. El directorio de evidencia queda dentro de `~/lab/evidencias/taller-01/`, no en el directorio `/evidence` del collector.

**Segunda evidencia:**

```sh
ip -brief address | tee ~/lab/evidencias/taller-01/ip-brief.txt
```

Esto conserva las interfaces de la estación y ayuda a detectar que se está en el noVNC correcto; no es un escaneo ni prueba conectividad con una tienda real.

**Si difiere.** Si el hostname no es `ws-hmi`, detenerse y volver al noVNC recomendado: no compensa cambiar el objetivo en mitad del taller. Si `id` muestra un usuario inesperado o privilegios no previstos, conservar la salida y avisar al responsable; no usar `sudo`, `docker`, `git`, `chmod` ni `iptables` para “arreglarlo”. Si `labctl guides` no abre la guía, continuar solo después de que el padre corrija la implementación del comando local; no volver al portal para sustituirla.

### 1. Comprobar estado local y estado global antes de tocar nada

**Propósito.** Establecer el punto de comparación y detectar una sesión de otra persona antes de un reset.

```sh
labctl status
```

**Resultado esperado y significado.** La respuesta es un objeto de estado local con campos como `host`, `role`, `policies`, `mode` y `osquery`. En una línea base limpia, el host/rol corresponden a `ws-hmi`, `policies` están desactivadas y el modo de `controller.conf` es el vulnerable inicial (semánticamente `0666`). El formato exacto puede variar; no asumir que existe `.event.outcome` en este comando.

**Segunda evidencia:**

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-01/classroom-state-before.json
```

Debe conservar un JSON con `process`, `gateway`, `endpoints`, `policies`, `events`, `history`, `last_update` y `errors`. En una sesión disponible, `endpoints` debe permitir reconocer los cinco hosts fijos: `ws-corporate`, `ws-vendor`, `ws-engineering`, `ws-hmi` y `ws-soc`. La fuente global no sustituye las consultas del endpoint local.

**Si difiere.** Si `errors` contiene `plc unavailable`, `gateway unavailable` o endpoints `unavailable`, registrar el estado y no declarar una línea base completa. Si aparecen políticas o una temperatura alterada, existe estado residual o una sesión concurrente: coordinar antes de resetear. Si `classroom-state` no existe, la estación conserva una imagen anterior: pedir al instructor actualizarla desde el anfitrión siguiendo README; no reemplazarlo con un endpoint inventado.

### 2. Reset global, únicamente coordinado

**Propósito.** Empezar desde un estado de aula reproducible sin borrar evidencia previa.

**Regla.** `reset-all` afecta proceso, gateway, políticas y endpoints de la clase; puede afectar a otros alumnos. Ejecutarlo solo cuando el responsable de la maqueta confirme que no hay otra sesión activa.

```sh
labctl reset-all
```

**Resultado esperado y significado.** La acción informa que el aula fue restablecida. El reset mantiene eventos, logs y PCAP; no es una limpieza forense.

**Segunda evidencia:**

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-01/classroom-state-after-reset.json
```

Comprobar que `process` vuelve al estado nominal (`setpoint` 2, temperatura cercana a 2 °C, `heater=false`, `compressor=true`, sin `spoiled`), que `policies` globales están desactivadas y que los endpoints no conservan políticas locales. La salida concreta y los timestamps son variables y deben conservarse tal como fueron capturados.

**Si difiere.** No repetir el reset a ciegas. Si solo la estación actual quedó alterada, `labctl reset` puede restablecer ese endpoint, pero no corrige PLC, gateway ni otras estaciones. Si el aula no puede ser coordinada, registrar el estado inicial real y marcar el taller como no limpio; no afirmar que se partió de cero. Nunca usar `docker compose down -v`: elimina volúmenes y evidencia. El arranque de Docker, si lo realiza el operador del laboratorio, es una tarea de infraestructura fuera de esta Terminal y no un paso del estudiante.

## Acciones paso a paso

### 3. Inventario del endpoint y anatomía del activo

**Propósito.** Obtener el inventario del sistema observado y conservar la distinción entre datos del backend y un dibujo pedagógico.

La vista gráfica de anatomía es opcional: en el Firefox local, si el panel de aula está disponible, se puede seleccionar `PLC-R01` → **Explorar anatomía** → **Separar componentes** para reconocer CPU, alimentación, interfaces y E/S. El SVG no es evidencia de inventario. La fuente primaria de este paso es `osqueryi` en la estación.

```sh
labctl inventory | tee ~/lab/evidencias/taller-01/inventory-ws-hmi.json
```

**Resultado esperado y significado.** La respuesta de este wrapper tiene `source: "osqueryi"` y `rows` con una fila de `system_info` que incluye `hostname`, `cpu_type` y `physical_memory`. Los valores de CPU y memoria son propios de la imagen y no deben copiarse desde un ejemplo. El resultado demuestra inventario del endpoint actual, no que se hayan inspeccionado mágicamente los otros cuatro.

**Segunda evidencia:**

```sh
labctl classroom-state | jq '{endpoint_hosts:(.endpoints|keys), endpoint_count:(.endpoints|length)}' | tee ~/lab/evidencias/taller-01/hosts-aula.json
```

El resultado esperado es un mapa global con cinco claves de host fijas y `endpoint_count: 5` cuando todos están disponibles. Su significado es “hosts publicados por el gemelo del aula”, no un escaneo de red ni una prueba de que cada host esté sano si su valor contiene `error`.

**Si difiere.** Si `rows` está vacío o `source` no es `osqueryi`, repetir una vez tras comprobar `labctl status`; no fabricar datos. Si el estado global no contiene cinco claves, revisar `errors` y distinguir host ausente de host no observado. Si la anatomía no carga, no usarla como sustituto: conservar la salida de `inventory` y la limitación visual.

### 4. Línea base de archivo y proceso térmico

**Propósito.** Medir los valores iniciales que el taller necesita antes de una contramedida; separar la evidencia del archivo de la evidencia del proceso.

```sh
labctl baseline | tee ~/lab/evidencias/taller-01/baseline-ws-hmi.json
```

**Resultado esperado y significado.** Este comando devuelve un objeto con `rows`, `policies` y un evento de aplicación. En `rows` debe aparecer `/home/student/lab/controller.conf` con el modo inicial semánticamente `0666` y propietario UID de `student` (normalmente 1000). `baseline` no devuelve por sí solo la temperatura ni el estado de deshielo; no interpretar un campo ausente como “deshielo apagado”.

**Segunda evidencia:**

```sh
stat -c 'path=%n mode=%a uid=%u gid=%g user=%U group=%G' /home/student/lab/controller.conf | tee ~/lab/evidencias/taller-01/controller-stat.txt
```

Debe corroborar el modo y propietario del archivo. El modo numérico puede imprimirse sin ceros a la izquierda; el criterio es que sea equivalente a `0666`, no la decoración del texto. La segunda fuente no prueba por sí sola la política del PLC.

Para completar el estado térmico, ejecutar además esta consulta de aula (es una observación global, no una segunda lectura física):

```sh
labctl classroom-state | jq '.process | {temperature,setpoint,heater,compressor,spoiled,thermal_risk,plc_guard}' | tee ~/lab/evidencias/taller-01/process-baseline.json
```

En una línea base limpia se espera `setpoint: 2`, temperatura próxima a `2.0`, `heater: false`, `compressor: true`, `spoiled: false`, `plc_guard: false` y sin riesgo térmico. Es un modelo acelerado de entrenamiento; no calcula salud alimentaria real.

**Si difiere.** Si el modo no es `0666`, la estación conserva hardening o se alteró el archivo: no cambiar permisos manualmente. Coordinar `reset` local o `reset-all` según el alcance y conservar la evidencia previa. Si faltan `process` o hay `errors`, no convertir un estado no observado en un estado seguro. Si la temperatura no es nominal, detener el resto de acciones hasta acordar si se reinicia el aula.

### 5. Tráfico legítimo FC03

**Propósito.** Identificar una lectura Modbus TCP producida por el ciclo legítimo del gateway, sin atribuirla a un ataque.

```sh
labctl evidence | tee ~/lab/evidencias/taller-01/evidence-endpoint.json
```

**Resultado esperado y significado.** La respuesta local contiene `host`, una lista `events` y la ruta `osquery_logs`. Es evidencia de eventos del agente de la estación; **no** es por sí sola un paquete Modbus ni una detección Suricata. Un resultado vacío significa “no observado en esta ventana”, no ausencia absoluta de actividad.

**Segunda evidencia — consultar los paquetes conservados por el panel:**

```sh
curl -fsS http://panel:8000/api/packets | jq '[.[] | select(.protocol=="Modbus TCP" and .function==3)] | .[-5:]' | tee ~/lab/evidencias/taller-01/fc03-packets.json
```

Debe mostrar, si la captura ya está lista, uno o más registros de lectura FC03 y campos de respuesta como protocolo, función, excepción, hex y fuente real de respuesta. `function: 3` significa lectura de registros; `exception: false` indica que esa respuesta no fue una excepción. No llamar “ataque” a este tráfico periódico: es el flujo legítimo del gateway hacia el PLC ficticio.

**Si difiere.** Si la lista es `[]`, revisar `classroom-state.errors`, esperar el ciclo normal del aula y consultar de nuevo; no inventar un paquete. Si hay registros pero no tienen exactamente todos esos campos, conservar el JSON real y describir solo los campos presentes. Si el panel no responde, no sustituirlo por un host o puerto externo. La API de paquetes y el PCAP son fuentes de captura; `lab.endpoint` y `lab.control` son logs de aplicación, no reemplazos independientes de PCAP.

### 6. Consulta de versión del sistema

**Propósito.** Obtener una fuente SQL manual independiente del agente programado.

```sh
osqueryi --json "SELECT name,version,platform FROM os_version;" | tee ~/lab/evidencias/taller-01/os-version.json
```

**Resultado esperado y significado.** Un arreglo JSON con la versión y plataforma del sistema de la estación. Los valores concretos dependen de la imagen y deben capturarse, no predecirse. Es una instantánea manual de `osqueryi`, no una afirmación de que `osqueryd` haya enviado exactamente la misma fila en ese momento.

**Segunda evidencia:**

```sh
labctl status | jq '{host,role,osquery}' | tee ~/lab/evidencias/taller-01/osquery-status.txt
```

El campo `osquery` confirma que el binario local responde y aporta su versión de ejecución. Es corroboración de disponibilidad, no una segunda consulta SQL del mismo contenido.

**Si difiere.** Si `osqueryi` devuelve error, conservar el texto y revisar `labctl status`; no instalar herramientas ni ejecutar con `sudo`. Si devuelve `[]`, significa que la consulta no observó una fila, no que el sistema carezca de versión. Si las versiones difieren, registrar hora y diferencia: una consulta manual y una versión del binario son fuentes con alcances distintos.

### 7. Procesos y consultas programadas

**Propósito.** Saber qué procesos relacionados con el laboratorio están presentes en el instante observado y distinguir una observación manual de un proceso histórico.

```sh
osqueryi --json "SELECT pid,name,path,cmdline FROM processes WHERE cmdline LIKE '%retail-%';" | tee ~/lab/evidencias/taller-01/processes-retail.json
```

**Resultado esperado y significado.** El resultado puede ser un arreglo vacío durante la línea base: significa que no se observó un proceso cuyo `cmdline` coincida en esa instantánea. Si aparecen filas, conservar cada `pid`, `name`, `path` y `cmdline`; ningún PID es permanente.

**Segunda evidencia:**

```sh
{ pgrep -af 'retail-|osqueryd' || true; } | tee ~/lab/evidencias/taller-01/processes-pgrep.txt
```

Esto permite contrastar la instantánea de `osqueryi` con el proceso del agente y los marcadores benignos presentes. La consulta programada de `osqueryd` es otra fuente y puede llegar con latencia de collector/Logstash/Kibana.

**Si difiere.** Un resultado vacío no prueba que no haya existido actividad antes ni que un guard sea antivirus. Si se ve un proceso benigno `retail-benign-malware`, registrar el PID capturado y no inventar otro. Si solo aparece en una fuente, anotar la diferencia de instante y del filtro. No matar procesos manualmente como parte de este taller de inventario.

### 8. Usuarios locales

**Propósito.** Registrar la identidad disponible para operar y evitar atribuir privilegios de una cuenta a otra.

```sh
osqueryi --json "SELECT uid,username,shell FROM users;" | tee ~/lab/evidencias/taller-01/users.json
```

**Resultado esperado y significado.** Un arreglo con los usuarios visibles en el endpoint, sus UID y shells. Se espera poder localizar `student`; la lista completa y sus valores son variables de la imagen y deben conservarse tal cual.

**Segunda evidencia:**

```sh
id student | tee ~/lab/evidencias/taller-01/id-student.txt
```

La salida confirma grupos y UID de la cuenta de laboratorio. Una cuenta listada por `osqueryi` no demuestra que tenga privilegios de root ni autorización sobre otros hosts.

**Si difiere.** Si `student` no existe o su UID no coincide entre fuentes, detenerse y registrar la anomalía. No crear usuarios, cambiar shells ni elevar privilegios. Si la consulta lista más usuarios, no convertir su presencia en un hallazgo de compromiso sin evidencia adicional.

### 9. Puertos en escucha

**Propósito.** Registrar los listeners que el endpoint declara mediante SQL y comprobar que el agente local responde, sin hacer un escaneo.

```sh
osqueryi --json "SELECT pid,port,address,protocol FROM listening_ports;" | tee ~/lab/evidencias/taller-01/listening-ports.json
```

**Resultado esperado y significado.** Un arreglo con los listeners observados por `osqueryi`; `pid`, `port`, `address` y `protocol` identifican cada fila. La presencia de un listener no demuestra que el servicio sea seguro ni que exista exposición fuera de la red de entrenamiento.

**Segunda evidencia:**

```sh
curl -fsS http://127.0.0.1:8010/health | jq '{host,role,mode,policies,osquery}' | tee ~/lab/evidencias/taller-01/agent-health.json
```

Una respuesta HTTP válida demuestra que el agente local atiende en su endpoint pedagógico; es corroboración de servicio, no un inventario completo de puertos. El contenido debe conservarse con los campos que realmente devuelva.

**Si difiere.** Si no hay filas, significa que no se observaron listeners en esa consulta. Si el health local falla, conservar el error y revisar `labctl status`; no usar `nc`, escáneres ni direcciones externas. No concluir que un puerto está “cerrado” solo porque el query llegó vacío.

### 10. Hash de firmware de entrenamiento

**Propósito.** Registrar una huella manual del artefacto educativo antes de cualquier ejercicio de cadena de suministro; esta guía no cambia firmware.

```sh
osqueryi --json "SELECT path,sha256 FROM hash WHERE path='/home/student/lab/firmware.bin';" | tee ~/lab/evidencias/taller-01/firmware-hash-osquery.json
```

**Resultado esperado y significado.** Una fila con la ruta y un `sha256` de 64 caracteres hexadecimales. La huella exacta depende del archivo presente y debe ser la capturada en la sesión; no pegar una huella predeterminada ni confundirla con un PID o timestamp.

**Segunda evidencia:**

```sh
sha256sum /home/student/lab/firmware.bin | tee ~/lab/evidencias/taller-01/firmware-hash-sha256sum.txt
```

El digest de `sha256sum` debe coincidir con el de la fila `osqueryi`; esta coincidencia comprueba el archivo local mediante dos consultas, no una firma de fabricante ni una validación de firmware real.

**Si difiere.** Si la ruta no existe, la consulta queda sin observación y debe registrarse así. Si los digest difieren, no elegir uno: conservar ambas salidas, comprobar que se leyó exactamente `/home/student/lab/firmware.bin` y avisar al responsable. `osqueryd` no monitoriza automáticamente `firmware.bin` solo por aparecer en esta consulta manual; la consulta manual y el log programado son fuentes distintas.

## Verificación opcional en Kibana, sin depender del portal

La resolución del taller no depende de Kibana. Si el observador SOC necesita una comprobación visual, abrir en el Firefox local la instancia interna de Kibana (`kibana:5601`) y usar la data view `retail-ot-*`, ventana **últimos 15 minutos** y refresco de 5 segundos. Copiar KQL, no SQL:

```kql
event.dataset : "osquery" AND host.name : "ws-hmi"
```

```kql
event.dataset : "lab.endpoint" AND host.name : "ws-hmi"
```

```kql
event.dataset : "lab.control"
```

```kql
event.dataset : "suricata" AND event.action : "alert"
```

- `osquery` muestra la telemetría del endpoint; los eventos de configuración pueden incluir `osquery.columns` y `config_integrity`.
- `lab.endpoint` es el log del agente local; `lab.control` puede tener como host `PLC`, `gateway` o el endpoint solicitante, por lo que no se debe filtrar todo por `ws-hmi`.
- Suricata usa el host `sensor` cuando existe una alerta; una consulta vacía es “no observada”.
- Ninguno de esos datasets sustituye el PCAP para demostrar FC03 ni convierte un botón de la interfaz en una aprobación.

Como referencia local opcional, el tutorial de observabilidad puede conservarse sin depender de una ruta relativa del repositorio:

```sh
curl -fsS http://panel:8000/api/tutorial-observability | tee ~/lab/evidencias/taller-01/tutorial-observabilidad.md
```

Si el endpoint no está disponible, no bloquear la resolución: los pasos de esta guía contienen las consultas necesarias.

## Evidencia entregable y cierre

### 11. Descargar el segmento PCAP real

**Propósito.** Conservar el artefacto de red que respalda la lectura FC03, sin escribir datos en `/evidence` del collector.

```sh
curl -fsS -o ~/lab/evidencias/taller-01/retail-ot-live.pcap http://panel:8000/api/capture
```

**Resultado esperado y significado.** Se crea `~/lab/evidencias/taller-01/retail-ot-live.pcap` cuando existe una captura lista. Es el segmento descargable del aula, no una captura de pantalla ni un paquete inventado.

**Segunda evidencia:**

```sh
stat -c 'path=%n size=%s mtime=%y' ~/lab/evidencias/taller-01/retail-ot-live.pcap | tee ~/lab/evidencias/taller-01/pcap-stat.txt
```

El tamaño debe ser mayor que cero y el archivo debe tener una hora de modificación; esos campos prueban que se conservó un archivo, no que cada paquete sea FC03. La identificación de FC03 se hace con `/api/packets` y, si corresponde, el análisis del PCAP por el observador.

**Si difiere.** Un HTTP 404 (`Capture is not yet ready`) significa que la captura aún no está lista; revisar paquetes y repetir después del ciclo legítimo. No crear un archivo vacío con ese nombre ni afirmar que fue descargado.

### 12. Consolidar la última evidencia

**Propósito.** Capturar el estado al cierre y dejar trazabilidad de la ventana de observación.

```sh
date -u +'%Y-%m-%dT%H:%M:%SZ' | tee ~/lab/evidencias/taller-01/closed-at-utc.txt
```

```sh
labctl evidence | tee ~/lab/evidencias/taller-01/evidence-endpoint-final.json
```

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-01/classroom-state-final.json
```

**Resultado esperado y significado.** La carpeta contiene las salidas originales y el momento UTC de cierre. El registro de entrega debe indicar, para cada evidencia, comando, endpoint, hora UTC, resultado (`observado`, `no observado`, `permitido` o `bloqueado`), efecto térmico, fuente y limitación. No usar una captura de pantalla inventada para completar un campo.

**Segunda evidencia:**

```sh
curl -fsS http://panel:8000/api/evidence | jq '{notice,state:(.state | {process,gateway,endpoints,policies,last_update,errors})}' | tee ~/lab/evidencias/taller-01/panel-evidence-final.json
```

Esta consulta del panel ayuda a correlacionar proceso, gateway, endpoints y políticas; sus eventos de aplicación siguen siendo independientes de `osquery`, Suricata y PCAP.

**Si difiere.** Si el estado cambió durante la observación, no sobrescribir los archivos anteriores: registrar la secuencia y la concurrencia. Un evento de `lab.endpoint` o `lab.control` no prueba por sí solo una detección de seguridad. Si faltan fuentes, marcar la limitación y no marcar éxito solo porque un comando terminó con código cero.

Después de revisar y copiar la evidencia, el responsable puede coordinar el reset de aula para la siguiente práctica:

```sh
labctl reset-all
```

No ejecutar este último comando durante la sesión de otro alumno. Si solo se debe abandonar la estación sin reiniciar el aula, no usar `labctl reset` como sustituto de una coordinación global: el reset local no restablece PLC, gateway ni las otras estaciones.

## Solución razonada

La resolución completa es: (1) confirmar `ws-hmi` y usuario, (2) comprobar estado local y global, (3) ejecutar un único `reset-all` coordinado si se requiere línea base limpia, (4) inventariar el endpoint y los cinco hosts publicados, (5) medir permisos del archivo y estado nominal del proceso, (6) separar `labctl evidence` de la evidencia real de FC03 en paquetes/PCAP, (7) contrastar cada consulta manual de `osqueryi` con su segunda fuente y (8) entregar los artefactos sin reemplazar discrepancias por resultados esperados.

La evidencia mínima válida combina fuentes con alcances diferentes:

- `inventory`/`osqueryi`: sistema del endpoint local.
- `baseline` y `stat`: permiso/propietario del archivo local.
- `classroom-state`: gemelo global y estado del proceso, no un segundo sensor físico.
- `/api/packets` y `/api/capture`: tráfico y PCAP de Modbus real del aula.
- `lab.endpoint`/`lab.control`: logs de aplicación, no detecciones independientes de osquery o Suricata.
- `sha256sum` frente a la tabla `hash`: misma huella capturada desde dos caminos locales.

## Criterios de éxito

- Se identifica `ws-hmi`, el usuario de laboratorio y el alcance local/global.
- Se conserva un inventario `osqueryi` del endpoint y el estado global permite identificar los cinco hosts fijos, sin confundir disponibilidad con seguridad.
- Se registran permisos iniciales equivalentes a `0666`, propietario inicial de `student` y una hora UTC.
- Se registra el proceso nominal: consigna 2 °C, temperatura próxima a 2 °C, deshielo/calefacción apagado y compresor activo, con la salvedad de que es un modelo acelerado.
- Existe evidencia de FC03 en `/api/packets` y un PCAP descargable cuando la captura está disponible.
- Se conservan las seis consultas manuales de `osqueryi` y sus comprobaciones secundarias, incluyendo resultados vacíos como **no observado**.
- Las discrepancias, latencias y fuentes faltantes quedan documentadas; no se inventan hashes, PID, timestamps ni capturas.

## Límites, mapeo y uso responsable

Solo usar el aula aislada y autorizada. No conectar a PLC, HMI, RTU, tienda o red productiva. No hay malware operativo, explotación, cifrado, escaneo ni direcciones externas configurables. Los artefactos están bajo `/home/student/lab`. Una emulación de 45 segundos no demuestra una APT.

El hardening que aparece en talleres posteriores es acotado: permisos reales de un archivo Linux, guard de ejecución del agente, validación de consigna en un PLC ficticio, gateway de aplicación y variable OPC UA de solo lectura. Eso no equivale a SELinux/AppArmor, firewall transparente, GPO, protección completa de endpoint, SIS ni certificación IEC 62443. La red de administración pedagógica es una excepción declarada. Este taller tampoco acredita cumplimiento de la Ley 21.663 ni genera notificaciones reales a ANCI; cualquier aplicación en una organización chilena requiere alcance, responsables, evaluación y procedimiento propios.

**MITRE ATT&CK for ICS:** el objetivo es inventario defensivo y observabilidad; no representa una intrusión ni atribuye una técnica ofensiva.

**IEC 62443:** el ejercicio se relaciona pedagógicamente con FR6 y FR7 y con la necesidad de definir SL-T por zona mediante análisis de riesgo. SL-A exige evaluación y evidencia mucho más amplias; no se obtiene por ejecutar comandos o botones.

## Antipatrón contextual y qué hacer el lunes

Ejemplo para discutir en plantas y tiendas chilenas, no una observación atribuida a una organización: acceso compartido del proveedor sin ventana, copia de configuración sin hash y cambios del HMI sin validación del proceso. El lunes: inventariar al dueño del activo, documentar cambio y reversión, probar primero fuera de producción y asignar una ventana con operaciones. No bloquear remotamente una planta sin evaluar la seguridad física.
