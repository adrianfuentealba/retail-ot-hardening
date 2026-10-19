# 06 · OPC UA: canal seguro y permisos

> **Borrador local del laboratorio Retail OT.** Esta guía es autocontenida: las instrucciones se ejecutan desde la **Terminal del laboratorio** dentro del noVNC recomendado y las comprobaciones visuales son opcionales en el Firefox local. No hace falta volver al portal para saber qué comando ejecutar.

## Portada y alcance

**Estación recomendada:** `ws-engineering`.

**Dónde se ejecuta cada bloque:** todos los bloques de shell se copian en la Terminal del laboratorio de `ws-engineering`. No se usa la consola web del portal como shell, no se cambia de host para “probar de nuevo” y no se usa el terminal del anfitrión. Si es necesario comprobar Kibana, se hace en la misma sesión de Firefox del noVNC; no es una fuente alternativa de comandos.

**Objetivos medibles**

- Distinguir **cifrado del canal** de **autorización de la variable**.
- Comprobar una escritura OPC UA real, inicialmente permitida, sobre `ns=2;s=Setpoint`.
- Aplicar la política del taller: el cliente posterior usa `Basic256Sha256/SignAndEncrypt` y la variable queda de solo lectura.
- Comprobar que el `Read` seguro sigue funcionando y que el `Write` posterior es rechazado sin cambiar la consigna.
- No afirmar que el endpoint `None` fue retirado: en este taller continúa disponible internamente. La retirada de `None`, los usuarios OPC UA/RBAC y el usuario `engineer` pertenecen al **módulo 10**, no se deben simular aquí.

**Criterio de éxito del taller:** escritura inicial permitida; lectura posterior con `security: "SignAndEncrypt"`; escritura posterior con resultado `blocked`; valor leído de vuelta sin cambio; evidencia conservada con host y hora. Los timestamps, temperaturas, contadores y valores `before`/`readback` son capturados en la sesión y no se deben reemplazar por números inventados.

## Mapa técnico que se va a observar

- Cliente didáctico: `labctl simulate opcua` desde el agente de la estación.
- Ruta OPC UA fija: `opc.tcp://gateway:4840/retail/`.
- Nodo objetivo: `ns=2;s=Setpoint`.
- Antes del hardening, el servidor acepta el `Write` de `50.0` en el modelo ficticio.
- Después de `harden opcua`, el cliente configura `Basic256Sha256` con `SignAndEncrypt`; el servidor mantiene la variable de solo lectura. El `Read` ocurre antes del intento de escritura, por lo que una respuesta con `readback` demuestra lectura, no permiso de escritura.
- `labctl simulate opcua` retorna una estructura distinta de `labctl harden opcua`: para la simulación, el resultado suele tener el evento en `.event.event.outcome`; para el hardening, el evento puede estar en `.event.outcome`. No asumir una ruta común ni inventar campos.

La barrera de este taller controla **el permiso de escritura de esa variable y la seguridad que configura el cliente**. No implementa PKI empresarial, MFA, RBAC de usuarios, firewall transparente, TLS de Modbus ni una certificación de seguridad. El gateway solo hace túnel del tráfico OPC UA; su política TLS de Modbus no forma parte de esta práctica.

## Preparación coordinada

Antes de comenzar, asignar operador/ingeniería, observador SOC y responsable de evidencia. La maqueta es compartida: no ejecutar otro escenario simultáneamente. `labctl reset-all` afecta al proceso, políticas y endpoints de las cinco estaciones; **solo se ejecuta después de coordinarlo con los demás alumnos**. Conserva la evidencia existente.

### Paso 0.1 — Confirmar host y usuario

**Propósito:** demostrar que los comandos se ejecutarán en el endpoint previsto y con el usuario de laboratorio, no en el anfitrión ni en otra estación.

**Acción exacta:**

```sh
hostname
```

**Resultado esperado y significado:** se identifica la estación actual; para este taller debe ser `ws-engineering` (la representación puede variar según el sistema). El siguiente comando confirma el usuario:

```sh
id
```

Debe mostrar el usuario de estudiante del laboratorio, normalmente `student`, sin exigir UID/PID inventados. `student` no tiene sudo general.

**Segunda evidencia:** comparar el host obtenido con `host`/`role` de `labctl status` y con `host.name`/`role` de los eventos de las respuestas del taller.

