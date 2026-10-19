# 08 · Contención y recuperación

> **Estación recomendada:** `ws-hmi`. Todos los bloques de esta guía se ejecutan en la **Terminal del laboratorio** del escritorio noVNC de `ws-hmi`, no en la consola web, no en el anfitrión y no en una estación distinta. Mantenga esta guía abierta en el Firefox local de la estación con `labctl guides`.
>
> El escenario es un laboratorio aislado y autorizado. Las acciones son simulaciones educativas con destinos internos fijos; no se deben conectar a PLC, HMI, RTU, tiendas o redes reales.

## Objetivos medibles

Al finalizar, el estudiante debe poder demostrar, con salidas reales y sin inventar valores:

1. Reproducir de forma benigna un incidente de proceso y distinguir su respuesta Modbus de la evolución del estado térmico.
2. Observar un marcador y un proceso benignos de endpoint sin confundirlos con malware operativo.
3. Ejecutar la recuperación central, verificar el retorno de la consigna nominal y comprobar la contención de procesos registrados.
4. Conservar eventos, estado, respuesta de protocolo y captura disponible en un expediente local.
5. Preparar un borrador de notificación con hora de conocimiento, fuentes, limitaciones y una evaluación explícita —no una conclusión automática— de la aplicabilidad de la Ley 21.663.

**Criterio de éxito:** la recuperación devuelve la consigna hacia `2 °C`, apaga el calefactor, detiene los procesos benignos registrados y conserva el estado de stock ya comprometido en cuarentena. Un `reset-all` posterior puede limpiar el aula para otra práctica; no es recuperación real de producto.

## Antes de empezar: alcance, roles y límites

- Designe operador de proceso, observador SOC y responsable de evidencia. La maqueta es compartida por la cohorte: anuncie cada escenario y no ejecute dos escenarios simultáneos.
- Use el usuario de la estación que ya está preparado para el laboratorio. `student` no tiene sudo general; no use `sudo`, `docker`, `git`, cambios de firewall ni herramientas de pentest.
- El comando opera en la estación donde está la Terminal. Estar viendo una guía en otro escritorio no mueve el rol ni el origen del tráfico.
- `ws-hmi` es el origen recomendado. `labctl simulate malware` es local a ese endpoint; `labctl simulate defrost` y `labctl recover` pasan por el panel y afectan al proceso del aula; `labctl recover` también solicita contención a los cinco endpoints. `labctl evidence` presenta evidencia del endpoint actual y `labctl classroom-state` consulta el gemelo del aula.
- `labctl reset` solo restablece las políticas y procesos del **endpoint actual**. No sustituye a `labctl reset-all`, no restablece PLC/gateway/otras estaciones y no restaura por sí solo un firmware.
- `labctl reset-all` es global y coordinado: afecta a otros alumnos, mantiene la evidencia y lo implementa el padre según el contrato común. No se ejecuta mientras otra sesión esté activa.
- No copie el signo `$` del prompt ni pegues salidas JSON en la shell. En noVNC, copie desde el botón de la guía y pegue con `Ctrl+Shift+V` en la Terminal; no use el portapapeles del anfitrión ni un pivote.
- Los valores dinámicos —PID, hash, timestamps, hexadecimales y contenidos de captura— deben ser los devueltos por la ejecución. Esta guía no proporciona valores capturados de ejemplo.

## 0. Preparación coordinada y línea base

### 0.1 Abrir la guía local

**Propósito.** Trabajar sin volver al portal por instrucciones y confirmar que el comando nuevo abre la guía HTML local de la estación.

**Acción exacta** — desde la Terminal del laboratorio:

```sh
labctl guides
```

**Resultado esperado y significado.** Firefox muestra el índice o la guía local del laboratorio. Esto no abre una consola ni cambia de estación.

**Segunda evidencia.** En la misma Terminal, conserve la identidad de la estación con:

```sh
hostname
```

El resultado debe identificar la estación recomendada `ws-hmi` o el nombre que el instructor haya asignado explícitamente. La guía debe seguir ejecutándose en esa estación.