**Si difiere:** detenerse. Cambiar a la pestaña noVNC de `ws-engineering` y abrir allí **Terminal del laboratorio**. No usar un pivote, el portapapeles del anfitrión ni comandos Docker/Git/sudo para compensarlo.

### Paso 0.2 — Abrir la guía local, no instrucciones del portal

**Propósito:** verificar que se usa la copia HTML/Markdown local provista para la estación.

**Acción exacta:**

```sh
labctl guides
```

**Resultado esperado y significado:** el comando abre o presenta la guía local de la estación; no es la interfaz del portal. La salida concreta depende de la implementación de `guides` del aula.

**Segunda evidencia:** comprobar en Firefox que la página corresponde al taller 06 y que la URL es local de la guía, no una página externa.

**Si difiere:** no buscar instrucciones en Internet ni en el portal. Conservar la salida y avisar al facilitador: la estación podría conservar una imagen anterior. Solicitar actualización desde el anfitrión siguiendo README.

### Paso 0.3 — Ver el gemelo antes de resetear

**Propósito:** obtener una lectura de solo consulta del proceso, gateway, endpoints, políticas y eventos recientes antes de modificar el aula.

**Acción exacta:**

```sh
labctl classroom-state
```

**Resultado esperado y significado:** JSON de solo lectura equivalente a `/api/state`, con claves como `process`, `gateway`, `endpoints`, `policies`, `events`, `history`, `last_update` y `errors`. Sirve para saber si hay otro escenario activo; no es por sí mismo una prueba de un paquete OPC UA.

**Segunda evidencia:** la persona observadora puede mirar el mismo estado en el Firefox local, pero se conserva como evidencia primaria el JSON de la Terminal. `classroom-state` no debe mutar el aula.

**Si difiere:** si `errors` informa PLC, gateway o endpoints no disponibles, no deducir que una barrera funcionó. Conservar el JSON y resolver la disponibilidad con el facilitador antes de continuar.

### Paso 0.4 — Restablecer el aula completo, con coordinación

**Propósito:** obtener una línea base limpia para proceso, PLC, gateway y las cinco estaciones. `labctl reset` no es equivalente: solo restablece el endpoint actual.

**Acción exacta:**

```sh
labctl reset-all
```

**Resultado esperado y significado:** evento de reset de aula con proceso y políticas globales restablecidos; la evidencia histórica no se borra. El evento global debe acreditarse con una consulta posterior de `classroom-state`. Este comando puede interrumpir el trabajo de otros alumnos.

**Segunda evidencia:** volver a leer el estado:

```sh
labctl classroom-state
```

Tras el reset, el estado debe mostrar el PLC en su línea nominal, políticas de este escenario desactivadas y endpoints disponibles. No se requiere que todos los campos aparezcan instantáneamente; un `errors` no vacío es una discrepancia a diagnosticar, no un éxito.

**Si difiere:** no sustituirlo por cinco `labctl reset` ni continuar con una línea base desconocida. Coordinar el aula, guardar las dos salidas y repetir el reset-all solo cuando no haya una sesión concurrente.

### Paso 0.5 — Capturar identidad, estado e inventario de línea base

**Propósito:** dejar evidencia reproducible del host, agente y permisos locales antes de la primera escritura.

**Acción exacta, un bloque por comando:**

```sh
labctl status
```

```sh
labctl inventory
```

```sh
labctl baseline
```

**Resultado esperado y significado:**

- `status` devuelve la salud del agente, el host/rol, las políticas locales y la modalidad del archivo de configuración; no es un certificado de seguridad.
- `inventory` devuelve JSON de `osqueryi` con filas de inventario local.
- `baseline` devuelve una consulta manual de `controller.conf` y el estado local. En una línea base limpia el archivo educativo suele ser escribible por `student` (`0666` y propietario de estudiante); confirmar los campos reales, sin copiar un UID o modo no observado.

Los wrappers no son uniformes: algunas acciones retornan una fila de evento, otras `{event, ...}`. Leer los campos presentes en cada respuesta.

**Segunda evidencia:** guardar los tres resultados junto con `hostname` e `id` en `~/lab/evidencias/taller-06/` cuando se cree esa carpeta en el paso de evidencia. Para el proceso/PLC usar además `labctl classroom-state`; no confundir `baseline` del endpoint con una lectura del PLC.