**Si difiere.** Si `labctl guides` no existe, abre una página del portal o no muestra una guía local, no sustituya el procedimiento con instrucciones del portal: conserve el mensaje, informe al responsable del aula y use solo la guía local ya provisionada cuando el comando sea corregido. Si `hostname` no corresponde a `ws-hmi`, cambie al noVNC recomendado antes de generar evidencia.

### 0.2 Identidad y alcance de la sesión

**Propósito.** Registrar quién ejecuta y en qué endpoint, antes de cambiar el estado.

**Acciones exactas:**

```sh
id
```

```sh
labctl status
```

**Resultado esperado y significado.** `id` muestra el usuario de la estación, normalmente `student`, sin conceder privilegios adicionales. `labctl status` imprime JSON del agente local con campos como `host`, `role`, `policies`, `mode` y estado de `osquery`; el objeto es la fuente del endpoint actual, no el estado global del aula.

**Segunda evidencia.** Compare `hostname` e identidad con `host`/`role` de `labctl status`. No asuma que el campo `host` tiene un valor fijo si el despliegue lo ha parametrizado.

**Si difiere.** Si el usuario no es el asignado, el rol no es HMI o el endpoint está no disponible, detenga la práctica. No intente corregirlo con sudo, Docker o cambios de red. Un `status` local correcto tampoco demuestra que PLC, gateway y las demás estaciones estén disponibles.

### 0.3 Restablecimiento de aula (solo tras coordinar)

**Propósito.** Empezar con proceso, gateway, políticas y endpoints en una condición conocida sin borrar la evidencia histórica.

**Precondición.** El operador debe confirmar que no hay otra práctica activa. Anote esa coordinación en la evidencia; `reset-all` afecta a toda la clase.

**Acciones exactas:**

```sh
labctl reset-all
```

```sh
labctl classroom-state
```

**Resultado esperado y significado.** `reset-all` devuelve un resultado de operación global. La consulta `classroom-state` devuelve el JSON de solo lectura de `/api/state`, con `process`, `gateway`, `endpoints`, `policies`, `events`, `history`, `last_update` y `errors`. Tras una limpieza, las políticas deben aparecer desactivadas, el proceso debe estar en su condición nominal y los endpoints deben ser comprobables; los eventos históricos se conservan.

La rehabilitación de stock que pudiera acompañar a un reinicio del aula es una operación administrativa del laboratorio, no una recuperación de inocuidad ni una reversión de un incidente real.

**Segunda evidencia.** Guarde el estado inicial en el expediente local:

```sh
mkdir -p ~/lab/evidencias/taller-08
```

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-08/estado-inicial.json
```

**Si difiere.** Si existe `errors`, un endpoint figura `unavailable`, el proceso no es legible o una política sigue activa, no marque la línea base como limpia. Coordine otra limpieza global o detenga la práctica; no intente reemplazar `reset-all` con `labctl reset`.

### 0.4 Línea base del endpoint

**Propósito.** Registrar host, inventario y el permiso inicial que luego permitirá separar evidencia de endpoint y evidencia de proceso.

**Acciones exactas:**

```sh
labctl inventory | tee ~/lab/evidencias/taller-08/inventario-inicial.json
```

```sh
labctl baseline | tee ~/lab/evidencias/taller-08/baseline-inicial.json
```

**Resultado esperado y significado.** `inventory` devuelve un objeto cuya fuente es `osqueryi` y una lista `rows` de `system_info`. `baseline` devuelve `{event,rows,policies}`: `rows` consulta `controller.conf` y, en una línea base vulnerable limpia, el modo esperado es `0666`; el propietario corresponde al usuario del laboratorio. No invente el valor numérico de `uid`.

El modo `0666` es una condición pedagógica vulnerable, no un certificado de seguridad. El estado global del proceso debe verificarse en `classroom-state`, no inferirse de `baseline`.

**Segunda evidencia.** Compruebe el archivo directamente, sin alterar permisos:

```sh
stat -c '%n mode=%a uid=%u gid=%g' /home/student/lab/controller.conf
```

**Si difiere.** Compare el `mode` de `stat` con `rows`. Si no es `0666` después de un `reset-all`, conserve ambas salidas y no fuerce el modo con `chmod`; la inconsistencia debe diagnosticarse. Un resultado vacío de osquery es **no observado**, no ausencia absoluta.

## 1. Incidente de proceso: deshielo benigno

**Propósito.** Reproducir la escritura fija de proceso y separar el evento de protocolo de sus efectos térmicos. El comando usa el destino interno predefinido y una escritura Modbus TCP FC06; no acepta IP, puerto ni payload libre.

**Antes.** En una línea base sin una barrera previa, el controlador ficticio acepta una consigna de aula alta; no hay que confundir esa aceptación con una vulnerabilidad demostrada en un PLC real.

**Acción exacta:**

```sh
labctl simulate defrost
```

**Resultado esperado y significado.** La respuesta normal es un objeto con `event` y `packet` (no un objeto que necesariamente tenga `event.outcome` en la raíz). En `event` se esperan `event.dataset: "lab.control"`, `event.action: "defrost"`, `host.name` del solicitante y un `event.outcome` real que debe leerse, no suponerse. En `packet` se esperan `protocol: "Modbus TCP"`, `function: 6`, `source: "actual TCP response"` y el indicador booleano `exception`. La salida de `success` significa que la escritura fija fue aceptada por el escenario; `blocked` significa que una barrera ya la rechazó. El campo hexadecimal es variable y debe conservarse tal cual.

Si la escritura fue aceptada, el estado del proceso debe mostrar la consigna de aula elevada y el calefactor activado; la temperatura puede tardar ciclos del simulador en reflejar la perturbación. El modelo no calcula termodinámica ni inocuidad alimentaria real.

**Segunda evidencia:**

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-08/estado-deshielo.json
```

Para una segunda fuente del tráfico, conserve los paquetes que el panel tenga disponibles:

```sh
curl -sS http://panel:8000/api/packets | tee ~/lab/evidencias/taller-08/paquetes-deshielo.json
```

Compare `process.setpoint`, `process.heater`, `process.temperature`, `process.exposure`, `process.spoiled` y `process.thermal_risk` con el `event`/`packet`. `/api/packets` y el `packet` de la acción son evidencias de tráfico; `classroom-state` es evidencia del estado del proceso. No confunda el log de aplicación con Suricata o osquery.

**Si difiere.**

- Si el resultado ya es `blocked`, no hay un incidente reproducido en esta ejecución: una política global puede haber quedado activa. Guarde la salida, coordine una nueva línea base y repita solo después de `reset-all` autorizado.
- Si el evento dice `success` pero el proceso no cambia, conserve ambas fuentes y vuelva a consultar `classroom-state`; una respuesta de protocolo no demuestra por sí sola que la temperatura haya cambiado.
- Si aparecen `errors`, `gateway unavailable` o una captura vacía, no convierta la ausencia de datos en una afirmación de ausencia de actividad. El taller queda pendiente de diagnóstico.
- Si la temperatura tarda en cambiar, siga la evolución del estado sin prometer un tiempo de resolución ni usar una cifra inventada.

## 2. Actividad de endpoint: marcador benigno

**Propósito.** Observar la descarga de un marcador educativo y el proceso temporal local, manteniéndolos separados del incidente de proceso. No es malware operativo: no cifra, no roba credenciales y no permite cambiar el objetivo.

**Acción exacta:**

```sh
labctl simulate malware
```

**Resultado esperado y significado.** Esta acción devuelve directamente un evento de endpoint, no necesariamente `{event: ...}`. En el evento deben leerse `host.name` de la estación actual, `event.dataset: "lab.endpoint"`, `event.action: "malware-emulation"`, `event.outcome` y un mensaje que distinga `BENIGN`, el marcador descargado y el `sleep` temporal. Sin una política local `os` o `application`, el resultado usual del escenario es `success` y se registra un proceso con nombre de entrenamiento. Con una barrera local ya activa, el resultado puede ser `blocked`; ese bloqueo es un guard de ejecución local, no un antivirus global.