**Si difiere:** si aparecen políticas OPC UA activas antes de la prueba, si el host no es `ws-engineering` o si el endpoint no responde, no ejecutar la escritura inicial. Registrar la salida y coordinar un nuevo `reset-all`.

## Acciones OPC UA

### Paso 1 — Probar el `Write` inicial con `None`

**Propósito:** reproducir de forma benigna el riesgo de una escritura OPC UA sin canal seguro ni autorización de solo lectura. Es una demostración controlada de **MITRE ATT&CK for ICS T0836 Modify Parameter**, no una intrusión ni una prueba contra un equipo real.

**Preparación de evidencia:**

```sh
mkdir -p ~/lab/evidencias/taller-06
```

**Acción exacta:**

```sh
labctl simulate opcua | tee ~/lab/evidencias/taller-06/01-opcua-none.json
```

**Resultado esperado y significado:** en una línea base limpia, la respuesta debe indicar:

- `security` igual a `"None"`;
- `event.event.action` igual a `"opcua-write"`;
- `event.event.outcome` igual a `"success"`;
- `readback` igual a `50.0` (o el formato numérico equivalente), porque la escritura sobre `ns=2;s=Setpoint` fue aceptada;
- `before` es el valor capturado antes de escribir y no se debe inventar. Tras un reset limpio normalmente representa la consigna nominal del modelo, pero solo la salida real es evidencia.

La respuesta combina el `Read` previo, el `Write` real y la lectura de vuelta. `success` aquí significa que el servidor aceptó la escritura; no significa que exista un canal confidencial ni que se haya demostrado seguridad física.

**Segunda evidencia:** consultar el gemelo sin mutarlo:

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-06/01-classroom-state.json
```

En el objeto `process`, `setpoint` debe reflejar la nueva consigna del modelo y `opcua_secure` aún debe estar desactivado. El evento más reciente debe corresponder a `opcua-write`. Esta segunda fuente es el estado/evento de aplicación; la evidencia primaria de aceptación sigue siendo la respuesta OPC UA del comando.

**Si difiere:**

- Si el resultado ya es `blocked`, `security` ya es `SignAndEncrypt` o el estado muestra políticas activas, la línea base no estaba limpia: conservar ambas salidas y coordinar `reset-all`.
- Si hay `OPC UA error`, endpoint no disponible o `process` nulo, no convertir un fallo de infraestructura en un bloqueo de seguridad; revisar `errors` y detenerse.
- Si `event.event.outcome` es `success` pero `readback` no refleja el valor solicitado, conservar la respuesta completa y revisar el estado del PLC; no repetir a ciegas.

### Paso 2 — Aplicar la barrera de variable de solo lectura

**Propósito:** activar la protección específica de OPC UA del taller. Esta acción no habilita RBAC de usuarios ni retira automáticamente el endpoint `None`.

**Acción exacta:**

```sh
labctl harden opcua | tee ~/lab/evidencias/taller-06/02-harden-opcua.json
```

**Resultado esperado y significado:** respuesta de evento de aplicación con `event.action: "harden-opcua"` y `event.outcome: "success"` cuando la política del PLC se aplicó. En esta acción el evento puede estar en la raíz, por lo que no se debe buscar `.event.event.outcome` por costumbre.

**Segunda evidencia:**

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-06/02-classroom-state.json
```

En `process` verificar `opcua_secure: true`. `opcua_tls_only` no debe interpretarse como true por este taller: `None` sigue siendo una opción interna. El estado también permite comprobar que el proceso sigue siendo el mismo y que no se cambió de host.

**Si difiere:**

- Si el evento no es exitoso o `opcua_secure` no cambia, guardar la salida, comprobar que se está en `ws-engineering` y que el PLC está disponible; no pasar al criterio final.
- Si el estado indica `opcua_tls_only: true` sin haber ejecutado el módulo 10, registrar la condición como estado heredado o reset incompleto; no presentarla como resultado de este paso.
- Si el comando aparece como no permitido, no usar `harden opcua-rbac` o `harden opcua-channel` como sustituto: son controles del módulo 10.

### Paso 3 — Repetir la operación: `Read` seguro y `Write` rechazado

**Propósito:** repetir el mismo objetivo sin cambiar estación ni nodo y separar dos afirmaciones: la lectura funciona mediante un canal configurado por el cliente, mientras la escritura es rechazada por autorización de la variable.

**Acción exacta:**

```sh
labctl simulate opcua | tee ~/lab/evidencias/taller-06/03-opcua-secure-readonly.json
```

Ejecutar cuando `classroom-state` refleje la política aplicada; no medir ni reportar el tiempo de transición como resultado del laboratorio.

**Resultado esperado y significado:**

- `security` igual a `"SignAndEncrypt"`;
- `event.event.action` igual a `"opcua-write"`;
- `event.event.outcome` igual a `"blocked"`;
- `before` y `readback` permanecen iguales a la consigna vigente, sin mutación por el intento de escritura;
- la presencia de `before` y `readback` demuestra que el `Read` fue posible; `blocked` corresponde al `Write` posterior.

El cliente usa el certificado fijado del laboratorio para esta conexión. Eso demuestra la configuración de esta prueba, no una PKI empresarial ni la identidad de una persona.

**Segunda evidencia:**

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-06/03-classroom-state.json
```

Comparar `process.setpoint` con el `readback` de la respuesta. En `events` debe quedar un evento `opcua-write` bloqueado. `lab.control` y `classroom-state` son fuentes de aplicación; deben acompañar, no reemplazar, la respuesta real del cliente OPC UA.

**Si difiere:**

- Si `security` sigue siendo `None`, revisar `process.opcua_secure` y el host. No afirmar que el canal es seguro.
- Si el servidor rechaza la conexión por no encontrar un endpoint `None`, eso no es el resultado esperado de este taller: probablemente quedó aplicado el control `opcua-channel` del módulo 10 o faltó resetear el aula. Guardar la salida y diagnosticar el estado.
- Si el resultado sigue siendo `success`, la variable no quedó protegida o otro actor cambió el estado; conservar ambas respuestas y no marcar éxito.
- Si hay un error de preparación (`opcua_ready` falso, PLC/gateway no disponible), registrar el estado y repetir solo después de que el estado del aula confirme disponibilidad. No cambiar de estación ni transformar un error de transporte en `blocked`.
- Si `readback` cambia después de un `blocked`, la barrera no está demostrada; detenerse y conservar la evidencia completa.

## Verificación independiente del endpoint con osquery

Estas consultas se ejecutan en la Terminal de **`ws-engineering`** y solo leen ese endpoint. `osqueryi` manual no es `osqueryd`: las consultas programadas de `osqueryd` llegan a ELK por separado. Un arreglo JSON vacío significa **no observado en esa consulta**, no ausencia absoluta de actividad. Los PID, timestamps, hashes y filas pueden variar; no rellenarlos con valores de ejemplo.

### Paso 4.1 — Versión local de osquery

**Propósito:** confirmar que las siguientes consultas se ejecutan con el recolector local autorizado.

```sh
osqueryi --json "SELECT name,version,platform FROM os_version;" | tee ~/lab/evidencias/taller-06/04-os-version.json
```

**Resultado esperado y significado:** uno o más objetos JSON con nombre, versión y plataforma del sistema local. Es una evidencia de endpoint, no de cifrado OPC UA.

**Segunda evidencia:** el campo `osquery` de `labctl status` y el host del propio comando deben corresponder a `ws-engineering`.

**Si difiere:** si el comando no existe o retorna error, guardar la salida y no sustituirla por una consulta ejecutada en otra estación. Si retorna `[]`, registrar “no observado”.

### Paso 4.2 — Procesos del ejercicio

**Propósito:** comprobar si el endpoint tiene procesos cuyo `cmdline` contenga el marcador educativo `retail-`.

```sh
osqueryi --json "SELECT pid,name,path,cmdline FROM processes WHERE cmdline LIKE '%retail-%';" | tee ~/lab/evidencias/taller-06/05-processes-retail.json
```

**Resultado esperado y significado:** JSON con las filas que existan en el instante de consulta; en este taller OPC UA normalmente no se espera un proceso educativo de larga duración. No se espera ni se inventa un PID. La ausencia de filas solo significa “no observado ahora”.

**Segunda evidencia:** `labctl classroom-state` y `labctl evidence` muestran eventos del agente, pero no reemplazan la consulta local de procesos.

**Si difiere:** si aparece un proceso, conservar PID y comando tal como fueron capturados y no matarlo manualmente. `harden application` no es parte de este taller; cualquier contención debe coordinarse con el facilitador.

### Paso 4.3 — Usuarios locales

**Propósito:** documentar la identidad local sin confundir usuario Linux con identidad OPC UA.

```sh
osqueryi --json "SELECT uid,username,shell FROM users;" | tee ~/lab/evidencias/taller-06/06-users.json
```

**Resultado esperado y significado:** filas de usuarios locales y sus shells. Esto no demuestra RBAC OPC UA, MFA ni autorización de la variable.

**Segunda evidencia:** comparar el usuario activo de `id` con la fila correspondiente, sin exigir una fila concreta que no haya sido observada.

**Si difiere:** si `student` no aparece o la consulta falla, guardar el JSON y tratarlo como discrepancia del endpoint; no usar usuarios del portal como sustituto.

### Paso 4.4 — Puertos que escucha el endpoint

**Propósito:** identificar listeners locales sin hacer escaneo ni afirmar que un puerto prueba una política OPC UA.

```sh
osqueryi --json "SELECT pid,port,address,protocol FROM listening_ports;" | tee ~/lab/evidencias/taller-06/07-listeners.json
```

**Resultado esperado y significado:** filas locales de puertos, direcciones y protocolos. La salida es inventario del endpoint y no acredita que el túnel `gateway:4840` esté cifrado.

**Segunda evidencia:** el campo `gateway`/`endpoints` de `labctl classroom-state` permite observar disponibilidad del gemelo; no debe confundirse con esta lista de sockets locales.

**Si difiere:** si no hay filas, registrar “no observado”; si aparece un listener inesperado, no cerrarlo ni cambiar firewall. Coordinar diagnóstico.

### Paso 4.5 — Permisos del archivo de configuración local

**Propósito:** recordar el límite de alcance: este taller no aplica `harden os`; los permisos Linux son una evidencia de endpoint independiente del permiso OPC UA.

```sh
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/controller.conf';" | tee ~/lab/evidencias/taller-06/08-controller-conf.json
```

**Resultado esperado y significado:** en la línea base limpia, la fila suele reflejar modo `0666` y propietario de estudiante; la representación exacta del modo y los IDs se toma de la salida real. Este archivo no es el certificado OPC UA ni el nodo `Setpoint`.

**Segunda evidencia:** `labctl baseline` consulta el mismo archivo y permite comparar el resultado manual con `osqueryi`. Las dos consultas siguen siendo evidencia del endpoint, no de la red.

**Si difiere:** no ejecutar `sudo chmod` ni convertir este taller en hardening de sistema operativo. Guardar la diferencia y, si se necesita restaurar la línea base, coordinar `reset-all`.

### Paso 4.6 — Hash manual del firmware educativo

**Propósito:** conservar la consulta original de integridad como evidencia manual, dejando claro que no forma parte de la barrera OPC UA.

```sh
osqueryi --json "SELECT path,sha256 FROM hash WHERE path='/home/student/lab/firmware.bin';" | tee ~/lab/evidencias/taller-06/09-firmware-hash.json
```

**Resultado esperado y significado:** una fila con el hash que exista en ese instante, sin publicar ni inventar un valor literal. En este taller no se ejecuta `simulate firmware`; el hash no prueba el canal OPC UA.

**Segunda evidencia:** la consulta manual es independiente de las consultas programadas de `osqueryd`; el schedule de osquery no incluye `firmware.bin` por defecto. Si se necesitara probar cadena de suministro, se haría en su taller con `simulate firmware` y `harden supply-chain`.

**Si difiere:** una lista vacía es “no observado”, no “firmware seguro”. No modificar el archivo ni atribuir un hash a una captura que no existe.

## Observabilidad local opcional

La terminal y el Firefox del noVNC son dos vistas del mismo laboratorio. La observabilidad visual no sustituye las respuestas guardadas de la Terminal. Si se usa Kibana local, seleccionar el data view `retail-ot-*`, una ventana de últimos 15 minutos y refresco de 5 segundos. Copiar **KQL**, no SQL.

### Paso 5.1 — Consultas osquery por estación

En Discover ejecutar:

```kql
event.dataset : "osquery" AND host.name : "ws-engineering"
```

**Resultado esperado y significado:** eventos osqueryd del endpoint `ws-engineering`, incluidos los campos `osquery.columns` y, para integridad, el nombre `config_integrity` cuando corresponda. No se espera que este filtro muestre automáticamente la consulta manual de `osqueryi`.

**Segunda evidencia:** los JSON guardados en `04-os-version.json` a `09-firmware-hash.json` son la fuente directa de cada consulta manual.

**Si difiere:** si no aparece el evento, no inventar latencia ni timestamp. Conservar la consulta local; la ausencia en Kibana no invalida ni confirma por sí sola el resultado.

### Paso 5.2 — Eventos del endpoint

```kql
event.dataset : "lab.endpoint" AND host.name : "ws-engineering"
```

**Resultado esperado y significado:** eventos producidos por políticas o simulaciones locales del agente. La simulación OPC UA se registra principalmente como `lab.control`, por lo que este filtro puede no mostrar el `opcua-write`.

**Segunda evidencia:** `labctl status`, `labctl evidence` y `labctl classroom-state` muestran la fuente local/aplicación.

**Si difiere:** no buscar el evento bajo HMI ni cambiar el host del filtro. Registrar que el dataset esperado para la acción fue `lab.control`.

### Paso 5.3 — Eventos de control OPC UA

```kql
event.dataset : "lab.control"
```

**Resultado esperado y significado:** eventos `harden-opcua` y `opcua-write`, con `event.outcome` aplanado en Kibana: primero `success`, después `blocked`, y con el host de la estación solicitante o la fuente que corresponda. La vista es un log de aplicación y no una detección independiente de Suricata.

**Segunda evidencia:** comparar `event.outcome`, `event.action` y timestamp con los JSON de los pasos 1–3 y con `classroom-state`.

**Si difiere:** conservar la salida de la Terminal como fuente del protocolo. Un filtro vacío no autoriza a repetir una escritura fuera de la secuencia ni a marcarla como bloqueada.

### Paso 5.4 — Alertas Suricata, solo como contexto

```kql
event.dataset : "suricata" AND event.action : "alert"
```

**Resultado esperado y significado:** puede no haber una alerta para esta operación de aplicación permitida/bloqueada. Suricata usa el host `sensor`; no se debe filtrar todo por `ws-engineering` ni tratar la ausencia de alerta como prueba de cifrado o autorización.

**Segunda evidencia:** la respuesta real de `labctl simulate opcua` y el estado del PLC son las fuentes relevantes para este taller.

**Si difiere:** si aparece una alerta, conservarla y describirla sin atribuirle un significado que el campo no indique. Si no aparece, no convertirlo en fallo del ejercicio.

## Evidencia y cierre

### Paso 6.1 — Exportar el resumen del agente

**Propósito:** conservar eventos recientes del endpoint sin escribir en el directorio interno del collector.

```sh
labctl evidence | tee ~/lab/evidencias/taller-06/10-labctl-evidence.json
```

**Resultado esperado y significado:** JSON con el host, eventos recientes y la referencia del log de osquery. La referencia `/evidence/osquery/osqueryd.results.log` es del collector y se lee según permisos; no se debe redireccionar allí.

**Segunda evidencia:** `~/lab/evidencias/taller-06/01-opcua-none.json`, `02-harden-opcua.json`, `03-opcua-secure-readonly.json` y los tres estados de aula vinculan cada resultado con su acción.

**Si difiere:** conservar la salida aunque haya menos eventos de los esperados; `labctl evidence` no crea detecciones de osquery o Suricata retroactivamente.

### Paso 6.2 — Guardar una copia final del estado de aula

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-06/11-classroom-state-final.json
```