**Segunda evidencia:** comprobar el endpoint de forma independiente mientras el proceso temporal siga presente:

```sh
osqueryi --json "SELECT pid,name,path,cmdline FROM processes WHERE cmdline LIKE '%retail-%';"
```

```sh
pgrep -af retail-benign-malware || true
```

La primera consulta es una lectura manual de `osqueryi`; la segunda es una observación directa de procesos. El PID, si aparece, es el que debe registrarse: la guía no fija ningún PID. El archivo de entrenamiento queda bajo `/home/student/lab/downloads/retail-marker.txt`; el hecho de que exista no prueba ejecución.

**Si difiere.**

- Un resultado vacío puede significar que el `sleep` temporal ya terminó; no significa que el proceso nunca existió ni que fue bloqueado. Coordine con el operador y ejecute `labctl simulate malware` otra vez; consulte inmediatamente con `osqueryi` y `pgrep`.
- Si la acción dice `blocked`, guarde el evento y revise `labctl status` para saber si `os` o `application` ya estaban activos. El guard mata procesos benignos registrados, pero no demuestra protección endpoint completa.
- Si `osqueryi` falla o el endpoint está no disponible, no sustituya la evidencia por una captura de pantalla ni por un PID supuesto. Conserve el error y marque la observación como no realizada.

## 3. Contención y recuperación central

**Propósito.** Recuperar el proceso y contener los procesos benignos registrados en los endpoints, sin presentar la acción como hardening preventivo o restauración de datos.

**Acción exacta:**

```sh
labctl recover
```

**Resultado esperado y significado.** La respuesta normal es un evento directo con `event.dataset: "lab.control"`, `event.action: "recover"`, `event.outcome: "success"` y un mensaje de refrigeración reanudada, procesos benignos detenidos y stock comprometido en cuarentena. El controlador ficticio vuelve hacia `setpoint: 2`, mantiene `heater: false` y deja que la temperatura tienda a la referencia nominal. La marca de stock ya comprometido no se borra: `recover` no restaura backups, no revierte exposición y no libera producto.

`recover` solicita la contención de cada uno de los cinco agentes. Que el evento central diga `success` no elimina la obligación de revisar la disponibilidad de cada endpoint.

**Segunda evidencia:**

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-08/estado-post-recuperacion.json
```

```sh
pgrep -af retail-benign-malware || true
```

En `classroom-state`, compruebe `process.setpoint`, `process.heater`, la tendencia de `process.temperature`, el indicador de stock (`spoiled`/cuarentena), `endpoints` y `errors`. En el endpoint HMI, `pgrep` debe quedar vacío después de la contención; si el proceso ya había terminado, ese vacío solo demuestra que no está presente ahora. Verifique que los eventos de deshielo y endpoint sigan en `events` o en el expediente; no use la ausencia del proceso como sustituto.

**Si difiere.**

- Si la consigna no retorna hacia `2` o el calefactor permanece activo, conserve la respuesta y el estado, vuelva a consultar una vez y trate el resultado como divergencia del modelo, no como éxito.
- Si algún elemento de `endpoints` tiene `error` o `unavailable`, no declare contención completa de cinco estaciones. Registre el host afectado y coordine con el responsable.
- Si `spoiled` pasa a falso después de un `recover`, el resultado no demuestra recuperación sanitaria; revise si se ejecutó un reinicio de aula u otra acción y preserve la secuencia real.
- `recover` no activa `harden plc`, `harden network`, `harden access`, una política de endpoint ni un control de OPC UA. Una repetición del ataque puede seguir siendo posible; eso es una limitación conocida, no una razón para modificar el código.

## 4. Evidencia local, fuentes independientes y borrador de notificación

### 4.1 Expediente de comandos y estado

**Propósito.** Crear el expediente en la ruta exigida, conservando salidas reales antes de una eventual limpieza global.

**Acciones exactas:**

```sh
labctl evidence | tee ~/lab/evidencias/taller-08/evidencia-endpoint.json
```

```sh
curl -sS http://panel:8000/api/evidence | tee ~/lab/evidencias/taller-08/evidencia-panel.json
```

```sh
curl -sS http://panel:8000/api/packets | tee ~/lab/evidencias/taller-08/paquetes-finales.json
```

**Resultado esperado y significado.** `labctl evidence` devuelve `host`, una lista `events` de los últimos eventos locales y la referencia `osquery_logs` del collector. `curl /api/evidence` devuelve `state` y advierte que los eventos de aplicación son independientes de osquery, Suricata y PCAP. `curl /api/packets` devuelve los paquetes de Modbus disponibles o una lista vacía si no se ha producido/recogido captura.

Las copias se guardan en `~/lab/evidencias/taller-08/`, no en `/evidence`. La ruta `/evidence/osquery/osqueryd.results.log` que pueda aparecer en la salida pertenece al collector: solo se lee como referencia. No se redireccionan datos al almacenamiento del collector.

**Segunda evidencia.** Si el panel informa que existe una captura, descárguela en el expediente local:

```sh
curl -fsS http://panel:8000/api/capture -o ~/lab/evidencias/taller-08/retail-ot-live.pcap
```

Un archivo PCAP descargado es una segunda fuente para el tráfico, no para la temperatura. El estado del proceso se prueba con `classroom-state` y el endpoint con osquery/eventos.

**Si difiere.** Un `404` de `/api/capture` significa que la captura todavía no está disponible; conserve el mensaje y no cree un PCAP vacío ni invente paquetes. Si el JSON de evidencia no contiene el evento esperado, compare el timestamp de la ejecución y la ventana de consulta; no marque éxito por haber pulsado un botón.

### 4.2 Plantilla de reporte sin datos inventados

**Propósito.** Dejar un borrador que el responsable pueda completar con la hora real de conocimiento, evidencia y aplicabilidad normativa. No se envía ninguna notificación a ANCI desde este laboratorio.

**Acción exacta:**

```sh
cat > ~/lab/evidencias/taller-08/notificacion-borrador.md <<'EOF'
# Borrador de notificación · Taller 08

- Hora UTC de conocimiento: [completar con el @timestamp real de la primera evidencia]
- Responsable que conoce el evento: [completar]
- Activo/zona: Retail OT educativo; origen observado: [host real]
- Descripción: [separar deshielo/FC06 de marcador de endpoint]
- Contención ejecutada: `labctl recover`; resultado real: [completar]
- Estado del proceso posterior: [copiar campos reales de estado-post-recuperacion.json]
- Estado de stock: [cuarentena; no afirmar rehabilitación]
- Fuentes: [evidencia-endpoint.json, evidencia-panel.json, paquetes-finales.json, PCAP si existe, consultas osquery]
- Limitaciones: [modelo acelerado; no es PLC/SIS productivo; no es cálculo de inocuidad]
- Ley 21.663: [evaluar aplicabilidad con el responsable competente; no marcar reportable/no reportable por el solo resultado del laboratorio]
- Comunicación: [no enviado; borrador de entrenamiento]

## Criterio de cierre