**Resultado esperado y significado:** snapshot JSON con proceso, gateway, endpoints, políticas y eventos. Es una segunda fuente de aplicación para comprobar que la consigna no cambió tras el rechazo.

**Segunda evidencia:** comparar `process.setpoint` con `readback` del paso 3 y conservar cualquier diferencia, incluidos `errors`.

**Si difiere:** no editar el JSON ni rellenar valores faltantes; la discrepancia debe quedar explícita en el informe.

### Paso 6.3 — PCAP opcional, sin atribución automática

Si el facilitador solicita el segmento real, descargarlo desde el endpoint fijo del panel a la carpeta de evidencias. No se debe interpretar un archivo descargado como prueba de contenido hasta inspeccionarlo.

```sh
curl -f http://panel:8000/api/capture -o ~/lab/evidencias/taller-06/retail-ot-live.pcap
```

**Resultado esperado y significado:** archivo PCAP real si la captura está preparada. El endpoint puede responder que aún no está listo; eso no cambia el resultado del protocolo guardado en la Terminal. No usar `/api/capture` para fabricar un paquete ni reemplazar los JSON.

**Segunda evidencia:** para este taller, cotejar la ventana de captura y el evento `lab.control` en Kibana. `/api/packets` y `/api/capture` son ayudas de captura del panel, especialmente útiles para Modbus; no afirmar que un segmento contiene una trama OPC UA concreta sin inspección.