[Comparar dos fuentes y anotar cualquier divergencia; no completar PID, hash, hora o impacto con valores supuestos.]
EOF
```

**Resultado esperado y significado.** Se crea un borrador local con campos explícitos para hora de conocimiento, impacto, contención, evidencia, limitaciones y aplicabilidad legal. La Ley 21.663 se conserva como pregunta de aplicabilidad; esta maqueta no decide por sí sola una obligación de notificar.

**Segunda evidencia.** Compare el borrador con `labctl evidence` y `classroom-state`; cada afirmación debe poder rastrearse a un archivo o a una salida real. No copie un PID, hash, timestamp o resultado de ejemplo desde esta guía.

**Si difiere.** Si el archivo no se puede crear, conserve el error y no lo escriba en `/evidence`; asegure que existe `~/lab/evidencias/taller-08/`. Si falta la hora exacta, use el `@timestamp` real del evento conservado, no la hora actual como sustituto sin explicarlo.

## 5. Consultas Linux/osquery de verificación

Estas consultas se ejecutan en la Terminal de **la estación observada**. `osqueryi` consulta el endpoint local; `osqueryd` de los cinco endpoints ejecuta sus propias consultas programadas y envía sus resultados al collector. Una consulta manual no inspecciona mágicamente otro contenedor.

### 5.1 Sistema, procesos, usuarios y listeners

**Propósito.** Obtener observaciones endpoint independientes de los eventos de aplicación.

**Acciones exactas:**

```sh
osqueryi --json "SELECT name,version,platform FROM os_version;"
```

```sh
osqueryi --json "SELECT pid,name,path,cmdline FROM processes WHERE cmdline LIKE '%retail-%';"
```

```sh
osqueryi --json "SELECT uid,username,shell FROM users;"
```

```sh
osqueryi --json "SELECT pid,port,address,protocol FROM listening_ports;"
```

**Resultado esperado y significado.** Cada comando imprime JSON de la tabla consultada. El resultado de `processes` puede estar vacío porque el `sleep` es temporal; se registra como **no observado**, no como ausencia absoluta. No se espera un PID predeterminado. `users` y `listening_ports` describen el endpoint actual, no el aula completa.

**Segunda evidencia.** Compare procesos con `pgrep -af retail-benign-malware || true` y compare host/rol con `labctl status`. Para el proceso global, use `classroom-state`; no extrapole una fila local a las cinco estaciones.

**Si difiere.** Un resultado vacío, una tabla no disponible o un error de osquery se conserva literalmente. No vuelva a ejecutar hasta obtener el resultado deseado sin registrar el primer resultado.

### 5.2 Archivo de control y firmware educativo

**Propósito.** Mantener las comprobaciones manuales originales, con la distinción entre permisos y hash manual. Este taller no altera el firmware.

**Acciones exactas:**

```sh
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/controller.conf';"
```

```sh
osqueryi --json "SELECT path,sha256 FROM hash WHERE path='/home/student/lab/firmware.bin';"
```

**Resultado esperado y significado.** La consulta `file` muestra el modo y propietario actuales; la línea base vulnerable usa `0666`. La consulta `hash` devuelve el hash **real de esta ejecución** y sirve como evidencia manual. No hay que inventar ni comparar contra un hash escrito en la guía. El schedule de osquery no incluye `firmware.bin` de forma predeterminada; esta consulta manual no prueba que `osqueryd` lo monitorice.

**Segunda evidencia.** Para `controller.conf`, use `stat -c '%n mode=%a uid=%u gid=%g' ...` y compare. Para firmware, conserve la consulta y el timestamp de la ejecución; no convierta el hash en detección de Suricata.

**Si difiere.** Si el modo no coincide, revise la secuencia de reset/hardening real. Si el hash está vacío, marque el archivo no observado. No aplique `harden supply-chain` ni `reset` dentro de este taller para fabricar una comparación; esas acciones pertenecen a la práctica de firmware y además `reset` es local.

### 5.3 Consulta programada y Kibana opcional

El intervalo programado de osquery para cambios de procesos/archivos es de aproximadamente 5 s, más la latencia del collector, Logstash y refresco de Kibana. No se debe prometer un tiempo de resolución ni asumir que un evento aparecerá inmediatamente.

Si el observador necesita una segunda vista visual, puede usar el Firefox local de la misma estación y Kibana interno, sin volver al portal para instrucciones. En Discover, data view `retail-ot-*`, ventana de últimos 15 minutos y refresco de 5 s, use KQL (no SQL):

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

`lab.control` puede tener `host.name` de PLC, gateway o endpoint solicitante; no filtre todo por HMI. Suricata suele usar el host `sensor`. Los eventos `lab.endpoint` y `lab.control` son logs de aplicación, no detecciones independientes de osquery o Suricata. Una vista vacía es no observada en esa ventana.

## 6. Antes/después: qué controla realmente cada barrera

| Situación | Antes | Después de la acción de este taller | Lo que **no** demuestra |
|---|---|---|---|
| Deshielo fijo | La línea base permite observar la escritura del escenario si no hay una política previa | `recover` devuelve la consigna nominal y detiene la respuesta de calefacción; la evidencia queda | No demuestra hardening permanente de PLC, gateway o red; no calcula inocuidad |
| Marcador de endpoint | `simulate malware` descarga un marcador y puede crear un `sleep` de 45 s | `recover` solicita `contain` y detiene procesos registrados; el evento permanece | No es antivirus global ni prueba que un proceso ya terminado nunca existiera |
| Evidencia | Eventos de aplicación, estado y paquetes se generan por fuentes distintas | Se copian a `~/lab/evidencias/taller-08/` y se dejan limitaciones explícitas | Guardar un JSON no valida por sí solo la conclusión |
| Reinicio de aula | El escenario queda sucio para la siguiente práctica | `reset-all` limpia políticas/proceso y mantiene evidencia, tras coordinación | No es recuperación de producto ni una liberación operacional real |

La contención central no restaura backups ni vuelve sano el stock. El guard de malware benigno no es antivirus global. `harden os`, `harden application`, `harden network`, `harden access`, `harden plc`, `harden opcua` y `harden supply-chain` son barreras acotadas de otras prácticas; no deben darse por aplicadas porque se haya ejecutado `recover`.

## 7. Criterios de solución razonada

La secuencia completa es:

1. Abrir la guía local y confirmar host/usuario.
2. Coordinar y ejecutar `reset-all`; guardar `classroom-state`, inventario y línea base.
3. Ejecutar el deshielo fijo; conservar la respuesta `{event,packet}` y comprobar el proceso con `classroom-state` y paquetes.
4. Ejecutar el marcador benigno; comprobar el proceso temporal con osquery/`pgrep` y conservar el evento de endpoint.
5. Ejecutar `recover`; comprobar proceso, endpoints, stock en cuarentena y ausencia actual del proceso local sin inventar una ausencia histórica.
6. Exportar la evidencia al expediente local y preparar el borrador legal sin enviarlo.
7. Coordinar el cierre y ejecutar `reset-all` solo cuando la cohorte lo autorice.

Se cumplen los criterios cuando:

- el proceso está de vuelta hacia `2 °C` y el calefactor está apagado;
- los eventos de deshielo y endpoint siguen conservados;
- el stock que el escenario haya marcado como comprometido sigue en cuarentena hasta una decisión operacional independiente;
- el expediente contiene dos fuentes apropiadas para cada afirmación (protocolo/PCAP para control, estado para proceso, permisos/SQL para endpoint, EVE para firmas si existe);
- el borrador registra hora de conocimiento, aplicabilidad y limitaciones sin inventar datos.

## 8. Cierre coordinado

**Propósito.** Dejar el aula lista para otra práctica sin destruir evidencia.

**Precondición.** Confirme con operador, observador y cohorte que no hay otra sesión activa. Si no hay coordinación, no ejecute el comando global.

**Acciones exactas:**

```sh
labctl reset-all
```

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-08/estado-cierre-reset-all.json
```

```sh
labctl evidence | tee ~/lab/evidencias/taller-08/evidencia-despues-del-reset.json
```

**Resultado esperado y significado.** El estado de cierre muestra políticas globales y de endpoints desactivadas y el proceso limpio para aula; `events`/`history` y el expediente local siguen disponibles. El reset global puede rehabilitar el stock solo como operación de preparación del laboratorio. La evidencia `despues-del-reset` debe permitir comprobar que los eventos históricos no fueron borrados.

**Segunda evidencia.** Compare `estado-cierre-reset-all.json` con `estado-inicial.json` y `evidencia-despues-del-reset.json` con `evidencia-endpoint.json`. El primero demuestra limpieza; los segundos demuestran conservación.

**Si difiere.** Si `reset-all` no está disponible, no lo sustituya con `labctl reset` y no ejecute comandos de Docker. Deje la evidencia intacta y comunique la falta de implementación. Si otro alumno comenzó una sesión, detenga el cierre global y coordine antes de continuar.

No ejecute `docker compose down -v`: elimina volúmenes y evidencia. Un `docker compose down` tampoco forma parte de las acciones de la Terminal del laboratorio de esta guía.

## Mapeo normativo y uso responsable

- **MITRE ATT&CK for ICS:** T0836/T0831 para la perturbación del proceso y la respuesta defensiva en el escenario educativo. El mapeo no convierte la simulación en una intrusión real.
- **IEC 62443:** FR6 y FR7 como requisitos fundacionales y diseño pedagógico. El SL-T se define mediante el análisis de riesgo de cada zona; SL-A requiere evaluación y evidencia más amplias. Siete botones o una recuperación no otorgan certificación ni un nivel de seguridad.
- **Ley 21.663:** el expediente debe registrar hora de conocimiento, activo, impacto observado, contención, fuentes y limitaciones para que el responsable competente evalúe aplicabilidad. Esta guía no declara por sí sola un incidente reportable, no envía información a ANCI y no reemplaza el procedimiento legal u organizacional.