**Si difiere:** conservar el error HTTP y continuar con las fuentes primarias disponibles. No descargar desde una URL externa ni usar una herramienta de escaneo.

### Paso 6.4 — Restablecer para la siguiente práctica

**Propósito:** devolver proceso y políticas a la línea base sin eliminar evidencia. Es una operación de aula que afecta a otros alumnos.

**Acción exacta, solo tras coordinar con operador, SOC y responsable de evidencia:**

```sh
labctl reset-all | tee ~/lab/evidencias/taller-06/12-reset-all-cierre.json
```

Verificar:

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-06/13-classroom-state-after-reset.json
```

**Resultado esperado y significado:** proceso y endpoints vuelven a la línea base, las políticas se limpian y los archivos de evidencia permanecen. `labctl reset` por sí solo no restablece PLC/gateway/otras estaciones. No ejecutar `docker compose down -v`, porque elimina volúmenes y evidencia.

**Segunda evidencia:** `13-classroom-state-after-reset.json` y un `labctl status` final muestran el estado de aula después de la operación coordinada.

**Si difiere:** no repetir resets mientras haya otra sesión. Guardar las salidas y escalar la discrepancia al facilitador.

## Diagnóstico compacto de salidas

- **Host incorrecto:** cambiar de pestaña noVNC a `ws-engineering`; no cambiar la ruta OPC UA ni usar otro objetivo.
- **`labctl` no reconoce `classroom-state`, `reset-all` o `guides`:** la estación conserva una imagen anterior; solicitar al instructor actualizarla desde el anfitrión siguiendo README. No sustituirlos con Docker, Git o llamadas externas.
- **`labctl simulate opcua` devuelve `success` después del hardening:** la variable no quedó de solo lectura, o se perdió el estado entre acciones; conservar los JSON y no marcar éxito.
- **`security: "None"` después del hardening:** no hay demostración de canal seguro. Comprobar `process.opcua_secure` y la estación. No decir que `None` fue retirado.
- **`security: "SignAndEncrypt"` pero el `Write` no aparece como bloqueado:** cifrado y autorización son barreras diferentes; la política de variable no está demostrada.
- **`Read`/`readback` ausentes:** el resultado no permite afirmar que la lectura funcionó; distinguir error de transporte de rechazo de escritura.
- **`osqueryi` vacío:** significa “no observado” en ese instante y endpoint; no ausencia absoluta.
- **Kibana vacío o sin alerta Suricata:** la fuente visual no reemplaza el protocolo ni el estado local. Conservar la terminal y no inventar tiempos de ingestión.

## Evidencia entregable y solución razonada

La carpeta entregable es `~/lab/evidencias/taller-06/`. Debe contener, como mínimo, la respuesta inicial, el hardening, la respuesta segura, los snapshots de `classroom-state`, `labctl evidence`, y cualquier consulta osquery realmente ejecutada. Para cada evidencia registrar en el informe: comando, host, hora UTC capturada, resultado permitido/bloqueado, efecto sobre la consigna, fuente exacta y limitación. No usar capturas de pantalla inventadas ni sustituir un JSON por el resultado esperado.

La solución es la secuencia: comprobar identidad y línea base; ejecutar una única escritura inicial sobre el nodo fijo; aplicar exactamente la barrera OPC UA; repetir la misma operación; comprobar `security`, `outcome`, `before` y `readback`; contrastar el proceso y conservar los artefactos. La primera respuesta del protocolo y la segunda lectura de estado deben concordar. `lab.endpoint` y `lab.control` son logs de aplicación, no detecciones independientes de osquery o Suricata.

**Criterios finales:**

1. `Write` inicial real permitido con `security: "None"`.
2. Estado de proceso con la consigna inicializada por la primera acción.
3. `Read` posterior exitoso mediante `SignAndEncrypt`.
4. `Write` posterior rechazado y `readback` sin cambio.
5. Evidencia de terminal y segunda fuente de estado conservadas, sin hashes, PID, timestamps o resultados inventados.
6. Afirmación explícita de que `None` **no** fue retirado por este taller.

## Mapeo normativo y límites

**MITRE ATT&CK for ICS:** la primera escritura controlada representa **T0836 Modify Parameter**. La etiqueta describe la técnica pedagógica; no convierte la maqueta en un ataque real.

**IEC 62443:** el ejercicio ilustra requisitos fundacionales **FR2, FR3 y FR4** a nivel de diseño y controles de aula. El `SL-T` debe definirse mediante análisis de riesgo de cada zona; un `SL-A` requiere evaluación, arquitectura y evidencia mucho más amplias. Siete botones o esta guía no acreditan un nivel de seguridad.

**Ley 21.663:** se conserva como marco de discusión del material del laboratorio. Esta práctica no determina cumplimiento legal, no notifica a ANCI y no reemplaza inventario, gestión de cambios, respuesta a incidentes ni las obligaciones que correspondan a una organización.

**Qué sí controla la barrera:** una variable OPC UA concreta queda de solo lectura para este flujo; el cliente de la repetición solicita `SignAndEncrypt`; el resultado del `Write` se verifica con una respuesta real y un `readback`.

**Qué no demuestra:** no retira `None` del servidor, no prueba RBAC, MFA o identidad de usuarios; no endurece el sistema operativo; no configura el gateway Modbus/TLS; no es firewall, SELinux/AppArmor, GPO, EDR, SIS, antivirus global ni certificación IEC 62443. El guard de malware benigno, la validación PLC y otros controles pertenecen a otros talleres.

## Uso responsable y antipatrón contextual

Ejecutar solo en el aula aislada y autorizada. No conectar a PLC, HMI, RTU, gateway o tiendas reales. El laboratorio usa destinos fijos internos y un nodo didáctico; no acepta IP, puerto, payload ni objetivo libre. No hay malware operativo, explotación, escaneo, cifrado ni direcciones externas configurables. Un ejercicio de corta duración tampoco demuestra una APT.

Antipatrón para discutir —no una observación atribuida a una organización—: acceso compartido del proveedor sin ventana, copia de configuración sin hash y cambios del HMI sin validación del proceso. El lunes, en una instalación real: identificar al dueño del activo, documentar cambio y reversión, probar fuera de producción y acordar una ventana con operaciones. No bloquear remotamente una planta sin evaluar la seguridad física.

## Separación respecto de otros módulos

Este documento es únicamente el taller 06. No mezclarlo con el **desafío 09**, que debe separar sus hosts y sus siete controles, ni con el **módulo 10**, que debe cubrir individualmente sus seis prácticas. En particular, `harden opcua-rbac` y `harden opcua-channel` no son sustitutos de `harden opcua` aquí: el módulo 10 trata usuarios públicos/RBAC y la retirada de `None` del servidor; el usuario legítimo `engineer` y su escritura de `3 °C` se validan allí. Este taller solo deja constancia del canal que configura el cliente y de la autorización de solo lectura de su variable.

## Referencia operativa local

El tutorial local de observabilidad puede consultarse desde la guía si el facilitador lo solicita, pero no es necesario para resolver la secuencia ni habilita nuevos destinos. No ejecutar pruebas automáticas en paralelo con este taller. Antes de marcar éxito, revisar que las fuentes estén identificadas: respuesta del comando OPC UA para el protocolo; `classroom-state` para el gemelo; osquery para el endpoint; Kibana/Suricata solo como observabilidad adicional; PCAP solo cuando se haya descargado e inspeccionado realmente.