El controlador es código Python ficticio de aula, no lógica de PLC/SIS productivo. El hardening pedagógico acotado no equivale a SELinux/AppArmor, firewall transparente, GPO, protección endpoint completa, SIS ni certificación IEC 62443. La red administrativa del laboratorio permite acciones fuera de banda y es una excepción declarada.

## Antipatrón contextual y qué hacer el lunes

Caso de discusión —no observación atribuida a una organización—: acceso compartido de proveedor sin ventana, copia de configuración sin hash y cambios de HMI sin validación del proceso. En una planta o tienda real: identificar al dueño del activo, documentar cambio y reversión, probar primero fuera de producción y asignar una ventana con operaciones. No bloquear remotamente una planta sin evaluar la seguridad física.

## Delimitación con desafío 09 y Módulo 10

Este documento resuelve el taller 08 y no acredita los módulos de pruebas integradoras. La entrega conjunta debe mantener estas separaciones:

- **Desafío 09:** documentar por separado los hosts involucrados y cada uno de sus **siete controles**; un `reset` en HMI no equivale a hardening de ingeniería y una salida del panel no debe atribuirse automáticamente a todos los hosts.
- **Módulo 10:** documentar individualmente sus **seis prácticas**; no marcar ninguna de ellas como realizada por haber ejecutado la recuperación de este taller.

No ejecutar comandos Red/Purple Team dentro de este taller para “completar” esas prácticas. Sus respuestas Modbus/OPC UA, hosts, controles y evidencias deben permanecer en sus guías correspondientes.

## Solución y limitaciones finales

La solución válida es la secuencia de esta guía y la comparación honesta de sus fuentes. Si una salida difiere, se conserva el error y se consulta el diagnóstico local del laboratorio; nunca se reemplaza evidencia por el resultado esperado. Un `sleep` de 45 s es temporal; una consulta vacía posterior no prueba bloqueo. Un hash o PID solo se registra si aparece en la ejecución real. La maqueta no calcula salud alimentaria real con sus ticks de simulador y no permite extrapolar los resultados a una organización, tienda o PLC productivo.

Como apoyo local, consulte `docs/operacion-y-diagnostico.md` si está disponible en el paquete de la estación y `docs/tutorial-observabilidad.md` para la conexión, búsquedas KQL y separación de fuentes. Son referencias de diagnóstico/observabilidad, no instrucciones para ejecutar pruebas automáticas en paralelo con este taller.
